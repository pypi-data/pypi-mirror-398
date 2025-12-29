from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, NamedTuple, cast

from lazy_bear import lazy

from bear_shelf.dialect import protocols as pro
from funcy_bear.sentinels import CONTINUE, ContinueType

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy import (
        BIGINT,
        BOOLEAN,
        DECIMAL,
        FLOAT,
        INTEGER,
        SMALLINT,
        TEXT,
        VARCHAR,
        Column,
        ColumnCollection,
        ColumnDefault,
        ColumnElement,
        ForeignKey,
        Select,
    )
    from sqlalchemy.sql import ClauseElement
    from sqlalchemy.sql.compiler import Compiled, ResultColumnsEntry
    from sqlalchemy.sql.dml import Update
    from sqlalchemy.sql.schema import Table
    from sqlalchemy.types import TypeEngine

    from bear_shelf.datastore.columns import Columns
    from bear_shelf.datastore.common import FKAction
    from bear_shelf.dialect.helpers._dispatchers import params_check, value_check
else:
    value_check, params_check = lazy("bear_shelf.dialect.helpers._dispatchers", "value_check", "params_check")
    FKAction = lazy("bear_shelf.datastore.common", "FKAction")
    Columns = lazy("bear_shelf.datastore.columns", "Columns")
    Update = lazy("sqlalchemy.sql.dml", "Update")
    ColumnCollection = lazy("sqlalchemy", "ColumnCollection")
    sqlalchemy = lazy("sqlalchemy")
    Column, Select = sqlalchemy.to("Column", "Select")
    BIGINT, BOOLEAN, DECIMAL, FLOAT, INTEGER, SMALLINT, TEXT, VARCHAR = sqlalchemy.to(
        "BIGINT",
        "BOOLEAN",
        "DECIMAL",
        "FLOAT",
        "INTEGER",
        "SMALLINT",
        "TEXT",
        "VARCHAR",
    )


def is_update_statement(statement: Any) -> bool:
    """Check if the statement is an UPDATE statement."""
    return isinstance(statement, Update)


def extract_update_values(statement: Update, parameters: dict[str, Any] | None) -> dict[str, Any]:
    """Extract SET clause values from UPDATE statement.

    When statement caching is enabled, bind parameters in the statement contain stale values.
    The runtime parameters dict contains fresh values, so we must prioritize it.
    """
    updates: dict[str, Any] = {}
    if is_update_statement(statement) and statement._values:
        for column, value_expr in statement._values.items():
            column_key: Any = value_check(column)
            if parameters and column_key in parameters:
                updates[column_key] = parameters[column_key]
            else:
                flow: Any | ContinueType = params_check(value_expr, column_key, updates)
                if flow is CONTINUE:
                    continue
    if not updates and parameters:
        updates = parameters.copy()
    return updates


def extract_selected_columns(statement: Any) -> list[str]:
    """Extract column names from SELECT statement."""
    columns: list[str] = []
    if not isinstance(statement, Select):
        return columns
    for col in statement.selected_columns:
        if isinstance(col, ColumnCollection):
            for sub_col in col:
                columns.append(value_check(sub_col))
        elif isinstance(col, pro.ColumnWithName):
            columns.append(col.name)
    return columns


def extract_limit(statement: Any) -> int | None:
    """Extract LIMIT clause from SELECT statement."""
    if hasattr(statement, "_limit_clause") and statement._limit_clause is not None:
        limit_clause: ColumnElement = statement._limit_clause
        if hasattr(limit_clause, "value"):
            return int(cast("int", limit_clause.value))
        return int(cast("int", limit_clause))
    return None


def extract_offset(statement: Any) -> int | None:
    """Extract OFFSET clause from SELECT statement."""
    if isinstance(statement, pro.LimitOffsetClause) and statement._offset_clause is not None:
        offset_clause: ColumnElement = statement._offset_clause
        if hasattr(offset_clause, "value"):
            return int(cast("int", offset_clause.value))
        return int(cast("int", offset_clause))
    return None


