"""A helper module for handling foreign key referential actions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy
from sqlalchemy.exc import IntegrityError

from funcy_bear.sentinels import MissingType

if TYPE_CHECKING:
    from collections.abc import Callable

    from bear_shelf.datastore.columns import ForeignKey
    from bear_shelf.datastore.database import BearBase
    from bear_shelf.datastore.record import Record
    from bear_shelf.datastore.tables.table import Table as BearTable
    from funcy_bear.query.query_mapping import where
else:
    where = lazy("funcy_bear.query.query_mapping", "where")


def fk_error(
    *strs: str,
    params: dict[str, Any] | None = None,
    orig: Exception | None = None,
) -> IntegrityError:
    """Create an IntegrityError for foreign key violations.

    Args:
        *strs: Parts of the error message to join.
        params: Optional parameters for the error.
        orig: Optional original exception to chain.

    Returns:
        IntegrityError: The constructed IntegrityError.
    """
    message: str = " ".join(strs)
    return IntegrityError(message, params=params, orig=orig if orig is not None else ValueError(message))


def handle_foreign_key_updates(
    table: BearTable,
    base: BearBase,
    records_to_update: list[Record],
    new_pk_value: Any,
) -> None:
    """Handle foreign key referential actions before updating parent PKs.

    For each child table referencing the parent:
    - CASCADE: Update child FKs to new PK value
    - SET NULL: Set child FKs to NULL
    - NO_ACTION: Allow update, orphaning records
    - RESTRICT/None: Raise IntegrityError if children exist

    Args:
        table: Parent table being updated
        base: The BearBase instance
        records_to_update: Parent records whose PKs will change
        new_pk_value: The new primary key value

    Raises:
        IntegrityError: If RESTRICT prevents update or SET NULL on non-nullable FK
    """
    from bear_shelf.datastore.common import FKAction

    parent_pk: str | None = table.primary_key
    if not parent_pk or not records_to_update:
        return

    old_pks: set[Any] = {rec[parent_pk] for rec in records_to_update}

    for child_table_name, child_table in base.get_tables().items():
        for column in child_table.get_columns():
            if column.foreign_key is None:
                continue

            fk: ForeignKey = column.split_foreign_key
            if fk.table != table.table_data.name:
                continue

            matching_children: list[Record] = [
                child for old_pk in old_pks for child in child_table.search(where(column.name) == old_pk).all()
            ]

            if not matching_children:
                continue

            if column.onupdate == FKAction.CASCADE:
                child_pk: str | None = child_table.primary_key
                if child_pk is None:
                    continue

                for child in matching_children:
                    child_table.update(
                        fields={column.name: new_pk_value},
                        cond=where(child_pk) == child[child_pk],
                    )

            elif column.onupdate == FKAction.SET_NULL:
                if not column.nullable:
                    raise fk_error(
                        f"Cannot SET NULL on non-nullable column '{column.name}' in table '{child_table_name}'",
                        orig=ValueError(f"FK column '{column.name}' is not nullable"),
                    )

                child_pk: str | None = child_table.primary_key
                if child_pk is None:
                    continue

                for child in matching_children:
                    child_table.update(fields={column.name: None}, cond=where(child_pk) == child[child_pk])

            elif column.onupdate == FKAction.NO_ACTION:
                continue  # NO_ACTION: Allow update, creating orphaned records

            else:
                raise fk_error(
                    f"Cannot update PK in '{table.table_data.name}':"
                    f"{len(matching_children)} record(s) in '{child_table_name}'"
                    f"reference it via '{column.name}'",
                    orig=ValueError(f"FK constraint violation on {child_table_name}.{column.name}"),
                )


def handle_foreign_key_deletes(
    table: BearTable,
    base: BearBase,
    records_to_delete: list[Record],
) -> None:
    """Handle foreign key referential actions before deleting parent records.

    For each child table referencing the parent:
    - CASCADE: Recursively delete child records
    - SET NULL: Update child FKs to None (requires nullable)
    - NO_ACTION: Allow delete, creating orphaned records
    - RESTRICT/None: Raise IntegrityError if children exist

    Args:
        table: Parent table being deleted from
        base: The BearBase instance
        records_to_delete: Parent records that will be deleted

    Raises:
        IntegrityError: If RESTRICT prevents deletion or SET NULL on non-nullable FK
    """
    from bear_shelf.datastore.common import FKAction

    parent_pk: str | None = table.primary_key
    if not parent_pk or not records_to_delete:
        return

    deleted_pks: set[Any] = {rec[parent_pk] for rec in records_to_delete}

    for child_table_name in base.tables():
        child_table: BearTable = base.table(child_table_name)

        for column in child_table.get_columns():
            if column.foreign_key is None:
                continue

            fk: ForeignKey = column.split_foreign_key
            if fk.table != table.table_data.name:
                continue

            matching_children: list[Record] = [
                child for pk_value in deleted_pks for child in child_table.search(where(column.name) == pk_value).all()
            ]

            if not matching_children:
                continue

            if column.ondelete == FKAction.CASCADE:  # Recursively handle FK deletes for children, then delete them
                # TODO: We should be aware of potentially circular FK dependencies here to avoid infinite recursion
                # maybe we should use a different data structure instead of recursion?
                # A stack or queue to track tables so all work can be done iteratively?
                handle_foreign_key_deletes(child_table, base, matching_children)

                child_pk: str | None = child_table.primary_key
                if child_pk is None:
                    continue

                for child in matching_children:
                    child_table.delete(cond=where(child_pk) == child[child_pk])

            elif column.ondelete == FKAction.SET_NULL:
                if not column.nullable:
                    raise fk_error(
                        f"Cannot SET NULL on non-nullable column '{column.name}' in table '{child_table_name}'",
                        orig=ValueError(f"FK column '{column.name}' is not nullable"),
                    )

                child_pk: str | None = child_table.primary_key
                if child_pk is None:
                    continue

                for child in matching_children:
                    child_table.update(
                        fields={column.name: None},
                        cond=where(child_pk) == child[child_pk],
                    )

            elif column.ondelete == FKAction.NO_ACTION:
                continue  # NO_ACTION: Allow delete, creating orphaned records

            else:
                raise fk_error(
                    f"Cannot delete from '{table.table_data.name}':",  # noqa: S608
                    f"{len(matching_children)} record(s) in '{child_table_name}'",
                    f"reference it via '{column.name}'",
                    orig=ValueError(f"FK constraint violation on {child_table_name}.{column.name}"),
                )


def validate_foreign_keys(
    table: BearTable,
    parameters: dict[str, Any],
    get_table: Callable[..., BearTable | MissingType],
) -> None:
    """Validate that all foreign key values exist in their referenced tables.

    Raises:
        IntegrityError: If a foreign key value doesn't exist in the parent table
    """
    for column in table.get_columns():
        if column.foreign_key is None or column.name not in parameters:
            continue

        fk_value: Any = parameters[column.name]
        if fk_value is None and column.nullable:
            continue

        fk: ForeignKey = column.split_foreign_key
        if fk.is_notset:
            continue

        parent_table: BearTable | MissingType = get_table(fk.table, cursor=None, reset=False)
        if isinstance(parent_table, MissingType):
            raise fk_error(
                f"Foreign key constraint failed: referenced table '{fk.table}' does not exist",
                orig=ValueError(f"Table '{fk.table}' not found"),
            )

        parent_pk: str | None = parent_table.primary_key
        if parent_pk is None:
            continue

        matching_records: list[Record] = parent_table.search(where(parent_pk) == fk_value).all()
        if not matching_records:
            raise fk_error(
                f"Foreign key constraint failed on column '{column.name}':"
                f"value {fk_value!r} does not exist in {fk.table}.{fk.column}",
                orig=ValueError(f"FK value {fk_value!r} not found in {fk.table}"),
            )


# ruff: noqa: PLC0415
