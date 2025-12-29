from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
from dataclasses import dataclass, field
from threading import RLock
from typing import TYPE_CHECKING, Any, Final, NamedTuple, final

from lazy_bear import lazy

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy import func, or_, select
    from sqlalchemy.orm import DeclarativeMeta, Query, QueryableAttribute, Session, scoped_session

    from funcy_bear.tools.names import Names
else:
    Names = lazy("funcy_bear.tools.names", "Names")
    func, or_, select = lazy("sqlalchemy", "func", "or_", "select")


def attr_name(cls: str, attr: str = "data") -> str:
    """Generate a standardized attribute name for storing per-class data.

    Args:
        cls (str): The class name.
        attr (str): The attribute name.

    Returns:
        str: The standardized attribute name.
    """
    return f"_{cls}_{attr}"


def get_name(obj: str | object | type, func: Callable[[str], str] | None = None) -> str:
    """Get the name of a class or return the string if already a string.

    Args:
        obj: The type, object instance, or string to get the name of.
        func: A function to process the name (default is to_snake),
        the default function converts CamelCase to snake_case. This
        allows for consistent/Pythonic naming conventions for attributes or keys.

    Returns:
        str: The name of the class or the string itself.
    """
    if func is None:
        from funcy_bear.ops.strings.manipulation import to_snake  # noqa: PLC0415

        func = to_snake

    if isinstance(obj, str):
        return func(obj)
    if isinstance(obj, type):
        return func(obj.__name__)
    return func(obj.__class__.__name__)


