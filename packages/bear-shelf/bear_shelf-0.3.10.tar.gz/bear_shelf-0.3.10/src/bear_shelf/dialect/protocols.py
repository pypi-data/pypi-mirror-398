"""Protocol definitions for SQLAlchemy statement types."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CompiledStatement(Protocol):
    """Protocol for compiled SQLAlchemy statements."""

    statement: Any
    _result_columns: Any


@runtime_checkable
class InsertStatement(Protocol):
    """Protocol for INSERT compiled statements."""

    isinsert: bool


@runtime_checkable
class UpdateStatement(Protocol):
    """Protocol for UPDATE compiled statements."""

    isupdate: bool


@runtime_checkable
class DeleteStatement(Protocol):
    """Protocol for DELETE compiled statements."""

    isdelete: bool


@runtime_checkable
class SelectableStatement(Protocol):
    """Protocol for SELECT-like statements."""

    def get_final_froms(self) -> Any:
        """Get the final FROM clauses."""

    _where_criteria: Any
    selected_columns: Any


@runtime_checkable
class TableReference(Protocol):
    """Protocol for table references."""

    name: str


@runtime_checkable
class ColumnWithKey(Protocol):
    """Protocol for columns with key attribute."""

    key: str


@runtime_checkable
class ColumnWithName(Protocol):
    """Protocol for columns with name attribute."""

    name: str


@runtime_checkable
class UpdateStatementWithValues(Protocol):
    """Protocol for UPDATE statements with _values attribute."""

    _values: dict[Any, Any]
    _where_criteria: Any

    @property
    def table(self) -> TableReference:
        """Get the table reference."""
        ...


@runtime_checkable
class BindParameterKey(Protocol):
    """Protocol for bind parameters."""

    key: Any


@runtime_checkable
class BindParameterOrigKey(Protocol):
    """Protocol for bind parameters."""

    _orig_key: str


@runtime_checkable
class BindParameterWithEffectiveValue(Protocol):
    """Protocol for bind parameters with effective_value."""

    effective_value: Any
    key: Any


@runtime_checkable
class BindParameterWithValue(Protocol):
    """Protocol for bind parameters with value."""

    value: Any
    key: Any


@runtime_checkable
class Compiled(Protocol):
    """Protocol for compiled SQLAlchemy objects."""

    compiled: Any


@runtime_checkable
class InsertCompiled(Protocol):
    """Protocol for compiled INSERT statements."""

    isinsert: bool
    compiled: Any


@runtime_checkable
class OrderByClause(Protocol):
    """Protocol for ORDER BY clauses."""

    _order_by_clauses: Any


@runtime_checkable
class LimitOffsetClause(Protocol):
    """Protocol for LIMIT and OFFSET clauses."""

    _limit_clause: Any
    _offset_clause: Any
