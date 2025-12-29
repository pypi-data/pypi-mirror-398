"""A holder for tables in the unified data format."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from pydantic import Field, RootModel

from .data import TableData

if TYPE_CHECKING:
    from collections.abc import Iterator


class TablesHolder(RootModel[dict[str, TableData]]):
    """A holder for tables in the unified data format."""

    root: dict[str, TableData] = Field(default_factory=dict)

    def get_all(self) -> dict[str, TableData]:
        """Get all tables as a dictionary."""
        return self.root

    def set(self, name: str, table: TableData) -> None:
        """Set or update a table."""
        self.root[name] = table

    def get(self, name: str) -> TableData | None:
        """Get a table by name, or None if it doesn't exist."""
        return self.root.get(name)

    def add(self, name: str, table: TableData) -> None:
        """Add a new table."""
        self.set(name, table)

    def remove(self, name: str) -> None:
        """Remove a table by name."""
        del self.root[name]

    def clear(self) -> None:
        """Clear all tables."""
        self.root.clear()

    @property
    def empty(self) -> bool:
        """Check if there are no tables."""
        return not self.root

    def iterate(self) -> Iterator[str]:
        """Iterate over table names."""
        return iter(self.root)

    def keys(self) -> list[str]:
        """Get a list of table names."""
        return cast("list", self.root.keys())

    def values(self) -> list[TableData]:
        """Get a list of TableData instances."""
        return cast("list", self.root.values())

    def items(self) -> list[tuple[str, TableData]]:
        """Get a list of (table name, TableData) tuples."""
        return list(self.root.items())

    def __getattr__(self, name: str) -> TableData:
        if name == "root" or (name.startswith("__") and name.endswith("__")):
            return super().__getattribute__(name)
        return self.root[name]

    def __setattr__(self, name: str, value: TableData) -> None:
        if name == "root":
            super().__setattr__(name, value)
        else:
            self.root[name] = value

    def __delattr__(self, name: str) -> None:
        if name == "root":
            super().__delattr__(name)
        else:
            del self.root[name]

    def __getitem__(self, name: str) -> TableData:
        return self.root[name]

    def __setitem__(self, name: str, value: TableData) -> None:
        self.root[name] = value

    def __delitem__(self, name: str) -> None:
        del self.root[name]

    def __contains__(self, name: str) -> bool:
        return name in self.root

    def __len__(self) -> int:
        return len(self.root)

    def __hash__(self) -> int:
        """Get the hash of the tables holder based on its tables."""
        return hash(tuple(sorted([hash(table) for table in self.root.values()])))

    def __repr__(self) -> str:
        return f"TablesHolder(root={self.root})"