def extract_order_by(statement: Any) -> list[tuple[str, bool]]:
    """Extract ORDER BY clause from SELECT statement.

    Returns:
        List of tuples (column_name, is_descending)
    """
    order_by_clauses: list[tuple[str, bool]] = []
    if isinstance(statement, pro.OrderByClause) and statement._order_by_clauses:
        for clause in statement._order_by_clauses:
            is_desc: bool = hasattr(clause, "modifier") and clause.modifier is not None
            col: ColumnElement = clause.element if hasattr(clause, "element") else clause
            if hasattr(col, "_is_keyed_column_element") and isinstance(col.key, str):
                order_by_clauses.append((col.key, is_desc))
            elif hasattr(col, "name") and isinstance(col.name, str):
                order_by_clauses.append((col.name, is_desc))
    return order_by_clauses


def extract_table_name(statement: Any | Select) -> str | None:
    """Extract table name from a statement."""
    if not hasattr(statement, "get_final_froms"):
        return None
    froms: Any = statement.get_final_froms()
    if not froms:
        return None
    table: Any = next(iter(froms))
    return table.name


def is_distinct(statement: Any) -> bool:
    """Check if SELECT statement has DISTINCT.

    Returns:
        True if DISTINCT is requested
    """
    return hasattr(statement, "_distinct") and statement._distinct


def single_col_distinct(records: list[dict[str, Any]], selected_columns: list[str]) -> list[dict[str, Any]]:
    """Return a DISTINCT version of the SELECT statement."""
    seen: set[Any] = set()
    unique_records: list[dict[str, Any]] = []
    col: str = selected_columns[0]
    for record in records:
        val: Any | None = record.get(col)
        hashable_val: tuple | None = tuple(val) if isinstance(val, list) else val
        if hashable_val not in seen:
            seen.add(hashable_val)
            unique_records.append(record)
    return unique_records


def multi_col_distinct(records: list[dict[str, Any]], selected_columns: list[str]) -> list[dict[str, Any]]:
    """Return a DISTINCT version of the SELECT statement for multiple columns."""
    seen_tuples: set[tuple[Any, ...]] = set()
    unique_records: list[dict[str, Any]] = []
    for record in records:
        key: tuple[Any | None, ...] = (
            tuple(record.get(col) for col in selected_columns) if selected_columns else tuple(record.values())
        )
        if key not in seen_tuples:
            seen_tuples.add(key)
            unique_records.append(record)
    return unique_records


def auto_increment(primary: Any, col_type: Any, autoinc: Any) -> bool:
    """Determine if autoincrement should be set for a column.

    Args:
        primary: Whether the column is a primary key.
        col_type: The type of the column.
        autoinc: The autoincrement flag from SQLAlchemy, this can be True, False, or 'auto'.

    Returns:
        True if autoincrement should be enabled, False otherwise.

    Raises:
        ValueError: If autoinc is True but the column type is not integer. We specifically do not
        raise if autoinc is 'auto' and the type is non-integer, as this is a valid configuration.
    """
    if autoinc is True and str(col_type).lower() not in {"int", "integer"}:
        raise ValueError(
            f"Cannot use autoincrement=True on non-integer type '{col_type}'. "
            f"Autoincrement only works with integer types!"
        )
    return primary is True and autoinc and str(col_type).lower() in {"int", "integer"}


def fk_work(column: Column) -> tuple[str | None, FKAction | None, FKAction | None]:
    """Extract ondelete and onupdate actions from a ForeignKey."""
    ondelete: FKAction | None = None
    onupdate: FKAction | None = None
    f_keys: set[ForeignKey] = column.foreign_keys
    if not f_keys:
        return None, ondelete, onupdate

    fk_constraint: ForeignKey = next(iter(f_keys))

    with suppress(AttributeError):
        if fk_constraint.ondelete is not None:
            ondelete = FKAction(fk_constraint.ondelete.upper())
    with suppress(AttributeError):
        if fk_constraint.onupdate is not None:
            onupdate = FKAction(fk_constraint.onupdate.upper())
    return fk_constraint.target_fullname, ondelete, onupdate


