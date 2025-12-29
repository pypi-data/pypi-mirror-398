"""This module implements the BearBase database class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from lazy_bear import lazy

from .record import NullRecords, Record, Records
from .storage._common import Storage

if TYPE_CHECKING:
    import atexit
    from collections.abc import Iterator

    from frozen_cub.lru_cache import LRUCache

    from bear_shelf.datastore.storage._common import get_storage
    from bear_shelf.datastore.tables.handler import TableHandler
    from bear_shelf.datastore.unified_data import UnifiedDataFormat
    from bear_shelf.datastore.wal.config import WALConfig
    from funcy_bear.query import QueryProtocol
    from funcy_bear.query.query_mapping import where

    from .columns import Columns
    from .storage._common import StorageChoices
    from .tables.data import TableData
    from .tables.table import Table
else:
    LRUCache = lazy("frozen_cub.lru_cache", "LRUCache")
    QueryProtocol = lazy("funcy_bear.query", "QueryProtocol")
    where = lazy("funcy_bear.query.query_mapping", "where")
    TableHandler = lazy("bear_shelf.datastore.tables.handler", "TableHandler")
    atexit = lazy("atexit")
    UnifiedDataFormat = lazy("bear_shelf.datastore.unified_data", "UnifiedDataFormat")
    get_storage = lazy("bear_shelf.datastore.storage._common", "get_storage")

WAL_CONFIG_FIELDS: set[str] = {
    "flush_mode",
    "flush_interval",
    "flush_batch_size",
    "auto_checkpoint",
    "checkpoint_threshold",
}


def is_record(obj: Any) -> bool:
    return hasattr(obj, "_is_record_instance") and obj._is_record_instance is True


class BearBase[T: Any]:
    """The main database class for Bear's datastore system."""

    ##########################################################################
    # Configuration defaults - override in subclasses or instances as needed #
    ##########################################################################
    default_table_name: str = "default"
    default_choice: StorageChoices = "jsonl"
    cache_capacity = 10
    wal_enabled_by_default: bool = False
    ##########################################################################

    def __init__(
        self,
        *args,
        current_table: str | None = None,
        enable_wal: bool | None = None,
        wal_dir: str | None = None,
        wal_config: WALConfig | None = None,
        **kwargs,
    ) -> None:
        """Create a new BearBase instance.

        Args:
            *args: Passed to storage backend (typically file path)
            storage: StorageChoices backend type (default: "jsonl")
            current_table: Default table name
            enable_wal: Enable Write-Ahead Logging for all tables (default: False)
            wal_dir: Directory for WAL files (default: same as database file)
            wal_config: WALConfig instance (optional, can build from kwargs)
            **kwargs: WAL config kwargs (flush_mode, flush_interval, etc.) or storage kwargs

        Special handling:
            - If first positional arg is ":memory:", automatically uses memory storage
            - WAL config can be passed as wal_config param OR individual kwargs
            - WALConfig is always created (even if enable_wal=False) for consistency

        Examples:
            BearBase("data.json", enable_wal=True)
            BearBase("data.json", wal_config=WALConfig.high_throughput())
            BearBase("data.json", enable_wal=True, flush_mode="buffered", flush_interval=0.5)
        """
        atexit.register(self.close)
        storage: StorageChoices = kwargs.pop("storage", self.default_choice)
        if (args and args[0] == ":memory:") or storage == "memory":
            storage = "memory"
            args = args[1:]

        ##################################
        ### WAL Configuration Handling ###
        ###################################
        self.enable_wal: bool = enable_wal if enable_wal is not None else self.wal_enabled_by_default
        self.wal_kwargs: dict[str, Any] = {k: kwargs.pop(k) for k in list(kwargs) if k in WAL_CONFIG_FIELDS}
        self._wal_config: WALConfig | None = (
            wal_config.model_validate(self.wal_kwargs) if (wal_config and self.wal_kwargs) else wal_config
        )
        self._wal_dir: str | None = wal_dir

        self._current_table: str | None = current_table
        self._storage: T = get_storage(storage)(*args, **kwargs)  # pyright: ignore[reportAttributeAccessIssue]
        self._data: UnifiedDataFormat | None = self.storage.read()

        self.handler: TableHandler[T] = TableHandler(
            storage=self._storage,
            data=self.data,
            enable_wal=self.enable_wal,
            wal_dir=self._wal_dir,
            wal_config=self.wal_config,
        ).load()

        self._query_cache: LRUCache | None = None

    @property
    def data(self) -> UnifiedDataFormat:
        """Get the current unified data format, loading from storage if necessary."""
        if self._data is None:
            self._data = UnifiedDataFormat()
            self.storage.write(self._data)  # FIXME: We shouldn't be writing directly?
        return self._data

    @property
    def wal_config(self) -> WALConfig:
        """Get the WALConfig instance for this BearBase."""
        if self._wal_config is None:
            from bear_shelf.datastore.wal.config import WALConfig  # noqa: PLC0415

            self._wal_config = WALConfig(**self.wal_kwargs)
        return self._wal_config if self.enable_wal else None  # pyright: ignore[reportReturnType]

    @property
    def storage(self) -> T:
        """Get the storage instance used for this BearBase instance."""
        return self._storage

    @property
    def opened(self) -> bool:
        """Check if the storage is open."""
        return not self.storage.closed

    @property
    def current_table(self) -> str:
        """Get the current table name, defaulting to default_table_name if not set."""
        return self._current_table or self.default_table_name

    def set_table(self, name: str) -> None:
        """Set the current table for operations.

        Args:
            name: The name of the table to set as current.
        """
        if name not in self.tables():
            raise KeyError(f"Table '{name}' does not exist.")
        self._current_table = name

    def create_table(
        self,
        name: str,
        columns: list[Columns] | None = None,
        save: bool = False,
        enable_wal: bool | None = None,
        wal_file: str | None = None,
        strict: bool = False,
    ) -> Table:
        """Create a new table with explicit schema.

        Args:
            name: Name of the table
            columns: List of Columns instances or ColumnsProtocol type
            save: Whether to immediately save the new table to storage
            enable_wal: Enable WAL for this table (overrides BearBase default if set)
            wal_file: Custom WAL file path (auto-generated if None)
            strict: If True, raises an error if the table already exists.

        Returns:
            The created Table instance
        """
        if columns is None:
            raise ValueError("Columns must be provided to create a new table.")
        table_data: TableData = self.data.new_table(name, columns=columns, strict=strict)
        table: Table = self.table(name, table_data=table_data, enable_wal=enable_wal, wal_file=wal_file)
        self.set_table(name)
        if save:
            self.handler.commit()
        return table

    def table(
        self,
        name: str,
        table_data: TableData | None = None,
        enable_wal: bool | None = None,
        wal_file: str | None = None,
    ) -> Table:
        """Get a table by name.

        Args:
            name: The name of the table to get.
            table_data: Optional TableData if creating a new table
            enable_wal: Enable WAL for this table (overrides BearBase default if set)
            wal_file: Custom WAL file path (auto-generated if None)

        Returns:
            The table instance.

        Raises:
            KeyError: If table doesn't exist and no table_data provided
        """
        if self.handler.has(name):
            return self.handler.get(name)

        if table_data is None:
            raise ValueError(f"Table '{name}' does not exist. Use create_table() to create it first.")
        enable_wal = self.enable_wal if enable_wal is None else enable_wal
        return self.handler.new(name, table_data=table_data, enable_wal=enable_wal, wal_file=wal_file)

    def tables(self) -> set[str]:
        """Get a set of all table names in the database.

        Returns:
            A set of table names.
        """
        if self.data.empty:
            return set()
        return set(self.data.names())

    def get_tables(self) -> dict[str, Table]:
        """Get a dictionary of all table names to Table instances in the database.

        Returns:
            A dictionary mapping table names to Table instances.
        """
        tables: set[str] = self.tables()
        return {table_name: self.table(table_name) for table_name in tables}

    def drop_table(self, name: str) -> None:
        """Drop a specific table from the database. **CANNOT BE REVERSED!**

        Args:
            name: The name of the table to drop.
        """
        if name not in self.data.tables:
            raise KeyError(f"Table '{name}' does not exist.")
        self.handler.drop_table(name, commit=True)

    def drop_tables(self) -> None:
        """Drop all tables from the database. **CANNOT BE REVERSED!**"""
        self.storage.clear()
        self.handler.clear()
        self.handler.commit()

    def insert(self, record: Any | None = None, **kwargs) -> None:
        """Insert a record into a specified or default table.

        Args:
            record: The record to insert
            **kwargs: Record fields as keyword arguments
        """
        if record is None and not kwargs:
            return
        if record is not None and not isinstance(record, dict):
            raise TypeError("Record must be a dictionary.")
        if record is None:
            record = kwargs
        self.table(self.current_table).insert(record)

    def insert_multiple(self, records: list[Any]) -> None:
        """Insert multiple records into the default table.

        Args:
            records: A list of records to insert.
        """
        self.table(self.current_table).insert_all(records)

    def all(self) -> list[Record]:
        """Get all records from the default table.

        Returns:
            A list of all records in the default table.
        """
        return self.table(self.current_table).all()

    def search(self, query: QueryProtocol) -> Records:
        """Search for records in the default table matching a query.

        Args:
            query: The query to search for.

        Returns:
            A list of records matching the query.
        """
        return self.table(self.current_table).search(query)

    def get(
        self,
        cond: QueryProtocol | None = None,
        default: Record | None = None,
        **pk_kwargs,
    ) -> Records:
        """Get a single record from the default table matching a condition.

        Args:
            cond: The condition to match.
            default: The default value to return if no record is found.
            **pk_kwargs: Primary key fields as keyword arguments

        Returns:
            The matching record or the default value.
        """
        return self.table(self.current_table).get(cond, default, **pk_kwargs)

    def contains(self, query: QueryProtocol) -> bool:
        """Check if any record in the default table matches a query.

        Args:
            query: The query to check.

        Returns:
            True if any record matches the query, False otherwise.
        """
        return self.table(self.current_table).contains(query)

    # TODO: Need to work on this concept a bit more
    # We _DO_ support foreign keys generally speaking but this
    # API is a bit weak right now.
    def get_related(
        self,
        parent_table: str | Table,
        parent_key: Any,
        child_table: str | Table,
        fk_column: str,
    ) -> Records:
        """Get records from child_table that reference parent_id via fk_column.

        This uses foreign key metadata to traverse relationships between tables.

        Args:
            parent_table: Name of the parent table or Table instance
            parent_key: Primary key value in the parent table
            child_table: Name of the child table containing the foreign key
            fk_column: Name of the foreign key column in the child table

        Returns:
            Records from child_table where fk_column equals parent_id

        Examples:
            # Get all posts by user 293
            db.get_related("users", 293, "posts", "user_id")

            # Get all comments on post 42
            db.get_related("posts", 42, "comments", "post_id")
        """
        if isinstance(parent_table, str):
            parent_table = self.table(parent_table)

        matches: Records = parent_table.get(**{parent_table.primary_key: parent_key})
        if not matches:
            return NullRecords

        if isinstance(child_table, str):
            child_table = self.table(child_table)

        if fk_column not in child_table.columns():
            raise KeyError(f"Foreign key column '{fk_column}' not found in table '{child_table.name}'.")

        return child_table.search(where(key=fk_column) == parent_key)

    def update(
        self,
        fields: dict | None = None,
        cond: QueryProtocol | None = None,
        **kwargs,
    ) -> int:
        """Update records in the default table matching a condition.

        Args:
            fields: Dictionary of fields to update
            cond: The condition to match for records to update
            **kwargs: Field updates as keyword arguments

        Returns:
            Number of records updated
        """
        updated: int = self.table(self.current_table).update(fields=fields, cond=cond, **kwargs)
        return updated

    def upsert(
        self,
        record: dict | Record | None = None,
        cond: QueryProtocol | None = None,
        **kwargs,
    ) -> None:
        """Update existing record or insert new one in the default table.

        Args:
            record: Record data to upsert
            cond: Query condition to find existing record
            **kwargs: Field values as keyword arguments
        """
        if record is None and not kwargs:
            return
        if record is not None and not isinstance(record, dict) and not is_record(record):
            raise TypeError("Record must be a dictionary or Record instance.")
        self.table(self.current_table).upsert(record=record, cond=cond, **kwargs)

    def close(self, clear: bool = True, delete: bool = True) -> None:
        """Close the storage instance."""
        self.storage.close()
        if self.enable_wal:
            self.handler.close(clear=clear, delete=delete)

    def commit(self) -> None:
        """Commit any pending changes to the storage."""
        self.handler.commit()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args) -> None:
        """Close the storage instance when leaving a context."""
        if self.opened:
            self.close()

    def __bool__(self) -> bool:
        """Return True if the default table has any documents."""
        if self._data is None or self.data.empty:
            return False
        return bool(self.table(self.current_table))

    def __len__(self) -> int:
        """Return the number of documents in the default table."""
        if self._data is None or self.data.empty:
            return 0
        return len(self.table(self.current_table))

    def __iter__(self) -> Iterator[Record]:
        """Return an iterator for the default table's documents."""
        if self._data is None or self.data.empty:
            return iter([])
        return iter(self.table(self.current_table))

    def __repr__(self) -> str:
        cls_name: str = self.__class__.__name__
        srg_name: str = self.storage.__class__.__name__
        tables: list[str] = list(self.tables())
        return f"{cls_name}(storage={srg_name}, tables={tables})"


