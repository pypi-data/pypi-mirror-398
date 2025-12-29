"""A WAL( Write-Ahead Log) data structure implementation."""

from __future__ import annotations

from pathlib import Path
import time
from typing import TYPE_CHECKING, Any, Protocol, Self

from lazy_bear import lazy

from .config import WALConfig, WALFlushMode
from .record import Operation, WALRecord

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from queue import Empty, Queue
    from threading import Event, RLock, Thread

    from codec_cub.jsonl.file_handler import JSONLFileHandler
    from codec_cub.text.file_handler import TextFileHandler
    from funcy_bear.sentinels import EXIT_SIGNAL
    from funcy_bear.tools.autosort_list import AutoSort
else:
    EXIT_SIGNAL = lazy("funcy_bear.sentinels", "EXIT_SIGNAL")
    AutoSort = lazy("funcy_bear.tools.autosort_list", "AutoSort")
    JSONLFileHandler = lazy("codec_cub.jsonl.file_handler", "JSONLFileHandler")
    TextFileHandler = lazy("codec_cub.text.file_handler", "TextFileHandler")
    Event, RLock, Thread = lazy("threading", "Event", "RLock", "Thread")
    Empty, Queue = lazy("queue", "Empty", "Queue")


class RecordProtocol(Protocol):
    """Protocol for WAL record types."""

    txid: int
    op: Operation
    data: dict[Any, Any] | None
    timestamp: Any

    def model_dump_json(self, *args, **kwargs: Any) -> str: ...  # noqa: D102


