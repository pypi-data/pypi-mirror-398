"""A single record in a table, represented as a dictionary with string keys and any type of values."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NoReturn, Self

from lazy_bear import lazy
from pydantic import PrivateAttr, RootModel

if TYPE_CHECKING:
    from collections.abc import Iterator

    from frozen_cub.frozen import FrozenDict, freeze

    from funcy_bear.constants.type_constants import NoReturnCall
    from funcy_bear.query import QueryProtocol
else:
    FrozenDict, freeze = lazy("frozen_cub.frozen", "FrozenDict", "freeze")


class Record(RootModel[dict[str, Any]]):
    """A single record in a table."""

    _is_record_instance: bool = PrivateAttr(default=True)

    def __init__(self, root: dict[str, Any] | None = None, /, **kwargs: Any) -> None:
        """Create a Record from a dict or kwargs."""
        if root is None and kwargs:
            root = kwargs
        elif root is None:
            root = {}
        super().__init__(root)

    def items(self) -> list[tuple[str, Any]]:
        """Return items for the record."""
        if self.is_null:
            return []
        return list(self.root.items())

    def keys(self) -> list[str]:
        """Return keys for the record."""
        if self.is_null:
            return []
        return list(self.root.keys())

    def values(self) -> list[Any]:
        """Return values for the record."""
        if self.is_null:
            return []
        return list(self.root.values())

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Override model_dump to ensure a dict is always returned."""
        if self.is_null:
            return {}
        return super().model_dump(*args, **kwargs) or {}

    def frozen_dump(self) -> FrozenDict:
        """Return a frozen representation of the record."""
        if self.is_null:
            return FrozenDict(())
        return freeze(self.model_dump(exclude_none=True))

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the record with a default."""
        return self.root.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the record."""
        if self.is_null:
            return
        self.root[key] = value

    def has(self, key: str) -> bool:
        """Check if the record has a key."""
        return key in self.root

    def update(self, other: dict[str, Any]) -> None:
        """Update the record with another dictionary."""
        if self.is_null:
            return
        self.root.update(other)

    def add(self, key: str, value: Any) -> None:
        """Add a new key-value pair to the record."""
        if self.is_null:
            return
        self.root[key] = value

    @property
    def count(self) -> int:
        """Count the number of key values in the record."""
        return len(self.root) if not self.is_null else 0

    @property
    def is_null(self) -> bool:
        """Check if the record has a key named "null" with value True."""
        return self.root.get("null") is True

    def __call__(self, data: Any) -> Self:
        """Update the record with new data and return self."""
        if self.is_null:
            return self
        self.update(data)
        return self

    def __getattr__(self, item: str) -> Any:
        return self.root.get(item)

    def __setattr__(self, key: str, value: Any) -> None:
        if self.is_null:
            return
        if key == "root":
            super().__setattr__(key, value)
        else:
            self.root[key] = value

    def __getitem__(self, item: str) -> Any:
        return self.root[item]

    def __setitem__(self, key: str, value: Any) -> None:
        if key == "null":
            return
        self.root[key] = value

    def __delitem__(self, key: str) -> None:
        if key == "null":
            return
        del self.root[key]

    def __contains__(self, item: str) -> bool:
        if self.is_null:
            return False
        return item in self.root

    def __len__(self) -> int:
        if self.is_null:
            return 0
        return len(self.root)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Record):
            if self.is_null and other.is_null:
                return True
            return self.root == other.root
        if isinstance(other, dict):
            return self.root == other
        return False

    def __ne__(self, other: object) -> bool:
        return other != self

    def __hash__(self) -> int:
        if self.is_null:
            return hash("NullRecord")
        return hash(freeze(self.root))

    def __bool__(self) -> bool:
        return bool(self.root) and not self.is_null

    def __repr__(self) -> str:
        if self.is_null:
            return "Record(root={})"
        return f"Record(root={self.root})"

    def __str__(self) -> str:
        return self.__repr__()


NullRecord = Record(root=freeze({"null": True}))


