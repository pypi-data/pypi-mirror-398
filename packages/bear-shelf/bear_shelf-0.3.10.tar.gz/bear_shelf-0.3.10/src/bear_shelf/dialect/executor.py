"""Executor for DML operations in BearShelf dialect."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

from bear_shelf.dialect import protocols as pro
from funcy_bear.sentinels import MISSING, MissingType

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy import BindParameter, Delete, Insert, Select, Table, Update
    from sqlalchemy.engine.default import DefaultExecutionContext
    from sqlalchemy.sql.compiler import Compiled

    from bear_shelf.datastore.record import Record, Records
    from bear_shelf.datastore.tables.table import Table as BearTable
    from bear_shelf.dialect.bear_dialect import BearShelfDialect
    from bear_shelf.dialect.common import AggregateResult
    from bear_shelf.dialect.cursor import BearCursor
    from bear_shelf.dialect.descript import Descriptor, get_descriptor
    from bear_shelf.dialect.helpers import _aggregate_functions as agg, _extract_values as ext
    from bear_shelf.dialect.helpers._check_clauses import check_clauses
    from bear_shelf.dialect.helpers._foreign_keys import (
        handle_foreign_key_deletes as fk_deletes,
        handle_foreign_key_updates as fk_updates,
        validate_foreign_keys,
    )
    from funcy_bear.query import QueryInstance

else:
    check_clauses = lazy("bear_shelf.dialect.helpers._check_clauses", "check_clauses")
    Descriptor, get_descriptor = lazy("bear_shelf.dialect.descript", "Descriptor", "get_descriptor")
    fk_deletes, fk_updates, validate_foreign_keys = lazy(
        "bear_shelf.dialect.helpers._foreign_keys",
        "handle_foreign_key_deletes",
        "handle_foreign_key_updates",
        "validate_foreign_keys",
    )
    ext = lazy("bear_shelf.dialect.helpers._extract_values")
    agg = lazy("bear_shelf.dialect.helpers._aggregate_functions")

type Results = list[tuple[Any, ...]]


def _get_row(record: dict[str, Any], selected_cols: list[str]) -> tuple[Any, ...]:
    cols = []
    if selected_cols:
        for col in selected_cols:
            cols.append(record.get(col))
        return tuple(cols)
    return tuple(record.values())


class DMLExecutor:
    """Handles DML (INSERT/UPDATE/DELETE) operations."""

    def __init__(self, dialect: Any) -> None:
        """Initialize DMLExecutor with dialect reference."""
        self.dialect: BearShelfDialect = dialect

    def execute_select(
        self,
        compiled: Compiled,
        cursor: BearCursor,
        parameters: dict[str, Any] | None = None,
    ) -> Results:
        """Execute SELECT statement."""
        from bear_shelf.datastore.record import Records

        statement: Select | None = compiled.statement  # type: ignore[reportOptionalMemberAccess]
        if statement is None:
            raise ValueError("Compiled statement is None in execute_select.")
        table_name: str | None = ext.extract_table_name(statement)
        if table_name is None:
            return []
        table: BearTable | MissingType = self.get_table(table_name, cursor, reset=False)
        if isinstance(table, MissingType):
            return []

        result: AggregateResult = agg.aggregate_functions(
            statement,
            self.dialect.base,
            table_name,
            parameters,
        )
        if result.not_null:
            cursor.set_descriptor(name=result.label)
            return [result.value]

        where_clause: QueryInstance | None = agg._translate_where_clause(statement, parameters)

        order_by_info: list[tuple[str, bool]] = ext.extract_order_by(statement)
        bear_records: list[Record] = self.dialect._get_records(table, order_by_info, where_clause)
        records_obj = Records(bear_records)

        records_obj: Records = check_clauses(statement, parameters, records_obj)

        records: list[dict[str, Any]] = [rec.model_dump() for rec in records_obj.all()]
        col_names: ext.ColumnNames = ext.extract_names(statement, compiled)

        if ext.is_distinct(statement):
            records = (
                ext.single_col_distinct(records, col_names.selected_columns)
                if len(col_names.selected_columns) == 1
                else ext.multi_col_distinct(records, col_names.selected_columns)
            )

        results: Results = [_get_row(rec, col_names.selected_columns) for rec in records]

        if col_names.has_selected:
            tbl: Table | None = self.dialect.get_table(table_name)
            descriptors: list[Descriptor] = get_descriptor(tbl, col_names)
            cursor.set_descriptor(descriptor=descriptors)
        return results

    def execute_insert(
        self,
        table: BearTable,
        cursor: BearCursor,
        parameters: dict[str, Any],
    ) -> None:
        """Execute INSERT for a single record."""
        from bear_shelf.datastore.record import Record

        primary_key_name: str | None = table.primary_key
        is_autoincrement: bool = table.table_data.is_auto if primary_key_name else False

        validate_foreign_keys(table, parameters, self.get_table)

        if is_autoincrement and primary_key_name in parameters and parameters[primary_key_name] is None:
            parameters = {k: v for k, v in parameters.items() if k != primary_key_name}

        record = Record(**parameters)
        table.insert(record)
        cursor.set_row_count(1)
        if primary_key_name is not None and primary_key_name in record:
            cursor.set_last_row_id(record[primary_key_name])

    def execute_insert_many(
        self,
        table: BearTable,
        cursor: BearCursor,
        parameters: list[dict[str, Any]],
    ) -> None:
        """Execute INSERT for multiple records (executemany)."""
        from bear_shelf.datastore.record import Record

        primary_key_name: str | None = table.primary_key
        is_autoincrement: bool = table.table_data.is_auto if primary_key_name else False

        for params in parameters:
            validate_foreign_keys(table, params, self.get_table)

        records: list[Record] = []
        for params in parameters:
            if is_autoincrement and primary_key_name in params and params[primary_key_name] is None:
                filtered_params: dict[str, Any] = {k: v for k, v in params.items() if k != primary_key_name}
                records.append(Record(**filtered_params))
            else:
                records.append(Record(**params))

        table.insert_all(records)
        if records and primary_key_name is not None:
            last_record: Record = records[-1]
            if primary_key_name in last_record:
                cursor.set_last_row_id(last_record[primary_key_name])

        cursor.set_row_count(len(parameters))

    def execute_update(
        self,
        table: BearTable,
        cursor: BearCursor,
        statement: Update,
        parameters: dict[str, Any] | None,
    ) -> None:
        """Execute UPDATE for a single parameter set."""
        updates: dict[str, Any] = ext.extract_update_values(statement, parameters)

        validate_foreign_keys(table, updates, self.get_table)
        where_clause: QueryInstance | None = agg._translate_where_clause(statement, parameters)

        parent_pk: str | None = table.primary_key
        if parent_pk and parent_pk in updates:
            records_to_update: list[Record] = table.search(where_clause).all() if where_clause else table.all()
            self.handle_foreign_key_updates(table, records_to_update, updates[parent_pk])

        count: int = table.update(updates, cond=where_clause)
        cursor.set_row_count(count)

    def execute_update_many(
        self,
        table: BearTable,
        cursor: BearCursor,
        statement: Update,
        parameters: list[dict[str, Any]],
    ) -> None:
        """Execute UPDATE for multiple parameter sets (executemany)."""
        total_count = 0
        for params in parameters:
            self.execute_update(table, cursor, statement, params)
            total_count += cursor.rowcount
        cursor.set_row_count(total_count)

    def execute_delete(
        self,
        table: BearTable,
        cursor: BearCursor,
        statement: Delete,
        parameters: dict[str, Any] | None,
    ) -> None:
        """Execute DELETE for a single parameter set."""
        where_clause: QueryInstance | None = agg._translate_where_clause(statement, parameters)

        if where_clause is None:
            raise ValueError("DELETE requires WHERE clause for safety. Use DELETE WHERE 1=1 for all records.")

        records_to_delete: list[Record] = table.search(where_clause).all()
        self.handle_foreign_key_deletes(table, records_to_delete)

        count: int = table.delete(cond=where_clause)
        cursor.set_row_count(count)

    def execute_delete_many(
        self,
        table: BearTable,
        cursor: BearCursor,
        statement: Delete,
        parameters: list[dict[str, Any]],
    ) -> None:
        """Execute DELETE for multiple parameter sets (executemany)."""
        total_count = 0
        for params in parameters:
            self.execute_delete(table, cursor, statement, params)
            total_count += cursor.rowcount
        cursor.set_row_count(total_count)

    def get_table(self, table_name: str, cursor: BearCursor | None, reset: bool = True) -> BearTable | MissingType:
        """Guard: check table exists

        Args:
            table_name: Name of the table
            cursor: BearCursor instance
            reset: Whether to reset the cursor rowcount if table not found
        Returns:
            BearTable instance or MISSING sentinel if not found
        """
        if self.dialect.not_name_in_table(str(table_name)):
            if reset and cursor is not None:
                cursor.reset_row_count()
            return MISSING
        return self.dialect.base.table(table_name)

    def handle_foreign_key_deletes(self, table: BearTable, records_to_delete: list[Record]) -> None:
        """Handle foreign key referential actions before deleting parent records.

        For each child table referencing the parent:
        - CASCADE: Recursively delete child records
        - SET NULL: Update child FKs to None (requires nullable)
        - NO_ACTION: Allow delete, creating orphaned records
        - RESTRICT/None: Raise IntegrityError if children exist

        Args:
            table: Parent table being deleted from
            records_to_delete: Parent records that will be deleted

        Raises:
            IntegrityError: If RESTRICT prevents deletion or SET NULL on non-nullable FK
        """
        fk_deletes(table, self.dialect.base, records_to_delete)

    def handle_foreign_key_updates(self, table: BearTable, records_to_update: list[Record], new_pk_value: Any) -> None:
        """Handle foreign key referential actions before updating parent PKs.

        For each child table referencing the parent:
        - CASCADE: Update child FKs to new PK value
        - SET NULL: Set child FKs to NULL
        - NO_ACTION: Allow update, orphaning records
        - RESTRICT/None: Raise IntegrityError if children exist

        Args:
            table: Parent table being updated
            records_to_update: Parent records whose PKs will change
            new_pk_value: The new primary key value

        Raises:
            IntegrityError: If RESTRICT prevents update or SET NULL on non-nullable FK
        """
        fk_updates(table, self.dialect.base, records_to_update, new_pk_value)

    def do_execute(
        self,
        cursor: BearCursor,
        statement: Select | Insert | Update | Delete | str,
        parameters: dict[str, Any] | None = None,
        context: DefaultExecutionContext | None = None,
        tables: dict[str, Table] | None = None,
    ) -> Any:
        """Execute a statement against the data store."""
        if tables is None:
            tables = {}
        if not (context and isinstance(context, pro.Compiled)):
            cursor.execute(statement, parameters or (), context=context)
            return cursor

        compiled: Compiled | None = context.compiled

        if isinstance(compiled, pro.CompiledStatement) and isinstance(compiled.statement, pro.SelectableStatement):
            results: list[tuple[Any, ...]] = self.execute_select(compiled, cursor, parameters)
            cursor.set_results(results)
            return cursor

        if isinstance(compiled, pro.InsertStatement) and compiled.isinsert:
            insert_statement: Insert = compiled.statement  # pyright: ignore[reportAssignmentType]
            table: BearTable | MissingType = self.get_table(insert_statement.table.name, cursor, reset=False)
            if not parameters or isinstance(table, MissingType):
                cursor.reset_row_count()
                return cursor

            if isinstance(parameters, list):
                self.execute_insert_many(table, cursor, parameters)
            else:
                self.execute_insert(table, cursor, parameters)
            return cursor

        if isinstance(compiled, pro.UpdateStatement) and compiled.isupdate:
            update_statement: Update = compiled.statement  # pyright: ignore[reportAssignmentType]
            if not isinstance(update_statement.table, pro.ColumnWithName):
                cursor.reset_row_count()
                return cursor
            table: BearTable | MissingType = self.get_table(str(update_statement.table.name), cursor, reset=False)
            if isinstance(table, MissingType):
                cursor.reset_row_count()
                return cursor

            if isinstance(parameters, list):
                self.execute_update_many(table, cursor, update_statement, parameters)
            else:
                self.execute_update(table, cursor, update_statement, parameters)
            return cursor

        if isinstance(compiled, pro.DeleteStatement) and compiled.isdelete:
            delete_statement: Delete = compiled.statement  # pyright: ignore[reportAssignmentType]
            if not isinstance(delete_statement.table, pro.ColumnWithName):
                cursor.reset_row_count()
                return cursor
            table: BearTable | MissingType = self.get_table(str(delete_statement.table.name), cursor, reset=False)
            if isinstance(table, MissingType):
                cursor.reset_row_count()
                return cursor

            if isinstance(parameters, list):
                self.execute_delete_many(table, cursor, delete_statement, parameters)
            else:
                self.execute_delete(table, cursor, delete_statement, parameters)
            return cursor
        return cursor


def bind_parameters_to_dict(parameters: Sequence[BindParameter]) -> dict[str, Any]:
    """Convert a sequence of BindParameter to a dictionary for easy lookup.

    Args:
        parameters: Sequence of BindParameter objects
    Returns:
        Dictionary mapping bind parameter keys to their values
    """
    return {param.key: param.value for param in parameters}


# ruff: noqa: PLC0415
