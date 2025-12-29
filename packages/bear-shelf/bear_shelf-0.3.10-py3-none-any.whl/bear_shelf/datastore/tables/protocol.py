"""Protocol for table-like storage interfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, Self, runtime_checkable

from lazy_bear import lazy

if TYPE_CHECKING:
    from bear_shelf.datastore.columns import Columns
    from funcy_bear.query import QueryProtocol
else:
    QueryProtocol = lazy("funcy_bear.query", "QueryProtocol")


@runtime_checkable
class TableProtocol[Doc, Docs](Protocol):
    """Protocol for table-like storage interfaces.

    This defines the interface that storage backends should implement
    for Bear's datastore system.
    """

    def get(
        self,
        cond: QueryProtocol | None = None,
        default: Doc | None = None,
        **pk_kwargs,
    ) -> Docs:
        """Get a value by key."""
        raise NotImplementedError("To be overridden!")

    def set(self, key: str, value: Any) -> None:
        """Set a key-value pair."""
        raise NotImplementedError("To be overridden!")

    def search(self, query: QueryProtocol) -> Docs:
        """Search for records matching a query."""
        raise NotImplementedError("To be overridden!")

    def all(self, **kwargs) -> Docs | list[Doc]:
        """Get all records."""
        raise NotImplementedError("To be overridden!")

    def upsert(self, record: Any, cond: QueryProtocol, **kwargs) -> None:
        """Update existing record or insert new one."""
        raise NotImplementedError("To be overridden!")

    def contains(self, query: QueryProtocol) -> bool:
        """Check if any record matches the query."""
        raise NotImplementedError("To be overridden!")

    def clear(self) -> None:
        """Clear all records in the table."""
        raise NotImplementedError("To be overridden!")

    def close(self) -> None:
        """Close the table/storage."""
        raise NotImplementedError("To be overridden!")

    def __call__(self, *args: Any, **kwargs: Any) -> Self:
        """Make the table callable."""
        raise NotImplementedError("To be overridden!")


@runtime_checkable
class ColumnsProtocol(Protocol):
    def get_columns(self) -> list[Columns]: ...


__all__ = ["TableProtocol"]
