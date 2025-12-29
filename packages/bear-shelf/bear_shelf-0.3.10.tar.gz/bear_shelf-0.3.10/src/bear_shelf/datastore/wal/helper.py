"""Helper class for Write-Ahead Log (WAL) operations in the datastore."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

from lazy_bear import lazy

from bear_shelf.datastore.wal.record import Operation, WALRecord

if TYPE_CHECKING:
    from pathlib import Path

    from bear_shelf.datastore.record import Record
    from bear_shelf.datastore.tables.table import Table
    from bear_shelf.datastore.wal.config import WALConfig
    from bear_shelf.datastore.wal.write_ahead_log import WriteAheadLog
    from funcy_bear.query import QueryProtocol
    from funcy_bear.tools.autosort_list import AutoSort
    from funcy_bear.tools.counter_class import Counter
else:
    AutoSort = lazy("funcy_bear.tools.autosort_list", "AutoSort")
    Counter = lazy("funcy_bear.tools.counter_class", "Counter")
    QueryProtocol = lazy("funcy_bear.query", "QueryProtocol")
    WriteAheadLog = lazy("bear_shelf.datastore.wal.write_ahead_log", "WriteAheadLog")
    WALConfig = lazy("bear_shelf.datastore.wal.config", "WALConfig")


class WALHelper:
    """Helper class for Write-Ahead Log (WAL) operations in the datastore."""

    def __init__(
        self,
        file: str | Path,
        table_name: str,
        *,
        config: WALConfig | None = None,
        auto_start: bool = True,
    ) -> None:
        """Initialize the WALHelper with a WAL file and a TableHandler.

        Args:
            file: Path to the WAL file
            table_name: Name of the table this WAL is for
            auto_start: Whether to automatically start the WAL logging thread
            config: WAL configuration (uses buffered defaults if None)
        """
        self._table_name: str = table_name
        self._tx_counter: Counter = Counter(start=0)
        self._file: str | Path = file
        self._config: WALConfig | None = config
        self._wal: WriteAheadLog[WALRecord] | None = None
        if auto_start:
            self.wal.start()

    @property
    def wal(self) -> WriteAheadLog[WALRecord]:
        if self._wal is None:
            self._wal = WriteAheadLog(self._file, WALRecord, self._config)
        return self._wal

    def insert(self, record: Record) -> None:
        """Log an insert operation to the WAL.

        Args:
            record: The record being inserted.
        """
        txid: int = self._tx_counter.tick()
        self.wal.add_op(
            txid=txid,
            op=Operation.INSERT,
            data={"record": record.model_dump(exclude_none=True)},
        )
        self.wal.commit(txid)

    def update(
        self,
        primary_key_value: dict[str, Any],
        updated_fields: dict[str, Any],
    ) -> None:
        """Log an update operation to the WAL.

        Args:
            primary_key_value: Dictionary of primary key field(s) and their value(s).
            updated_fields: Dictionary of fields to update.
        """
        txid: int = self._tx_counter.tick()
        self.wal.add_op(
            txid=txid,
            op=Operation.UPDATE,
            data={
                "primary_key_value": primary_key_value,
                "updated_fields": updated_fields,
            },
        )
        self.wal.commit(txid)

    def delete(self, primary_key_value: dict[str, Any]) -> None:
        """Log a delete operation to the WAL.

        Args:
            primary_key_value: Dictionary of primary key field(s) and their value(s).
        """
        txid: int = self._tx_counter.tick()
        self.wal.add_op(
            txid=txid,
            op=Operation.DELETE,
            data={"primary_key_value": primary_key_value},
        )
        self.wal.commit(txid)

    def insert_batch(self, records: list[Record]) -> None:
        """Log a batch of insert operations.

        Note: Currently each record is logged as a separate transaction.
        This provides granular recovery - if one record fails, others still succeed.

        TODO: Consider adding 'atomic' parameter for true batch atomicity.
        When atomic=True, all records would share a single transaction ID,
        providing "all or nothing" semantics. Trade-off is less granular recovery
        but stricter consistency guarantees for related records.

        Args:
            records: List of Record instances to insert
        """
        for record in records:
            txid: int = self._tx_counter.tick()
            self.wal.add_op(
                txid=txid,
                op=Operation.INSERT,
                data={"record": record.model_dump(exclude_none=True)},
            )
            self.wal.commit(txid)

    def update_batch(
        self,
        updates: list[tuple[dict[str, Any], dict[str, Any]]],
    ) -> None:
        """Log a batch of update operations.

        Args:
            updates: List of tuples (primary_key_value, updated_fields)
        """
        for primary_key_value, updated_fields in updates:
            txid: int = self._tx_counter.tick()
            self.wal.add_op(
                txid=txid,
                op=Operation.UPDATE,
                data={
                    "primary_key_value": primary_key_value,
                    "updated_fields": updated_fields,
                },
            )
            self.wal.commit(txid)

    def delete_batch(self, primary_key_values: list[dict[str, Any]]) -> None:
        """Log a batch of delete operations.

        Args:
            primary_key_values: List of primary key dictionaries
        """
        for primary_key_value in primary_key_values:
            txid: int = self._tx_counter.tick()
            self.wal.add_op(
                txid=txid,
                op=Operation.DELETE,
                data={"primary_key_value": primary_key_value},
            )
            self.wal.commit(txid)

    def recover_from_wal(self, table: Table) -> Self:
        """Recover the table's state from the Write-Ahead Log (WAL).

        Replays all committed transactions from the WAL, then checkpoints
        to flush changes to disk and clear the WAL.

        This method reads all WAL records, filters for committed transactions,
        and replays them in chronological order. Operations are applied in
        the order they appear in the WAL to ensure consistency.

        Args:
            table: The Table instance to recover

        Returns:
            Self for method chaining
        """
        records: AutoSort[dict[str, Any]] = self.wal.read_all()
        if not records:
            return self

        committed_txids: set[int] = {r["txid"] for r in records if r["op"] == Operation.COMMIT}
        ops: list[dict[str, Any]] = [r for r in records if r["txid"] in committed_txids and r["op"] != Operation.COMMIT]

        for op in ops:
            op_type: Operation = op["op"]
            data: dict[str, Any] = op["data"]

            match op_type:
                case Operation.INSERT:
                    table.insert_all([data["record"]], flush=True)
                case Operation.UPDATE:
                    from funcy_bear.query import where_map  # noqa: PLC0415

                    pk_value: dict[str, Any] = data["primary_key_value"]
                    fields: dict[str, Any] = data["updated_fields"]
                    pk_field: str = next(iter(pk_value.keys()))
                    pk_val = pk_value[pk_field]
                    cond: QueryProtocol = where_map(pk_field) == pk_val
                    table.update(fields=fields, cond=cond, flush=True)
                case Operation.DELETE:
                    table.delete_all(pk_kwargs_list=[data["primary_key_value"]], flush=True)
        self.checkpoint(table)
        return self

    def checkpoint(self, table: Table) -> None:
        """Checkpoint the table: commit to disk and clear WAL.

        Args:
            table: The Table instance to checkpoint
        """
        print("Checkpointing WAL...")
        table.commit()
        self.wal.clear()

    def close(self, clear: bool = True, delete: bool = True) -> None:
        """Close the WAL helper and stop the logging thread."""
        self.wal.stop(clear=clear, delete=delete)

    def wait_for_idle(self, timeout: float = 5.0) -> bool:
        """Wait for all queued WAL operations to be processed.

        Useful for testing to ensure WAL operations are flushed to disk.

        Args:
            timeout: Maximum time to wait in seconds (default: 5.0)

        Returns:
            True if queue became empty within timeout, False otherwise
        """
        return self.wal.wait_for_idle(timeout=timeout)


class WALHelperDummy(WALHelper):
    """A dummy WAL helper for tables without WAL enabled."""

    def __init__(self, *_args, **_kwargs) -> None: ...
    def insert(self, **_kwargs) -> None: ...  # pyright: ignore[reportIncompatibleMethodOverride]
    def update(self, **_kwargs) -> None: ...  # pyright: ignore[reportIncompatibleMethodOverride]
    def delete(self, **_kwargs) -> None: ...  # pyright: ignore[reportIncompatibleMethodOverride]
    def insert_batch(self, **_kwargs) -> None: ...  # pyright: ignore[reportIncompatibleMethodOverride]
    def update_batch(self, **_kwargs) -> None: ...  # pyright: ignore[reportIncompatibleMethodOverride]
    def delete_batch(self, **_kwargs) -> None: ...  # pyright: ignore[reportIncompatibleMethodOverride]
    def recover_from_wal(self, *_args, **_kwargs) -> Self:
        return self  # pyright: ignore[reportIncompatibleMethodOverride]

    def checkpoint(self, *_args, **_kwargs) -> None: ...  # pyright: ignore[reportIncompatibleMethodOverride]
    def close(self, clear: bool = True, delete: bool = True) -> None: ...
    def wait_for_idle(self, timeout: float = 5.0) -> bool:  # noqa: ARG002
        return True


# ruff: noqa: D102, D107
