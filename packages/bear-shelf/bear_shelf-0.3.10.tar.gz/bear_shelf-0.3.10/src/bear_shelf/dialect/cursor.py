"""A basic cursor for the Bear Shelf dialect."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from lazy_bear import lazy

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.engine.interfaces import _DBAPISingleExecuteParams
    from sqlalchemy.types import TypeEngine

    from bear_shelf.dialect.descript import Descriptor
else:
    Descriptor = lazy("bear_shelf.dialect.descript", "Descriptor")


class BearCursor:
    """A basic cursor implementation for Bear Shelf dialect."""

    def __init__(self) -> None:
        """Initialize the cursor."""
        self._rowcount: int = -1
        self._description: list[Descriptor] | None = None
        self._result_set: list[tuple[Any, ...]] = []
        self._current_index = 0
        self._context: Any = None
        self.arraysize: int = 1
        self.lastrowid: int = 0

    @property
    def description(self) -> list[Descriptor]:
        """Return the description of the result set."""
        if self._description is None:
            return [Descriptor()]
        return self._description

    @description.setter
    def description(self, value: list[Descriptor]) -> None:
        """Set the description of the result set."""
        self._description = value

    @property
    def rowcount(self) -> int:
        """Return the number of rows affected by the last operation."""
        return self._rowcount

    @rowcount.setter
    def rowcount(self, value: int) -> None:
        """Set the number of rows affected by the last operation."""
        self._rowcount = value

    def execute(self, operation: Any, parameters: _DBAPISingleExecuteParams | None = None, context=None) -> Self:  # noqa: ANN001, ARG002
        """Execute a statement against the data store."""
        self._context = context
        self._result_set = []
        self._current_index = 0
        self.rowcount = 0
        return self

    def set_results(self, results: list[tuple[Any, ...]]) -> None:
        """Set the result set (called by dialect)."""
        self._result_set = results
        self.rowcount = len(results)

    def executemany(self, operation: str, parameters: Any) -> Self:  # noqa: ARG002
        """Execute many statements (for bulk inserts)."""
        self._context = None
        self._result_set = []
        self._current_index = 0
        self.rowcount = 0
        return self

    def fetchall(self) -> list[tuple[Any, ...]]:
        """Fetch all remaining rows."""
        results: list[tuple[Any, ...]] = self._result_set[self._current_index :]
        self._current_index = len(self._result_set)
        return results

    def fetchone(self) -> tuple[Any, ...] | None:
        """Fetch one row."""
        if self._current_index < len(self._result_set):
            result: tuple[Any, ...] = self._result_set[self._current_index]
            self._current_index += 1
            return result
        return None

    def fetchmany(self, size: int | None = None) -> list[tuple[Any, ...]]:
        """Fetch multiple rows."""
        if size is None:
            size = 1
        end_index: int = min(self._current_index + size, len(self._result_set))
        results: list[tuple[Any, ...]] = self._result_set[self._current_index : end_index]
        self._current_index: int = end_index
        return results

    def setinputsizes(self, sizes: Sequence[Any]) -> None:
        """Set input sizes - no-op for Bear Shelf."""

    def setoutputsize(self, size: int, column: int | None = None) -> None:
        """Set output size - no-op for Bear Shelf."""

    def callproc(self, procname: str, parameters: Sequence[Any] | None = None) -> Any:
        """Call a stored procedure - not implemented for Bear Shelf."""
        raise NotImplementedError("Stored procedures are not supported in Bear Shelf dialect.")

    def nextset(self) -> bool | None:
        """Move to the next result set - not implemented for Bear Shelf."""
        return None

    def reset_row_count(self) -> None:
        """Reset the rowcount to -1 (no rows affected)."""
        self.rowcount = -1

    def set_row_count(self, c: int) -> None:
        """Set the rowcount value."""
        self.rowcount = c

    def set_last_row_id(self, rid: int = 0) -> None:
        """Set the lastrowid value."""
        self.lastrowid = rid

    def set_descriptor(
        self,
        *,
        descriptor: list[Descriptor] | None = None,
        name: str = "",
        type_code: TypeEngine | None = None,
        display_size: int | None = None,
        internal_size: int | None = None,
        precision: int | None = None,
        scale: int | None = None,
        null_ok: bool | None = None,
    ) -> None:
        """Set the description value."""
        if descriptor is not None:
            self.description = descriptor
        else:
            self.description = [Descriptor(name, type_code, display_size, internal_size, precision, scale, null_ok)]

    def close(self) -> None:
        """Close the cursor."""
        self._result_set = []
        self._current_index = 0

    def __getattr__(self, name: str) -> Any:
        """Forward all unknown attribute calls to the underlying cursor."""
        raise AttributeError(f"BearCursor has no attribute '{name}'")

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> tuple[Any, ...]:
        result: tuple[Any, ...] | None = self.fetchone()
        if result is None:
            raise StopIteration
        return result

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()
