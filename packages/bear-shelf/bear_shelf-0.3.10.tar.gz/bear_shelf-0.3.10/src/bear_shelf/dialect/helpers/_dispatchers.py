from __future__ import annotations

from functools import partial
from typing import Any

from bear_shelf.dialect import protocols as pro
from funcy_bear.sentinels import CONTINUE
from funcy_bear.tools import Dispatcher
from funcy_bear.type_stuffs.validate import is_instance_of

col = Dispatcher("value")
params = Dispatcher("value")


@col.dispatcher()
def value_check(value: Any) -> Any:
    """Default value checker."""
    return value


@col.register(partial(is_instance_of, types=pro.ColumnWithKey))
def column_value_check(value: pro.ColumnWithKey) -> Any:
    """Extract value from ColumnWithKey."""
    return value.key


@col.register(partial(is_instance_of, types=pro.ColumnWithName))
def column_name_value_check(value: pro.ColumnWithName) -> Any:
    """Extract name from ColumnWithName."""
    return value.name


@params.dispatcher()
def params_check(value: Any, key: Any, updates: dict[str, Any]) -> Any:  # noqa: ARG001
    """Default params checker."""
    return CONTINUE


@params.register(partial(is_instance_of, types=pro.BindParameterWithEffectiveValue))
def bind_effective_value_check(value: pro.BindParameterWithEffectiveValue, key: str, updates: dict[str, Any]) -> Any:
    """Extract effective value from BindParameterWithEffectiveValue."""
    updates[key] = value.effective_value


@params.register(partial(is_instance_of, types=pro.BindParameterWithValue))
def bind_value_check(value: pro.BindParameterWithValue, key: str, updates: dict[str, Any]) -> Any:
    """Extract value from BindParameterWithValue."""
    updates[key] = value.value
