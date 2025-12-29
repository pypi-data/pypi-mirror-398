"""Bear Shelf dialect database API module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NoReturn

from lazy_bear import lazy

from bear_shelf.datastore import BearBase

if TYPE_CHECKING:
    from bear_shelf.config import StorageChoices
    from bear_shelf.dialect.cursor import BearCursor
else:
    BearCursor = lazy("bear_shelf.dialect.cursor", "BearCursor")


WAL_CONFIG_FIELDS: set[str] = {
    "flush_mode",
    "flush_interval",
    "flush_batch_size",
    "auto_checkpoint",
    "checkpoint_threshold",
}


class StandardError(Exception):
    """Standard error class for Bear Shelf dialect."""


class BearConnection:
    """Helper class to handle a connection to a Bear Shelf database."""

    def __init__(self, database_path: str, base: BearBase) -> None:
        """Initialize the connection."""
        self.database_path: str = database_path
        self.base: BearBase = base
        self.closed = False

    def close(self) -> None:
        """Close the connection."""
        self.base.close()
        self.closed = True

    def commit(self) -> None:
        """Commit changes - handled by dialect's do_commit."""
        self.base.commit()

    def cursor(self, *args: Any, **kwargs: Any) -> BearCursor:  # pyright: ignore[reportIncompatibleMethodOverride] # noqa: ARG002
        """Return a cursor object."""
        return BearCursor()

    def rollback(self) -> None:
        """Rollback changes - not implemented."""
        # TODO: Implement rollback support
        # We might be able to do this via WAL that BearBase supports
        # since we can just clear uncommitted changes from the WAL
        # and memory cache, but for now, we do nothing.

    def __getattr__(self, item: Any) -> NoReturn:
        raise AttributeError(f"BearConnection has no attribute '{item}'")

    def __setattr__(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)


class BearDBAPI:
    """DBAPI module for bear-shelf dialect."""

    enable_wal: bool
    _base: BearBase
    paramstyle: str = "named"
    params: dict[str, Any]
    Error: Any = StandardError

    def connect(self, database_path: str, storage: StorageChoices, **kwargs) -> BearConnection:
        """Connect to the database."""
        self.params = {
            "enable_wal": kwargs.pop("enable_wal", False),
            **{k: v for k, v in kwargs.items() if k in WAL_CONFIG_FIELDS},
        }
        self.enable_wal = self.params["enable_wal"]
        self.base = BearBase(file=database_path, storage=storage, **self.params)
        existing_tables: set[str] = self.base.tables()
        if existing_tables:
            self.base.set_table(next(iter(existing_tables)))
        return BearConnection(database_path, self.base)

    @property
    def base(self) -> BearBase:
        """Get the BearBase instance."""
        return self._base

    @base.setter
    def base(self, value: BearBase) -> None:
        """Set the BearBase instance."""
        self._base: BearBase = value

    def __getattr__(self, item: Any) -> NoReturn:
        raise AttributeError(f"BearDBAPI has no attribute '{item}'")

    def __repr__(self) -> str:
        if self.base is not None:
            return (
                f"<BearDBAPI enable_wal={self.enable_wal}, flush_mode={self.flush_mode}, storage={self.base.storage}>"
            )
        return "<BearDBAPI uninitialized>"
