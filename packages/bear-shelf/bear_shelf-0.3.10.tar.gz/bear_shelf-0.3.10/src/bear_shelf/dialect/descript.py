"""A simple descriptor for cursor.description."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from sqlalchemy import Column, Table
    from sqlalchemy.types import TypeEngine

    from bear_shelf.dialect.helpers._extract_values import ColumnNames


class Descriptor(NamedTuple):
    """A simple descriptor for cursor.description."""

    name: str = ""
    type_code: TypeEngine | None = None
    display_size: int | None = None
    internal_size: int | None = None
    precision: int | None = None
    scale: int | None = None
    null_ok: bool | None = None


def get_descriptor(table: Table | None, columns: ColumnNames) -> list[Descriptor]:
    """Build cursor.description with actual column metadata from table definition."""

    def to_descript(name: str, col: Column | None, type_code: Any = None, null_ok: bool | None = None) -> Descriptor:
        if col is not None:
            return Descriptor(name=name, type_code=col.type, null_ok=col.nullable)
        return Descriptor(name=name, type_code=type_code, null_ok=null_ok)

    if table is None:
        return [Descriptor(name=col_name) for col_name in columns.selected_columns]

    descriptors: list[Descriptor] = []
    for base_name, alias_name in columns.zipped():
        column: Column[Any] | None = table.columns.get(base_name) if table is not None else None
        descriptors.append(to_descript(alias_name, column))
    return descriptors
