"""A handler for managing multiple tables in the database."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

from bear_shelf.datastore.storage._common import Storage

from .table import Table

if TYPE_CHECKING:
    from bear_shelf.datastore.tables.data import TableData
    from bear_shelf.datastore.unified_data import UnifiedDataFormat
    from bear_shelf.datastore.wal.config import WALConfig


class TableHandler[T: Storage]:
    """A handler for managing multiple tables in the database."""

    __slots__: tuple = ("data", "enable_wal", "storage", "tables", "wal_config", "wal_dir")

    storage: T
    data: UnifiedDataFormat
    tables: dict[str, Table]
    enable_wal: bool
    wal_dir: str | None
    wal_config: WALConfig | None

    def __init__(
        self,
        storage: T,
        data: UnifiedDataFormat,
        enable_wal: bool = False,
        wal_dir: str | None = None,
        wal_config: Any | None = None,
    ) -> None:
        """Initialize the TableHandler with a storage backend.

        Args:
            storage: An instance of a Storage backend.
            data: The unified data format for all tables
            enable_wal: Enable Write-Ahead Logging for tables
            wal_dir: Directory for WAL files (defaults to storage file directory)
            wal_config: WAL configuration (uses buffered defaults if None)
        """
        self.storage = storage
        self.data = data
        self.tables = {}
        self.enable_wal = enable_wal
        self.wal_dir = wal_dir
        self.wal_config = wal_config

    def commit(self) -> None:
        """Commit the current state of all tables to storage."""
        self.storage.write(self.data)

    def update_data(self, data: UnifiedDataFormat) -> Self:
        """Update the internal data representation."""
        self.data = data
        return self

    def load(self) -> Self:
        """Load all tables from storage into the handler."""
        for name, table_data in self.data.tables.items():
            table: Table = self.make(name=name, table_data=table_data)
            self.tables[name] = table
        return self

    def new(
        self,
        name: str,
        table_data: TableData,
        enable_wal: bool | None = None,
        wal_file: str | None = None,
        commit: bool = True,
    ) -> Table:
        """Create a new empty table and add it to the handler.

        Args:
            name: Name of the new table.
            table_data: The table's data structure
            enable_wal: Enable WAL for this table (overrides handler default if set)
            wal_file: Custom WAL file path (auto-generated if None)
            commit: Whether to commit the updated data to storage immediately.

        Returns:
            The newly created Table instance.

        Raises:
            ValueError: If a table with the same name already exists.
        """
        if name in self.tables:
            raise ValueError(f"Table '{name}' already exists.")
        table: Table = self.make(name=name, table_data=table_data, enable_wal=enable_wal, wal_file=wal_file)
        self.tables[name] = table
        if commit:
            self.commit()
        return table

    def get(self, name: str) -> Table:
        """Get a table by name."""
        return self.tables[name]

    def has(self, name: str) -> bool:
        """Check if a table exists."""
        return name in self.tables

    def clear(self) -> None:
        """Clear all tables from the handler."""
        self.data.clear()
        self.tables.clear()

    def close(self, clear: bool = True, delete: bool = True) -> None:
        """Close all tables and their associated resources."""
        for table in self.tables.values():
            table.close(clear=clear, delete=delete)

    def _wal_path(self, wal_file: str | None = None) -> Path:
        """Get the WAL file path for a table.

        Args:
            name: Table name
            wal_file: Custom WAL file path (auto-generated if None)

        Returns:
            Path to the WAL file
        """
        if wal_file is not None:
            return Path(wal_file)
        if self.wal_dir:
            return Path(self.wal_dir)
        if hasattr(self.storage, "file") and self.storage.file:
            return Path(self.storage.file).parent
        return Path(".")

    def make(
        self,
        name: str,
        table_data: TableData,
        enable_wal: bool | None = None,
        wal_file: str | None = None,
    ) -> Table:
        """Map a TableData instance to a Table instance.

        Args:
            name: Table name
            table_data: The table's data structure
            enable_wal: Enable WAL for this table (overrides handler default if set)
            wal_file: Custom WAL file path (auto-generated if None)

        Returns:
            Configured Table instance
        """
        use_wal: bool = enable_wal if enable_wal is not None else self.enable_wal
        wal_path: str | Path | None = None
        if use_wal:
            wal_path = self._wal_path(wal_file=wal_file) / f"{name}.wal"

        return Table(
            name=name,
            table_data=table_data,
            commit_callback=self.commit,
            enable_wal=use_wal,
            wal_file_path=wal_path,
            wal_config=self.wal_config,
        )

    def drop_table(self, name: str, commit: bool = False) -> None:
        """Drop a table from the handler.

        Args:
            name: Name of the table to drop.
            commit: Whether to commit the updated data to storage immediately.
        """
        if name not in self.tables:
            raise KeyError(f"Table '{name}' does not exist.")
        self.data.delete_table(name)
        del self.tables[name]
        if commit:
            self.commit()

    def __delitem__(self, name: str) -> None:
        """Delete a table by name."""
        del self.tables[name]

    def __contains__(self, name: str) -> bool:
        """Check if a table exists in the handler."""
        return self.has(name)