@dataclass(slots=True)
class DynamicRecords[T: DeclarativeMeta]:
    """A simple class to hold records of a specific type."""

    tbl_obj: type[T]
    _session: scoped_session[Session]

    @property
    def session(self) -> Session:
        """Get the current session."""
        return self._session()

    def add(self, instance: T) -> None:
        """Add a new record to the session."""
        self.session.add(instance)

    def add_all(self, instances: Sequence[T]) -> None:
        """Add multiple new records to the session."""
        self.session.add_all(instances)

    def count(self) -> int:
        """Get the number of records of the specified type."""
        return len(self)

    def query(self) -> Query[T]:
        """Query all records of the specified type."""
        return self.session.query(self.tbl_obj)

    def all(self) -> list[T]:
        """Get all records of the specified type."""
        return self.query().all()

    def first(self) -> T | None:
        """Get the first record of the specified type."""
        return self.query().first()

    def scalar(self) -> T | None:
        """Get a single scalar result of the specified type."""
        return self.query().scalar()

    def filter(self, *criteria: Any) -> Query[T]:
        """Filter records by specified criteria.

        Wraps the SQLAlchemy Query.filter method.
        """
        return self.query().filter(*criteria)

    def select_from(self, *entities: Any) -> Query[T]:
        """Select records from specified entities.

        Wraps the SQLAlchemy Query.select_from method.
        """
        return self.query().select_from(*entities)

    def filter_by(self, **kwargs: Any) -> Query[T]:
        """Filter records by specified keyword arguments.

        Wraps the SQLAlchemy Query.filter_by method.
        """
        return self.query().filter_by(**kwargs)

    def order_by(self, *criteria: Any) -> Query[T]:
        """Order records by specified criteria.

        Wraps the SQLAlchemy Query.order_by method.
        """
        return self.query().order_by(*criteria)

    def limit(self, limit_count: int) -> Query[T]:
        """Limit the number of records returned.

        Wraps the SQLAlchemy Query.limit method.
        """
        return self.query().limit(limit_count)

    def offset(self, offset_count: int) -> Query[T]:
        """Offset the number of records returned.

        Wraps the SQLAlchemy Query.offset method.
        """
        return self.query().offset(offset_count)

    def distinct(self) -> Query[T]:
        """Get distinct records.

        Wraps the SQLAlchemy Query.distinct method.
        """
        return self.query().distinct()

    def group_by(self, *criteria: Any) -> Query[T]:
        """Group records by specified criteria.

        Wraps the SQLAlchemy Query.group_by method.
        """
        return self.query().group_by(*criteria)

    def get(self, ident: Any) -> T | None:
        """Get a record by its primary key."""
        return self.session.get(entity=self.tbl_obj, ident=ident)

    def search(self, search: str, *columns: QueryableAttribute, match_any: bool = True) -> Query[T]:
        """Search records by specified columns.

        Args:
            search (str): The search string.
            *columns (QueryableAttribute): The columns to search in.

        Returns:
            Query[T]: The query with the applied search filter.
        """
        if not columns:
            raise ValueError("At least one column must be specified for search.")
        query: Query[T] = self.query()
        search_pattern: str = f"%{search}%"
        filters: list = [column.ilike(search_pattern) for column in columns]
        return query.filter(or_(*filters)) if match_any else query.filter(*filters)

    def update(self, instance: T, **kwargs: Any) -> None:
        """Update a record with specified keyword arguments."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        self.session.add(instance)

    def join(self, target: Any, onclause: Any = None, *, isouter: bool = False, full: bool = False) -> Query[T]:
        """Join with another table.

        Wraps the SQLAlchemy Query.join method.
        """
        return self.query().join(target, onclause=onclause, isouter=isouter, full=full)

    def outerjoin(self, target: Any, onclause: Any = None, full: bool = False) -> Query[T]:
        """Perform an outer join with another table.

        Wraps the SQLAlchemy Query.outerjoin method.
        """
        return self.query().outerjoin(target, onclause=onclause, full=full)

    def having(self, *criteria: Any) -> Query[T]:
        """Apply a HAVING clause to the query.

        Wraps the SQLAlchemy Query.having method.
        """
        return self.query().having(*criteria)

    def exists(self, **criteria: Any) -> bool:
        """Check if a record exists in the database."""
        query: Query[T] = self.query()
        return query.filter_by(**criteria).first() is not None

    def union(self, *queries: Query[T]) -> Query[T]:
        """Perform a UNION operation with other queries.

        Wraps the SQLAlchemy Query.union method.
        """
        query: Query[T] = self.query()
        return query.union(*queries)

    def slice(self, start: int, end: int) -> Query[T]:
        """Slice records from start to end indices.

        Wraps the SQLAlchemy Query.slice method.

        Args:
            start (int): The starting index.
            end (int): The ending index.

        Returns:
            Query[T]: The sliced query.
        """
        if start < 0 or end < 0 or start >= end:
            raise ValueError("Invalid start or end indices for slicing.")
        query: Query[T] = self.query()
        return query.slice(start, end)

    def paginate(self, page: int, per_page: int) -> list[T]:
        """Paginate records of the specified type."""
        if page < 1 or per_page < 1:
            raise ValueError("Page and per_page must be positive integers.")
        query: Query[T] = self.query()
        return query.offset((page - 1) * per_page).limit(per_page).all()

    def pages(self, per_page: int) -> int:
        """Get the total number of pages based on per_page."""
        if per_page < 1:
            raise ValueError("per_page must be a positive integer.")
        total_records: int = len(self)
        return (total_records + per_page - 1) // per_page  # Ceiling division

    def delete(self, instance: T) -> None:
        """Delete a record from the session."""
        self.session.delete(instance)

    def commit(self) -> None:
        """Commit the current transaction."""
        self.session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.session.rollback()

    def refresh(self, instance: T) -> None:
        """Refresh the instance with the latest data from the database."""
        self.session.refresh(instance)

    def remove(self) -> None:
        """Close the session."""
        self._session.remove()

    def __len__(self) -> int:
        """Get the number of records of the specified type."""
        return self.session.scalar(select(func.count()).select_from(self.tbl_obj)) or 0

    def __enter__(self) -> DynamicRecords[T]:
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit the runtime context related to this object."""
        self.remove()

    def __del__(self) -> None:
        """Ensure the session is removed when the object is deleted."""
        self.remove()


class TableHandler[T](NamedTuple):
    """A simple named tuple to hold table handler information."""

    name: str
    table_obj: type[T]
    session: scoped_session[Session]
    records: DynamicRecords

    def remove(self) -> None:
        """Close the session associated with this table handler."""
        self.records.remove()

    def get_session(self) -> scoped_session[Session]:
        """Get the session associated with this table handler."""
        return self.session

    def get_records(self) -> DynamicRecords:
        """Get the records associated with this table handler."""
        return self.records

    def __getattr__(self, item: str) -> Any:
        """Delegate attribute access to the records object."""
        return getattr(self.records, item)


