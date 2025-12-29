"""A core data model for the unified data format used by all storage backends."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from lazy_bear import lazy
from pydantic import Field, model_validator

from bear_shelf.datastore.columns import NOTSET_TUPLE
from bear_shelf.datastore.header_data import HeaderData
from bear_shelf.datastore.tables.holder import TablesHolder
from bear_shelf.models import ExtraIgnoreModel

if TYPE_CHECKING:
    from bear_shelf.datastore.columns import Columns, ForeignKey
    from bear_shelf.datastore.tables.data import TableData
else:
    TableData = lazy("bear_shelf.datastore.tables.data", "TableData")


class UnifiedDataFormat(ExtraIgnoreModel):
    """The unified in-memory data structure for all storage backends.

    This structure is used internally by all storage backends (JSONL, JSON, TOML, XML).
    Each format handles serialization/deserialization to/from this structure.

    Example structure:
        {
            "header": {
                "version": UNIFIED_DATA_VERSION
                "schema_version": "0.0.1",
                "tables": ["users", "posts"],
            },
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "int", ...}],
                    "count": 2,
                    "records": [{"id": 1, "name": "Bear"}, ...]
                }
            }
        }
    """

    header: HeaderData = Field(default_factory=HeaderData)
    tables: TablesHolder = TablesHolder()

    def model_post_init(self, context: Any) -> None:
        """Post-initialization to ensure header and tables are in sync."""
        for table_name in self.tables.iterate():
            if table_name not in self.header.tables:
                self.header.add(table_name)
        return super().model_post_init(context)

    def new_table(
        self,
        name: str,
        columns: list[Columns] | None = None,
        table_data: TableData | None = None,
        strict: bool = False,
    ) -> TableData:
        """Create a new empty table and add it to the unified data format.

        Args:
            name: Name of the new table.
            columns: Optional list of Columns instances.
            table_data: Optional TableData instance to use.
            strict: If True, raises an error if the table already exists.

        Returns:
            The newly created TableData instance.
        """
        if name in self.tables:
            if strict:
                raise ValueError(f"Table '{name}' already exists.")
            return self.tables[name]
        if table_data is None:
            if columns is None or not columns:
                raise ValueError("Columns must be provided if table_data is not.")
            table: TableData = TableData.new(name=name, columns=columns)
        else:
            table = table_data
            table.name = name
        self.tables.add(name, table)
        self.header.add(table.name)
        return table

    def table(self, name: str) -> TableData:
        """Get a table by name.

        Args:
            name: Name of the table to get.

        Returns:
            The TableData instance.

        Raises:
            KeyError: If the table does not exist.
        """
        if name not in self.tables:
            raise KeyError(f"Table '{name}' does not exist.")
        return self.tables[name]

    def names(self) -> list[str]:
        """Get a list of table names in the unified data format."""
        return list(self.tables.keys())

    def has(self, name: str) -> bool:
        """Alias for __contains__ to check if a table exists."""
        return self.__contains__(name)

    def get_table(self, name: str) -> TableData | None:
        """Retrieve a table by name.

        Args:
            name: Name of the table to retrieve.

        Returns:
            TableData instance if found, else None.
        """
        return self.tables.get(name)

    def delete_table(self, name: str) -> None:
        """Delete a table by name.

        Args:
            name: Name of the table to delete.
        """
        self.tables.remove(name)
        self.header.remove(name)

    def clear(self) -> None:
        """Clear all tables and reset the header."""
        self.tables.clear()
        self.header.tables.clear()

    def render(self) -> dict[str, Any]:
        """Render the unified data format as a dictionary."""
        return self.model_dump(exclude_none=True)

    @property
    def empty(self) -> bool:
        """Check if the unified data format is empty (no tables)."""
        return self.tables.empty

    @classmethod
    def _validate_foreign_keys(cls, tables: TablesHolder) -> None:
        """Validate foreign key constraints in the tables."""
        tables_with_fks: dict[str, TableData] = {
            table_name: table_data
            for table_name, table_data in tables.items()
            if any(col.foreign_key is not None for col in table_data.columns)
        }
        for table_name, table_data in tables_with_fks.items():
            cols_with_fks: list[Columns] = [col for col in table_data.columns if col.foreign_key is not None]
            for col in cols_with_fks:
                fk: ForeignKey = col.split_foreign_key
                if fk is NOTSET_TUPLE:
                    continue
                if fk.table not in tables:
                    msg: str = f"Foreign key references non-existent table '{fk.table}' in column '{col.name}' of table '{table_name}'."
                    raise ValueError(msg)
                if fk.column not in {c.name for c in tables[fk.table].columns}:
                    msg = f"Foreign key references non-existent column '{fk.column}' in table '{fk.table}' for column '{col.name}' of table '{table_name}'."
                    raise ValueError(msg)

    @model_validator(mode="before")
    @classmethod
    def validate_tables(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Ensure tables is a TablesHolder instance and inject table names."""
        tables: dict = values.get("tables", {})
        if not isinstance(tables, TablesHolder):
            tables_with_names: dict[str, Any] = {}
            for table_name, table_data in tables.items():
                if isinstance(table_data, dict) and "name" not in table_data:
                    table_data["name"] = table_name
                tables_with_names[table_name] = table_data
            values["tables"] = TablesHolder(root=tables_with_names)
        cls._validate_foreign_keys(values["tables"])
        return values

    @classmethod
    def _load_tables(cls, tables: Any) -> Self:
        """Set the tables attribute, used for testing purposes."""
        if isinstance(tables, dict):
            return cls(tables=TablesHolder(root=tables))
        return cls(tables=tables)

    @property
    def tuple_output(self) -> tuple[str, str, dict[str, TableData]]:
        """Get a dictionary representation of the header information."""
        return (self.header.version, self.header.schema_version, self.tables.get_all())

    def __contains__(self, name: str) -> bool:
        """Check if a table exists in the unified data format.

        Args:
            name: Name of the table to check.

        Returns:
            True if the table exists, else False.
        """
        return name in self.tables

    def __eq__(self, other: object) -> bool:
        """Check equality between two UnifiedDataFormat instances."""
        if not isinstance(other, UnifiedDataFormat):
            return NotImplemented
        return self.header == other.header and self.tables == other.tables

    def __ne__(self, other: object) -> bool:
        """Check inequality between two UnifiedDataFormat instances."""
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Hash the unified data format based on its header and tables."""
        return hash(f"UnifiedDataFormat-{hash(self.header)}-{hash(self.tables)}")

    def __repr__(self) -> str:
        return f"UnifiedDataFormat(header={self.header}, tables={self.tables})"
