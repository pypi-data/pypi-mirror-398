from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

from sqlalchemy.sql import operators

from funcy_bear.api import any_of
from funcy_bear.ops.value_stuffs import equal_value
from funcy_bear.tools import Dispatcher

if TYPE_CHECKING:
    from funcy_bear.query import QueryInstance


t = Dispatcher("op")


@t.dispatcher()
def translate_op(op: Any, query_path: Any, value: Any) -> QueryInstance:
    """Default operator translator."""
    raise NotImplementedError(f"Operator {op} not supported yet")


@t.register(any_of(partial(equal_value, value=operators.eq), partial(equal_value, value=operators.is_)))
def _equality_op(op: Any, query_path: Any, value: Any) -> Any:
    """Translate equality operator."""
    return query_path == value


@t.register(partial(equal_value, value=operators.ne))
def _inequality_op(op: Any, query_path: Any, value: Any) -> Any:
    """Translate inequality operator."""
    return query_path != value


@t.register(partial(equal_value, value=operators.gt))
def _greater_than_op(op: Any, query_path: Any, value: Any) -> Any:
    """Translate greater than operator."""
    return query_path > value


@t.register(partial(equal_value, value=operators.lt))
def _less_than_op(op: Any, query_path: Any, value: Any) -> Any:
    """Translate less than operator."""
    return query_path < value


@t.register(partial(equal_value, value=operators.ge))
def _greater_equal_op(op: Any, query_path: Any, value: Any) -> Any:
    """Translate greater than or equal operator."""
    return query_path >= value


@t.register(partial(equal_value, value=operators.le))
def _less_equal_op(op: Any, query_path: Any, value: Any) -> Any:
    """Translate less than or equal operator."""
    return query_path <= value


@t.register(partial(equal_value, value=operators.is_not))
def _is_not_op(op: Any, query_path: Any, value: Any) -> Any:
    """Translate IS NOT operator."""
    return query_path != value


@t.register(partial(equal_value, value=operators.like_op))
def _like_op(op: Any, query_path: Any, value: Any) -> Any:
    """Translate LIKE operator."""
    if not isinstance(value, str):
        raise TypeError(f"LIKE pattern must be a string, got {type(value)}")
    return query_path.matches(sql_like_to_regex(value))


@t.register(partial(equal_value, value=operators.notlike_op))
def _not_like_op(op: Any, query_path: Any, value: Any) -> Any:
    """Translate NOT LIKE operator."""
    if not isinstance(value, str):
        raise TypeError(f"NOT LIKE pattern must be a string, got {type(value)}")
    return ~query_path.matches(sql_like_to_regex(value))


# ruff: noqa: ARG001 PLC0415


def sql_like_to_regex(pattern: str) -> str:
    """Convert SQL LIKE pattern to regex.

    SQL LIKE wildcards:
    - % matches any sequence of characters (including empty)
    - _ matches exactly one character

    Args:
        pattern: SQL LIKE pattern (e.g., 'B%', '%ear', 'B_ar')

    Returns:
        Regex pattern string with anchors

    Examples:
        'B%' -> '^B.*$'       (starts with B)
        '%ear' -> '^.*ear$'   (ends with ear)
        '%ear%' -> '^.*ear.*$' (contains ear)
        'B_ar' -> '^B.ar$'    (B, any char, ar)
    """
    import re

    pattern = pattern.replace("%", "\x00PERCENT\x00")
    pattern = pattern.replace("_", "\x00UNDERSCORE\x00")
    pattern = re.escape(pattern)
    pattern = pattern.replace("\x00PERCENT\x00", ".*")  # % -> .*
    pattern = pattern.replace("\x00UNDERSCORE\x00", ".")  # _ -> .
    return f"^{pattern}$"  # Add anchors for exact match behavior
