from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

if TYPE_CHECKING:
    from sqlalchemy.sql.dml import Delete, Update
    from sqlalchemy.sql.selectable import Select

    from bear_shelf.datastore import BearBase
    from bear_shelf.datastore.record import Record
    from bear_shelf.datastore.tables.table import Table
    from bear_shelf.dialect.common import AggregateResult
    from bear_shelf.dialect.sql_translator import translate_where_clause
    from funcy_bear.query import QueryInstance
else:
    translate_where_clause = lazy("bear_shelf.dialect.sql_translator", "translate_where_clause")


def get_name(c: Any) -> str:
    """Extract the column name from a SQLAlchemy column expression.

    Args:
        c: SQLAlchemy column expression
    Returns:
        The name of the column as a string
    """
    if hasattr(c, "clauses") and hasattr(c.clauses, "clauses"):
        inner_column: Any = next(iter(c.clauses.clauses))
        return inner_column.name
    return ""


def aggregate_functions(
    statement: Any,
    base: BearBase,
    table_name: str,
    parameters: dict[str, Any] | None,
) -> AggregateResult:
    """Check if statement contains aggregate functions and compute them.

    Returns:
        A tuple with the aggregate result, or None if no aggregates found.
    """
    from bear_shelf.dialect.common import NULL_RESULT, AggregateResult, Result  # noqa: PLC0415

    if table_name not in base.tables() or not hasattr(statement, "selected_columns"):
        return NULL_RESULT
    table: Table = base.table(table_name)
    where_clause: QueryInstance | None = _translate_where_clause(statement, parameters)
    records: list[Record] = table.search(where_clause).all() if where_clause else table.all()
    for col in statement.selected_columns:
        column_name: str = get_name(col)
        all_values: bool = column_name == "*"
        if col.name == "sum":
            values = [rec.get(column_name, 0) for rec in records if rec.get(column_name) is not None]
            return AggregateResult(
                Result(n=sum(values)),
                "sum_1",
            )
        if col.name == "avg":
            values = [rec.get(column_name, 0) for rec in records if rec.get(column_name) is not None]
            return AggregateResult(
                Result(n=(sum(values) / len(values) if values else 0)),
                "avg_1",
            )
        if col.name == "min":
            values = [rec.get(column_name, 0) for rec in records if rec.get(column_name) is not None]
            return AggregateResult(
                Result(n=min(values) if values else 0),
                "min_1",
            )
        if col.name == "max":
            values = [rec.get(column_name, 0) for rec in records if rec.get(column_name) is not None]
            return AggregateResult(
                Result(n=max(values) if values else 0),
                "max_1",
            )
        if col.name == "count":
            non_null_count: int = sum(1 for rec in records if rec.get(column_name) is not None)
            return AggregateResult(
                Result(n=len(records) if all_values else non_null_count),
                "count_1",
            )
    return NULL_RESULT


def _translate_where_clause(
    statement: Any | Select | Update | Delete,
    parameters: dict[str, Any] | None,
) -> QueryInstance | None:
    """Translate WHERE clause from statement to QueryMapping."""
    if not hasattr(statement, "_where_criteria") or not statement._where_criteria:
        return None
    where_expr: Any = statement._where_criteria[0]
    return translate_where_clause(where_expr, parameters)