SQLAlchemyTypeMapping: dict[str, str] = {
    "INTEGER": "int",
    "SMALLINT": "int",
    "BIGINT": "int",
    "VARCHAR": "str",
    "TEXT": "str",
    "BOOLEAN": "bool",
    "FLOAT": "float",
    "DECIMAL": "float",
}
SQLtoTypeMapping: dict[str, str] = {v: k for k, v in SQLAlchemyTypeMapping.items()}

_ToTypeSQLAlchemy: dict[str, TypeEngine] = {}


def map_to_sqlalchemy_type(sqlalchemy_type: str) -> str:
    """Map SQLAlchemy types to string representations."""
    type_str: str = str(sqlalchemy_type).upper()
    return SQLAlchemyTypeMapping.get(type_str, "str")


def map_from_sqlalchemy_type(type_str: str) -> TypeEngine:
    """Map string representations to SQLAlchemy types."""
    global _ToTypeSQLAlchemy  # noqa: PLW0602
    if not _ToTypeSQLAlchemy:
        _ToTypeSQLAlchemy.update(
            {
                "INTEGER": INTEGER(),
                "SMALLINT": SMALLINT(),
                "BIGINT": BIGINT(),
                "VARCHAR": VARCHAR(),
                "TEXT": TEXT(),
                "BOOLEAN": BOOLEAN(),
                "FLOAT": FLOAT(),
                "DECIMAL": DECIMAL(),
            }
        )

    sqlalchemy_type_str: str = SQLtoTypeMapping.get(type_str.lower(), "TEXT")
    return _ToTypeSQLAlchemy.get(sqlalchemy_type_str, TEXT())


def get_columns(table: Table) -> list[Columns]:
    """Extract Columns definitions from a SQLAlchemy Table."""
    cols: list[Columns] = []
    for c in table.columns:
        col_type: str = map_to_sqlalchemy_type(cast("str", c.type))
        auto_inc_literal: bool = auto_increment(c.primary_key, col_type, c.autoincrement)
        default_value: Any = cast("ColumnDefault", c.default).arg if c.default is not None else None
        foreign_key, ondelete, onupdate = fk_work(c)
        cols.append(
            Columns.create(
                name=c.name,
                type=col_type,
                default=0 if auto_inc_literal and default_value is None else default_value,
                nullable=bool(c.nullable) if not c.primary_key else False,
                primary_key=bool(c.primary_key),
                autoincrement=auto_inc_literal if auto_inc_literal else None,
                unique=bool(c.unique),
                comment=str(c.comment) if c.comment is not None else None,
                foreign_key=foreign_key if foreign_key is not None else None,
                ondelete=ondelete,
                onupdate=onupdate,
            )
        )
    return cols


class ColumnNames(NamedTuple):
    """A named tuple to hold selected column names and result column names."""

    selected_columns: list[str]
    result_column_names: list[str]

    @property
    def no_selected(self) -> bool:
        """Check if there are no selected columns."""
        return not self.selected_columns

    @property
    def has_selected(self) -> bool:
        """Check if there are selected columns."""
        return bool(self.selected_columns)

    def zipped(self) -> Generator[tuple[str, str], Any]:
        """Iterate over selected columns and result column names."""
        yield from zip(self.selected_columns, self.result_column_names, strict=True)


def extract_names(statement: ClauseElement | None, compiled: Compiled) -> ColumnNames:
    """Extract selected columns and their aliases from a compiled statement."""
    result_cols: list[ResultColumnsEntry] | None = compiled._result_columns
    if result_cols is None:
        return ColumnNames(
            selected_columns=[],
            result_column_names=extract_selected_columns(statement),
        )

    selected_columns: list[str] = []
    result_column_names: list[str] = []

    for rc in result_cols:
        col_obj: Column | None = next((obj for obj in rc.objects if isinstance(obj, Column)), None)

        if col_obj is not None:
            selected_columns.append(col_obj.name)
            result_column_names.append(rc.keyname)

    return ColumnNames(
        selected_columns=selected_columns,
        result_column_names=result_column_names,
    )