class Records(RootModel[tuple[Record, ...]]):
    """A list of records."""

    def __init__(self, root: Any = None, /, **kwargs: Any) -> None:
        """Create a Records from a list or tuple of Record, or from a single Record using the 'record' keyword argument.

        Args:
            root: A list, tuple, Records, or Record instance.
            record: (optional) A single Record instance to initialize the Records.
        """
        values: list = []
        record = kwargs.pop("record", None)
        if root is None and record is not None:
            values = [record]
        if root is not None:
            if isinstance(root, Record):
                values = [root]
            elif isinstance(root, (list | tuple)):
                values = list(root)
            elif isinstance(root, Records):
                values = list(root.root)
        frozen_values = freeze(values)
        super().__init__(frozen_values)

    def _immutable(self, *_, **__) -> NoReturn:
        """Disable any method that would modify the records."""
        raise TypeError("Records is immutable")

    @classmethod
    def from_list(cls, r: list[Record] | Record) -> Records:
        """Create a Records instance from a list of Record or a single Record."""
        return cls(root=freeze(r))

    @classmethod
    def from_self(cls, r: tuple[Record, ...]) -> Records:
        """Create a Records instance from a tuple of Record."""
        return cls(root=freeze(r))

    def all(self) -> list[Record]:
        """Return all records."""
        return list(self.root) or []

    def one(self) -> Record:
        """Return exactly one record or raise an error."""
        if not self.root:
            raise ValueError("No records found.")
        if self.count > 1:
            raise ValueError(f"Expected exactly one record, found {self.count}.")
        return next(iter(self.root))

    def first(self) -> Record:
        """Return the first record or None if empty."""
        return self.root[0] if self.root else NullRecord

    def last(self) -> Record:
        """Return the last record or None if empty."""
        return self.root[-1] if self.root else NullRecord

    def filter_by(self, func: QueryProtocol) -> Records:
        """Filter records by a function."""
        return Records([rec for rec in self.root if func(rec)])

    def limit(self, n: int) -> Records:
        """Limit the number of records returned."""
        return Records(self.root[:n])

    def offset(self, n: int) -> Records:
        """Offset the records by n."""
        return Records(self.root[n:])

    def order_by(self, *keys: str, desc: bool = False) -> Records:
        """Order records by a key.

        Args:
            *keys: Keys to sort by, in order of priority
            desc: If True, sort in descending order

        Returns:
            New Records instance with sorted records

        Note:
            None values are always sorted last (or first if desc=True)
        """

        def sort_key(record: Record) -> tuple[Any, ...]:
            result: list = []
            for key in keys:
                value: Any = record.get(key)
                is_none: bool = value is None
                if desc:
                    result.append((0, value) if is_none else (1, value))
                else:
                    result.append((1, value) if is_none else (0, value))
            return tuple(result)

        return Records(sorted(self.root, key=sort_key, reverse=desc))

    @property
    def count(self) -> int:
        """Return the count of records."""
        return len(self.root) if self.root else 0

    def record_count(self) -> int:
        """Return the count of records."""
        return self.count

    @property
    def is_null(self) -> bool:
        """Check if the records list is empty or contains only a NullRecord."""
        return not self.root or (len(self.root) == 1 and self.root[0].is_null)

    def model_dump(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        """Override model_dump to ensure a list of dicts is always returned."""
        if self.is_null:
            return []
        return [rec.model_dump(*args, **kwargs) for rec in self.root] or []

    def distinct(self, key: str | None = None) -> Records:
        """Return records with duplicates removed.

        Args:
            key: Optional field name to check for distinctness.
                If None, checks entire record.

        Returns:
            New Records with duplicates removed.
        """
        if key:
            seen: set[Any] = set()
            unique: list[Record] = []
            for rec in self.root:
                value: Any = rec.get(key)
                if value not in seen:
                    seen.add(value)
                    unique.append(rec)
            return Records(unique)
        return Records(list(dict.fromkeys(self.root)))

    # def __bool__(self) -> bool:
    #     return not self.is_null and bool(self.root)

    def __getattr__(self, item: str) -> Any:
        if self.is_null or not self.root:
            return NullRecord
        return self.root[0].get(key=item, default=NullRecord)

    def __getitem__(self, item: Any) -> Record:
        if self.is_null or not self.root:
            return NullRecord
        return self.root[item]

    def __len__(self) -> int:
        if self.is_null:
            return 0
        return len(self.root)

    def __hash__(self) -> int:
        if self.is_null:
            return hash("NullRecords")
        return hash(freeze(self.root))

    def __repr__(self) -> str:
        """String representation for debugging."""
        if self.is_null:
            return "Records([])"
        return f"Records({list(self.root)})"

    def __iter__(self) -> Iterator[Record]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Iterate over individual records, not model fields."""
        return iter(self.root)

    __setattr__: NoReturnCall = _immutable
    __setitem__: NoReturnCall = _immutable
    __delitem__: NoReturnCall = _immutable


NullRecords = Records(root=freeze([NullRecord]))


__all__ = ["NullRecord", "NullRecords", "Record", "Records"]