class WriteAheadLog[T: RecordProtocol]:
    """A simple Write-Ahead Log (WAL) implementation with configurable flush strategies."""

    _record_type: type[T] = WALRecord  # pyright: ignore[reportAssignmentType]
    """The record type stored in the WAL."""

    _config_type: type[WALConfig] = WALConfig
    """The WALConfig type used for configuration."""

    def __init__(
        self,
        file: str | Path,
        record_t: type[T] | None = None,
        config: WALConfig | None = None,
        **kwargs,
    ) -> None:
        """Initialize the Write-Ahead Log.

        Args:
            file: Path to WAL file
            record_t: Record class factory
            config: WALConfig instance (uses buffered defaults if None)
            **kwargs: Additional WALConfig parameters to override defaults
        """
        self._record_type = record_t or WALRecord  # pyright: ignore[reportAttributeAccessIssue]
        self._log_queue: Queue[T] = Queue[self._record_type]()

        config = config or self._config_type.buffered()
        self.config: WALConfig = config.model_copy(update=kwargs)
        self._file: str | Path = file
        self._writer: TextFileHandler | None = None
        self._reader: JSONLFileHandler[dict] | None = None

        self._buffer_lock = RLock()
        self._thread: Thread | None = None
        self._flush_thread: Thread | None = None
        self._stop_event: Event = Event()

        self._op_count: int = 0
        self._buffer_size: int = 0
        self._buffer: list[str] = []
        self._on_error: Callable[[Exception], Any] | None = self.config.on_error if self.config.on_flush_error else None

    @property
    def reader(self) -> JSONLFileHandler[dict]:
        """Get the JSONL file reader."""
        if self._reader is None:
            self._reader = JSONLFileHandler(self._file)
        return self._reader

    @property
    def writer(self) -> TextFileHandler:
        """Get the text file writer."""
        if self._writer is None:
            self._writer = TextFileHandler(self._file, touch=True)
        return self._writer

    @property
    def running(self) -> bool:
        """Check if the WAL is currently running."""
        return self._thread is not None and self._thread.is_alive()

    def _record_factory(self, **kwargs: Any) -> T:
        """Create a new record of type T."""
        return self._record_type(**kwargs)

    def commit(self, txid: int) -> bool:
        """Log a COMMIT operation to the WAL.

        Args:
            txid: The transaction ID to commit

        Returns:
            True if the commit operation was successfully logged
        """
        try:
            self._log_queue.put(self._record_factory(txid=txid, op=Operation.COMMIT, data={}))
            return True
        except Exception as e:
            if self._on_error is not None:
                self._on_error(e)
            return False

    def add_op(self, txid: int, op: Operation | str, data: dict[str, Any]) -> bool:
        """Log an operation to the WAL.

        Args:
            txid: The transaction ID
            op: The operation to log (Operation enum or string)
            data: The data associated with the operation

        Returns:
            True if the operation was successfully logged
        """
        try:
            if isinstance(op, str):
                op = Operation(op)
            record: T = self._record_factory(txid=txid, op=op, data=data)
            self._log_queue.put(record)
            return True
        except ValueError as e:
            if self._on_error is not None:
                self._on_error(e)
                return False
            raise ValueError(f"Invalid operation '{op}': {e}") from e

    def _write(self, record: T) -> None:
        """Write a single WAL record to the file.

        Behavior depends on flush_mode:
        - IMMEDIATE: fsync after every write (slow, maximum safety)
        - BUFFERED: batch in memory, flush periodically (fast, small crash window)

        Args:
            record: The WAL record to write
        """
        with self._buffer_lock:
            try:
                serialized: str = record.model_dump_json(exclude_none=True)
                if self.config.flush_mode == WALFlushMode.IMMEDIATE:
                    return self.writer.append(serialized, force=True)
                if self.config.flush_mode == WALFlushMode.BUFFERED:
                    self._buffer.append(serialized)
                    self._op_count += 1
                    self._buffer_size += len(serialized)

                    if (
                        self._op_count >= self.config.flush_batch_size
                        or self._buffer_size >= self.config.max_buffer_bytes
                    ):
                        self._flush_buffer()

            except Exception as e:
                if self._on_error is not None:
                    self._on_error(e)
                else:
                    raise OSError(f"Failed to write WAL record {record}: {e}") from e

    def read_all(self, sort_key: Callable[[dict], Any] | None = None) -> AutoSort[dict]:
        """Read all WAL records from the file.

        Basically this would be used during recovery to replay the log.

        Args:
            sort_key: Optional callable to sort records (default: by timestamp, txid)

        Returns:
            A list of records as dictionaries, sorted if sort_key provided
        """

        def _default_key(r: dict) -> tuple[int, ...]:
            """Default sort key: (timestamp, txid)."""
            return r.get("timestamp", 0), r.get("txid", 0)

        records: AutoSort[dict] = AutoSort(key=sort_key or _default_key)
        try:
            records.extend(self.reader.readlines())
            return records
        except Exception as e:
            if self._on_error is not None:
                self._on_error(e)
                return records
            raise OSError(f"Failed to read WAL records: {e}") from e

    def _loop(self) -> None:
        """Write log records to the file."""
        q: Queue = self._log_queue
        has_task_done: bool = hasattr(q, "task_done")
        while True:
            try:
                record: T = q.get(timeout=self.config.get_timeout)
                if record is EXIT_SIGNAL:
                    self._flush_buffer()
                    if has_task_done:
                        q.task_done()
                    break
                self._write(record)
                if has_task_done:
                    q.task_done()
            except Empty:
                continue

    def _flush_buffer(self) -> None:
        """Flush buffered WAL records to disk."""
        if not self._buffer:
            return
        with self._buffer_lock:
            try:
                for line in self._buffer:
                    self.writer.append(line, force=False)
                self.writer.flush()  # Single fsync for entire batch
                self._buffer.clear()
                self._op_count = 0
                self._buffer_size = 0
            except Exception as e:
                if self._on_error is not None:
                    self._on_error(e)
                else:
                    raise OSError(f"Failed to flush WAL buffer: {e}") from e

    def _flush_loop(self) -> None:
        """Periodically flush WAL buffer in BUFFERED mode."""
        if self.config.flush_mode != WALFlushMode.BUFFERED:
            return

        while not self._stop_event.is_set():
            if self._stop_event.wait(timeout=self.config.flush_interval):
                break  # Stop event set, exit

            if self._buffer:
                self._flush_buffer()

    def start(self) -> None:
        """Start the WAL logging threads."""
        if self.running:
            raise RuntimeError("WAL listener already started")

        self._stop_event.clear()
        self._thread = t = Thread(target=self._loop)
        t.daemon = True
        t.start()

        if self.config.flush_mode == WALFlushMode.BUFFERED:
            self._flush_thread = ft = Thread(target=self._flush_loop)
            ft.daemon = True
            ft.start()

    def stop(self, clear: bool = True, delete: bool = True) -> None:
        """Stop the WAL threads and flush remaining buffer.

        Args:
            clear: If True, clear the WAL file after stopping (default: True)
            delete: If True, delete the WAL file after stopping (default: True)
        """
        if not self.running:
            return
        self._stop_event.set()

        if self._flush_thread is not None:
            self._flush_thread.join(timeout=self.config.timeout)
            self._flush_thread = None

        if self._thread is not None:
            self.enqueue_sentinel()
            self._thread.join(timeout=self.config.timeout)
            self._thread = None

        if self._writer is not None and not self._writer.closed:
            if clear:
                self._writer.clear()
            if delete:
                self._writer.delete()
            self._writer.close()
            self._writer = None

        if self._reader is not None and not self._reader.closed:
            self._reader.close()
            self._reader = None

    def clear(self) -> None:
        """Clear the WAL file.

        This should happen after it is ensured that all logged operations have been
        safely applied to the main data store.
        """
        self.writer.clear()

    def enqueue_sentinel(self) -> None:
        """Enqueue a sentinel object to stop thread."""
        self._log_queue.put(EXIT_SIGNAL)  # pyright: ignore[reportArgumentType]

    def wait_for_idle(self, timeout: float = 5.0, flush_buffer: bool = True) -> bool:
        """Wait for all queued operations to be processed.

        Useful for testing to ensure WAL operations are flushed to disk
        before checking file contents.

        Args:
            timeout: Maximum time to wait in seconds (default: 5.0)
            flush_buffer: If True, also flush buffer in BUFFERED mode (default: True)

        Returns:
            True if queue became empty within timeout, False otherwise
        """
        deadline: float = time.monotonic() + timeout
        queue_ref: Queue[T] = self._log_queue

        with queue_ref.all_tasks_done:  # wait for workers to drain queued work
            while queue_ref.unfinished_tasks:
                remaining: float = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                queue_ref.all_tasks_done.wait(timeout=remaining)

        if flush_buffer and self.config.flush_mode == WALFlushMode.BUFFERED:
            self._flush_buffer()  # In BUFFERED mode, also flush any pending buffer
        return True

    def __enter__(self) -> Self:
        """Enter the context manager."""
        self.start()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit the context manager."""
        self.stop()
