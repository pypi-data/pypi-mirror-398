from collections.abc import Callable
from functools import cached_property
from typing import Any, Final, Literal, NamedTuple, overload

from pydantic import BaseModel

from bear_shelf.datastore.common import FKAction
from funcy_bear.tools import FrozenDict

INVALID_NAME_PREFIXES: list[str] = ["xml"]

type IntLiteral = Literal["int", "integer"]
NOTSET_SENTINEL = ...

class ForeignKey(NamedTuple):
    table: str
    column: str

    @property
    def is_notset(self) -> bool: ...

NOTSET_TUPLE: Final[ForeignKey] = ...

class Columns[T](BaseModel):
    name: str = ...
    type: str = ...
    unique: bool | None = None
    comment: str | None = None
    foreign_key: str | None = None
    ondelete: FKAction | None = None
    onupdate: FKAction | None = None
    default: T | None = None
    default_factory: Callable[..., T] | None = None
    nullable: bool = False
    primary_key: bool | None = None
    autoincrement: bool | None = None

    @overload
    def __init__(
        self,
        name: str,
        type: IntLiteral = ...,
        default: int | None = ...,
        unique: bool | None = ...,
        comment: str | None = ...,
        *,
        nullable: Literal[False] = ...,
        primary_key: Literal[True],
        autoincrement: Literal[True],
    ) -> None: ...
    @overload
    def __init__(
        self,
        name: str,
        type: IntLiteral = ...,
        unique: bool | None = ...,
        comment: str | None = ...,
        *,
        default_factory: Callable[..., int],
        nullable: Literal[False] = ...,
        primary_key: Literal[True],
        autoincrement: Literal[True],
    ) -> None: ...
    @overload
    def __init__(
        self,
        name: str,
        type: IntLiteral = ...,
        default: int | None = ...,
        unique: bool | None = ...,
        comment: str | None = ...,
        *,
        nullable: bool = False,
        primary_key: bool | None = None,
        autoincrement: Literal[False] | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        name: str,
        type: IntLiteral = ...,
        unique: bool | None = ...,
        comment: str | None = ...,
        *,
        default_factory: Callable[..., int],
        nullable: bool = False,
        primary_key: bool | None = None,
        autoincrement: Literal[False] | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        name: str,
        type: str = ...,
        unique: bool | None = ...,
        comment: str | None = ...,
        *,
        nullable: bool = False,
        primary_key: bool | None = None,
        autoincrement: Literal[False] | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        name: str,
        type: str = ...,
        default: T | None = None,
        unique: bool | None = ...,
        comment: str | None = ...,
        *,
        nullable: bool = False,
        primary_key: bool | None = None,
        autoincrement: Literal[False] | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        name: str,
        type: str = ...,
        unique: bool | None = ...,
        comment: str | None = ...,
        *,
        default_factory: Callable[..., T],
        nullable: bool = False,
        primary_key: bool | None = None,
        autoincrement: Literal[False] | None = None,
    ) -> None: ...
    def __init__(
        self,
        name: str,
        type: str = ...,
        unique: bool | None = ...,
        comment: str | None = ...,
        default: T | None = None,
        default_factory: Callable[..., T] | None = None,
        nullable: bool = False,
        primary_key: bool | None = None,
        autoincrement: bool | None = None,
    ) -> None: ...
    @classmethod
    def create(
        cls,
        name: str,
        type: str,
        unique: bool | None = None,
        comment: str | None = None,
        foreign_key: str | None = None,
        default: T | None = None,
        default_factory: Callable[..., T] | None = None,
        nullable: bool = False,
        primary_key: bool | None = None,
        autoincrement: bool | None = None,
        ondelete: FKAction | None = None,
        onupdate: FKAction | None = None,
    ) -> Columns[T]: ...
    @cached_property
    def split_foreign_key(self) -> ForeignKey: ...
    @property
    def fk_table(self) -> str: ...
    @property
    def fk_column(self) -> str: ...
    @cached_property
    def type_obj(self) -> type[T]: ...
    @classmethod
    def validate_name(cls, v: Any) -> str: ...
    @classmethod
    def validate_type(cls, v: Any) -> str: ...
    def validate_column_constraints(self) -> Columns: ...
    @property
    def is_int(self) -> bool: ...
    def get_default(self) -> T | None: ...
    def __hash__(self) -> int: ...
    def frozen_dump(self) -> FrozenDict: ...
    def render(self) -> dict[str, Any]: ...
    def items(self) -> list[tuple[str, Any]]: ...
    @classmethod
    def fields(cls) -> list[str]: ...

NullColumn: Columns[None] = ...

# ruff: noqa: A002