class JSONBase(BearBase[Storage]):
    """A BearBase database using JSONL storage by default."""

    default_choice: StorageChoices = "json"


class JSONLBase(BearBase[Storage]):
    """A BearBase database using JSONL storage by default."""

    default_choice: StorageChoices = "jsonl"


class MemoryBase(BearBase[Storage]):
    """A BearBase database using in-memory storage by default."""

    default_choice: StorageChoices = "memory"


class TOMLBase(BearBase[Storage]):
    """A BearBase database using TOML storage by default."""

    default_choice: StorageChoices = "toml"


class YAMLBase(BearBase[Storage]):
    """A BearBase database using YAML storage by default."""

    default_choice: StorageChoices = "yaml"


class MSGPackBase(BearBase[Storage]):
    """A BearBase database using MessagePack storage by default."""

    default_choice: StorageChoices = "msgpack"


class NixBase(BearBase[Storage]):
    """A BearBase database using Nix storage by default."""

    default_choice: StorageChoices = "nix"


class ToonBase(BearBase[Storage]):
    """A BearBase database using Toon storage by default."""

    default_choice: StorageChoices = "toon"


class XMLBase(BearBase[Storage]):
    """A BearBase database using XML storage by default."""

    default_choice: StorageChoices = "xml"


__all__ = [
    "BearBase",
    "JSONBase",
    "JSONLBase",
    "MSGPackBase",
    "MemoryBase",
    "NixBase",
    "TOMLBase",
    "ToonBase",
    "XMLBase",
    "YAMLBase",
]
