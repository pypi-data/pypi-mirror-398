from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.sql import Select

    from bear_shelf.datastore.record import Records


def check_clauses(
    statement: Select,
    parameters: dict[str, Any] | None,
    records_obj: Records,
) -> Records:
    limit_value: int | None = None
    offset_value: int | None = None

    has_limit: bool = statement._limit_clause is not None
    has_offset: bool = statement._offset_clause is not None

    if parameters and (has_limit or has_offset):
        if has_limit and has_offset:
            limit_value = parameters.get("param_1")
            offset_value = parameters.get("param_2")
        elif has_limit:
            limit_value = parameters.get("param_1")
        elif has_offset:
            offset_value = parameters.get("param_1")

    if offset_value is not None:
        records_obj = records_obj.offset(offset_value)
    if limit_value is not None:
        records_obj = records_obj.limit(limit_value)

    return records_obj