class TableHandlers[T](Names[TableHandler[T]]):
    """A Namespace-like class to hold multiple TableHandler instances."""

    def add_handler(self, k: str, v: TableHandler[T]) -> None:
        """Add a new TableHandler to the collection."""
        self.add(get_name(k), v)

    def get_handler(self, name: str | type) -> TableHandler[T]:
        """Get a table handler by name."""
        returned: TableHandler | None = self.get(get_name(name), strict=False)
        if returned is None:
            if not name:
                raise KeyError("No tables were registered and the name provided is empty.")
            raise KeyError(f"Table handler '{name}' not found.")
        return returned

    def has_handler(self, name: type | str) -> bool:
        """Check if a table handler exists by name."""
        return self.has(get_name(name))

    @property
    def sessions(self) -> list[scoped_session[Session]]:
        """Get all sessions from the table handlers."""
        return [handler.session for handler in self.values()]

    def count(self) -> int:
        """Get the number of table handlers."""
        return len(self._root)

    def clear(self) -> None:
        """Clear all table handlers and close their sessions."""
        self.close()
        self._root.clear()

    def close(self) -> None:
        """Close all table handlers."""
        for handler in self.values():
            handler.remove()

    @property
    def single_table_mode(self) -> bool:
        """Check if there is only one table handler."""
        return len(self._root) == 1

    @property
    def is_empty(self) -> bool:
        """Check if there are no table handlers."""
        return len(self._root) == 0

    @property
    def names(self) -> list[str]:
        """Get all table handler names."""
        return self.keys()


@final
class TableNotSet(str):
    """Sentinel class to indicate that no table is set."""

    def __bool__(self) -> bool:
        return False


NO_TABLE_SET: Final[TableNotSet] = TableNotSet("NO_TABLE_SET")


@dataclass(slots=True)
class PerClassData:
    """Data class to hold per-class database information."""

    base: DeclarativeMeta | None = None
    scoped_sess: scoped_session | None = None
    lock: RLock = field(default_factory=RLock)


class DatabaseManagerMeta(type):
    def __new__(mcs, name: str, bases: tuple, namespace: dict, bypass: bool = True) -> Any:
        if not bases and bypass:
            return super().__new__(mcs, name, bases, namespace)
        container_name: str = attr_name(name)
        namespace[container_name] = PerClassData()
        return super().__new__(mcs, name, bases, namespace)

    @property
    def _name(cls) -> str:
        """Get the name of the class."""
        return cls.__name__

    @property
    def _meta_name(cls) -> str:
        return attr_name(cls.__name__)

    @property
    def _internal(cls) -> PerClassData:
        """Get the internal data attribute name for the class."""
        if not hasattr(cls, cls._meta_name):
            raise AttributeError(f"Class {cls._name} is missing internal data attribute {cls._meta_name}")
        return getattr(cls, cls._meta_name)

    @property
    def _lock(cls) -> RLock:
        """Get the lock for the database manager."""
        return cls._internal.lock

    @property
    def _base(cls) -> DeclarativeMeta | None:
        """Get the base class for the database manager."""
        return cls._internal.base

    def _set_base(cls, value: DeclarativeMeta | None) -> None:
        """Set the base class for the database manager."""
        with cls._internal.lock:
            cls._internal.base = value

    def _get_base(cls) -> DeclarativeMeta:
        """Get the base class for the database manager, creating it if necessary."""
        with cls._internal.lock:
            return cls._base  # type: ignore[return-value]

    @property
    def _scoped_session(cls) -> scoped_session | None:
        """Get the scoped session for the database manager."""
        with cls._internal.lock:
            return cls._internal.scoped_sess

    @_scoped_session.setter
    def _scoped_session(cls, value: scoped_session | None) -> None:
        """Set the scoped session for the database manager."""
        with cls._internal.lock:
            cls._internal.scoped_sess = value
