"""Database Manager Module for managing database connections and operations."""

from __future__ import annotations

import atexit
from contextlib import contextmanager
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar, Literal, overload

from lazy_bear import lazy
from sqlalchemy.orm import DeclarativeMeta, Query, declarative_base, scoped_session, sessionmaker

from .config import DatabaseConfig, Schemas, get_default_config

if TYPE_CHECKING:
    from collections.abc import Generator
    from threading import RLock

    from sqlalchemy import Engine, MetaData, create_engine
    from sqlalchemy.orm.mapper import Mapper
    from sqlalchemy.orm.session import Session

    from bear_shelf.database._extra import (
        NO_TABLE_SET,
        DatabaseManagerMeta,
        DynamicRecords,
        TableHandler,
        TableHandlers,
        get_name,
    )
else:
    Engine, MetaData, create_engine = lazy("sqlalchemy", "Engine", "MetaData", "create_engine")
    NO_TABLE_SET, DatabaseManagerMeta, DynamicRecords, TableHandler, TableHandlers, get_name = lazy(
        "bear_shelf.database._extra",
        "NO_TABLE_SET",
        "DatabaseManagerMeta",
        "DynamicRecords",
        "TableHandler",
        "TableHandlers",
        "get_name",
    )


class DatabaseManager[T_Table: DeclarativeMeta](metaclass=DatabaseManagerMeta, bypass=False):
    """A class to manage database connections and operations."""

    _scheme: ClassVar[Schemas] = "sqlite"
    config_factory: partial[DatabaseConfig]
    engine_factory: partial[Engine]

    @classmethod
    def set_base(cls, base: DeclarativeMeta | None) -> None:
        """Set the base class for this database class."""
        cls._set_base(base)

    @classmethod
    def get_base(cls) -> DeclarativeMeta:
        """Get the base class for this database class."""
        if cls._base is None:
            cls._set_base(declarative_base())
        return cls._get_base()

    @classmethod
    def clear_base(cls) -> None:
        """Clear the base class for this database class."""
        cls._set_base(None)

    @classmethod
    def set_scheme(cls, scheme: Schemas) -> None:
        """Set the default scheme for the database manager."""
        cls._scheme = scheme

    def __init__(self, **kwargs) -> None:
        """Initialize the DatabaseManager with a database URL or connection parameters.

        Args:
            database_config (DatabaseConfig | None): The database configuration object.
            host (str): The database host.
            port (int): The database port.
            user (str): The database username.
            password (str | SecretStr): The database password.
            name (str): The database name.
            path (str | None): The database file path (for SQLite).
            schema (Schemas | None): The database schema/type (e.g., 'sqlite', 'postgresql', 'mysql').
            auto: (bool): Whether to automatically create the engine and tables.
            long_lived (bool): Whether to use a long-lived connection/session.
            enable_wal (bool): Whether to enable Write-Ahead Logging (WAL) for SQLite databases.
            flush_mode (WALFlushMode): The WAL flush mode.
            engine_create (bool): Whether to create the engine immediately.
            tables_create (bool): Whether to create tables on initialization.
            echo: (bool): Whether to enable SQLAlchemy echo for debugging.
            records (dict[str, type[T_Table]] | None): An optional dictionary of pre-registered dynamic records.
        """
        self._metadata: MetaData = self.get_base().metadata
        self.long_lived: bool = kwargs.pop("long_lived", False)

        self._handlers: TableHandlers[T_Table] = TableHandlers()
        self._current_table: str = NO_TABLE_SET

        self._config: DatabaseConfig | None = None
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None

        self._on_init(
            config=kwargs.pop("database_config", None),
            schema=kwargs.pop("schema", None),
            auto=kwargs.pop("auto", False),
            engine_create=kwargs.pop("engine_create", False),
            tables_create=kwargs.pop("tables_create", False),
            records=kwargs.pop("records", {}),
            **kwargs,
        )

    def _on_init(
        self,
        records: dict[str, type[T_Table]] | None = None,
        config: DatabaseConfig | None = None,
        schema: Schemas | None = None,
        auto: bool = False,
        engine_create: bool = False,
        tables_create: bool = False,
        echo: bool = False,
        **kwargs,
    ) -> None:
        """Hook method called after initialization.

        Args:
            records: Optional dictionary of pre-registered dynamic records.
            config: Optional database configuration.
            schema: Database type (sqlite, postgresql, mysql, bearshelf).
            auto: If True, creates engine and tables immediately.
            engine_create: If True, creates engine immediately.
            tables_create: If True, creates tables immediately.
            **kwargs: Connection parameters.
        """
        if auto:
            engine_create = True
            tables_create = True

        self.config_factory = partial(
            get_default_config,
            schema=schema or self._scheme,
            user=kwargs.pop("user", None),
            password=kwargs.pop("password", None),
            host=kwargs.pop("host", None),
            port=kwargs.pop("port", None),
            name=kwargs.pop("name", None),
            path=kwargs.pop("path", None),
        )

        if config is not None:
            self._config = config

        self.engine_factory: partial[Engine] = partial(
            create_engine,
            self.config.db_url.get_secret_value(),
            echo=echo,
            connect_args={**kwargs},
        )

        if engine_create:
            self._engine = self.engine_factory()

        if records:
            for _, rec_cls in records.items():
                self.register_record(rec_cls)

        if tables_create:
            self.create_tables()

        atexit.register(self.close)

    def create_tables(self) -> TableHandlers:
        """Create all tables and return handles for working with them.

        Single-table: returns handlers, auto-sets current table.
        Multi-table: returns handlers, use them or pass table explicitly.

        Returns:
            TableHandlers: Access via .tablename or ['tablename']

        Examples:
            tables = db.create_tables()
            tables.users.all()
            tables['posts'].filter_by(status='published').all()
        """
        self._metadata.create_all(self.engine, checkfirst=True)

        for table_cls in self.get_orm_tables().values():
            if not self.is_registered(table_cls):
                self.register_record(table_cls)

        if self._handlers.single_table_mode:
            self._current_table = next(iter(self._handlers.names))
        return self._handlers

    def register_records(self, *tbl_objs: type[T_Table]) -> Generator[DynamicRecords[T_Table]]:
        """Register multiple table classes for dynamic record access.

        Args:
            *tbl_objs: The table classes to register.
        """
        for tbl_obj in tbl_objs:
            yield self.register_record(tbl_obj)

    def register_record(self, tbl_obj: Any) -> DynamicRecords[T_Table]:
        """Register a table class for dynamic record access.

        Args:
            name (str): The name to register the table class under.
            tbl_obj (type[T]): The table class to register.

        Returns:
            DynamicRecords[T]: An instance of DynamicRecords for the table class.
        """
        name: str = get_name(tbl_obj)
        if self._handlers.has(name):
            raise ValueError(f"Table '{name}' is already registered.")

        session: scoped_session[Session] = self.get_session(scoped=True)
        records: DynamicRecords[T_Table] = DynamicRecords(tbl_obj, session)
        tbl_handler: TableHandler[T_Table] = TableHandler(
            name=name.lower(), table_obj=tbl_obj, session=session, records=records
        )
        self._handlers.add_handler(name, tbl_handler)
        return records

    def _resolve_table(self, table: type[T_Table] | None) -> type[T_Table]:
        """Resolve table class for operations.

        Single-table: table arg optional, uses current table.
        Multi-table: table arg required, or raises clear error.
        """
        if table is not None:
            return table

        if not self._registered:
            raise ValueError("No tables have been registered yet.")

        if self._current_table != NO_TABLE_SET:
            return self._handlers.get_handler(self._current_table).table_obj

        if self._handlers.single_table_mode:
            self._current_table = next(iter(self._handlers.names))
            return self._handlers.get_handler(self._current_table).table_obj

        available: list[str] = list(self._handlers.keys())
        raise ValueError(
            f"Database has {len(available)} tables: {available}. "
            f"Pass table explicitly or use handles: tables = db.create_tables()"
        )

    def is_registered(self, table: type[T_Table] | str) -> bool:
        """Check if a table class is registered.

        Args:
            table (type | str): The table class to check.

        Returns:
            bool: True if the table class is registered, False otherwise.
        """
        return self._registered and self._handlers.has_handler(table)

    def get_records(self, table: type[T_Table] | str) -> DynamicRecords[T_Table]:
        """Get the DynamicRecords instance for a registered table class.

        Args:
            table (type[T_Table] | str): The table class to get records for.

        Returns:
            DynamicRecords[T_Table]: The DynamicRecords instance for the table class.
        """
        if not self._registered:
            raise ValueError("No tables have been registered yet.")
        if not self.is_registered(table):
            raise ValueError(f"Table '{table}' is not registered.")
        return self._handlers.get_handler(table).get_records()

    def set_table(self, table: type[T_Table] | str) -> None:
        """Set the current table for operations."""
        name: str = get_name(table)
        if not self._registered:
            raise ValueError("No tables have been registered yet.")
        if not self.is_registered(table):
            raise ValueError(f"Table '{table}' is not registered.")
        self._current_table = name

    def get_current_table(self) -> type[T_Table]:
        """Get the current table class."""
        if not self._registered or self._current_table == NO_TABLE_SET:
            raise ValueError("No table is currently selected, ensure tables are created.")
        return self._handlers.get_handler(self._current_table).table_obj

    def get_all(self, table: type[T_Table] | None = None) -> list[T_Table]:
        """Get all records from a table.

        Args:
            table: Table class (optional for single-table databases).
        """
        table = self._resolve_table(table)
        return self.get_records(table).all()

    def get(self, table: type[T_Table] | None = None, ident: Any | None = None) -> T_Table | None:
        """Get a record by its primary key.

        Args:
            table: Table class (optional for single-table databases).
            ident: Primary key value.
        """
        table = self._resolve_table(table)
        return self.get_records(table).get(ident)

    def count(self, table: type[T_Table] | None = None, **kwargs) -> int:
        """Count records in a table.

        Args:
            table: Table class (optional for single-table databases).
            **kwargs: Optional filters to apply when counting.
        """
        table = self._resolve_table(table)
        records: DynamicRecords[T_Table] = self.get_records(table)
        return records.count() if not kwargs else records.filter_by(**kwargs).count()

    def query(self, table: type[T_Table] | None = None) -> Query[T_Table]:
        """Get a query object for a table.

        Args:
            table: Table class (optional for single-table databases).
        """
        table = self._resolve_table(table)
        return self.get_records(table).query()

    def filter_by(self, table: type[T_Table] | None = None, **kwargs) -> Query[T_Table]:
        """Filter records by column values.

        Args:
            table: Table class (optional for single-table databases).
            **kwargs: Column filters.
        """
        table = self._resolve_table(table)
        return self.get_records(table).filter_by(**kwargs)

    @overload
    def get_session(self, scoped: Literal[True]) -> scoped_session: ...

    @overload
    def get_session(self, scoped: Literal[False] = False) -> Session: ...

    def get_session(self, scoped: bool = False) -> scoped_session | Session:
        """Get the scoped session for this database class.

        Args:
            scoped (bool): Whether to return a scoped session or a regular session.

        Returns:
            scoped_session | Session: The scoped session or regular session.
        """
        if self.instance_session is None:
            self.instance_session = scoped_session(self.session_factory)
        return self.instance_session if scoped else self.instance_session()

    @contextmanager
    def open_session(self, remove: bool = False) -> Generator[Session, Any]:
        """Provide a transactional scope around a series of operations.

        Will commit the session if no exceptions occur, otherwise will rollback.

        Args:
            remove (bool): Whether to remove the session after use. Will
            override long_lived attribute if set to True.

        Yields:
            Generator[Session, Any]: A SQLAlchemy Session instance.
        """
        session: scoped_session[Session] = self.get_session(scoped=True)
        session_obj: Session = session()
        try:
            yield session_obj
            session_obj.commit()
        except Exception:
            session_obj.rollback()
            raise
        finally:
            if not self.long_lived or remove:
                session.remove()

    def table(self, name: str) -> TableHandler:
        """Get the TableHandler for a registered table by name.

        Args:
            name (str): The name of the registered table.

        Returns:
            TableHandler: The TableHandler for the specified table.
        """
        return self._handlers.get_handler(name)

    def tables(self) -> TableHandlers:
        """Get all registered TableHandlers.

        Returns:
            TableHandlers: All registered TableHandlers.
        """
        return self._handlers

    def table_names(self) -> list[str]:
        """Get the names of all registered tables.

        Returns:
            list[str]: A list of registered table names.
        """
        return list(self._handlers.keys())

    def get_table_objs(self) -> dict[str, Any]:
        """Get the Table objects defined in the metadata.

        Generally you shouldn't need to use this directly
        but it can be helpful for debugging.
        """
        return self._metadata.tables

    def get_orm_tables(self) -> dict[str, type[T_Table]]:
        """Get the ORM table classes defined in the base.

        Can be useful for introspection and debugging.
        """
        base: DeclarativeMeta = self.get_base()
        mappers: frozenset[Mapper[Any]] = base.registry.mappers
        return {get_name(mapper.class_): mapper.class_ for mapper in mappers}

    def close_session(self) -> None:
        """Close the scoped session for this database class.

        This will remove the session and set it to None.
        """
        if self.instance_session is not None:
            self.instance_session.remove()
        self.instance_session = None

    def close_handlers(self) -> None:
        """Close all table handlers."""
        self._handlers.close()

    def close(self) -> None:
        """Close the session and connection."""
        self.close_session()
        self.close_handlers()
        if self._session_factory is not None:
            self._session_factory = None
        if self.engine is not None:
            self.engine.dispose()
            self._engine = None

    @property
    def closed(self) -> bool:
        """Check if the database manager is closed."""
        return self._engine is None and self._session_factory is None

    @property
    def config(self) -> DatabaseConfig:
        """Get the database configuration."""
        if self._config is None:
            self._config = self.config_factory()
        return self._config

    @property
    def engine(self) -> Engine:
        """Get the SQLAlchemy Engine."""
        if self._engine is None:
            self._engine = self.engine_factory()
        return self._engine

    @property
    def session_factory(self) -> sessionmaker[Session]:
        """Get the session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory

    @property
    def session(self) -> scoped_session[Session]:
        """Get the scoped session for this database class."""
        return self._handlers.get_handler(self._current_table).session

    @property
    def instance_session(self) -> scoped_session | None:
        """Get the scoped session for this database class."""
        return self.__class__._scoped_session

    @instance_session.setter
    def instance_session(self, value: scoped_session | None) -> None:
        self.__class__._scoped_session = value

    @property
    def lock(self) -> RLock:
        """Get the lock for the database manager."""
        return self.__class__._lock

    @property
    def _registered(self) -> bool:
        """Check if any tables have been registered."""
        return not self._handlers.is_empty

    def __enter__(self) -> DatabaseManager[T_Table]:
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit the runtime context related to this object."""
        self.close()

    def __del__(self) -> None:
        """Ensure the database manager is closed when the object is deleted."""
        self.close()


class SqliteDB[T: DeclarativeMeta](DatabaseManager[T]):
    """SQLite Database Manager, inherits from DatabaseManager and sets the scheme to sqlite."""

    _scheme: ClassVar[Schemas] = "sqlite"


class PostgresDB[T: DeclarativeMeta](DatabaseManager[T]):
    """Postgres Database Manager, inherits from DatabaseManager and sets the scheme to postgresql."""

    _scheme: ClassVar[Schemas] = "postgresql"


class MySQLDB[T: DeclarativeMeta](DatabaseManager[T]):
    """MySQL Database Manager, inherits from DatabaseManager and sets the scheme to mysql."""

    _scheme: ClassVar[Schemas] = "mysql"


class BearShelfDB[T: DeclarativeMeta](DatabaseManager[T]):
    """BearShelf Database Manager, inherits from DatabaseManager and sets the scheme to bearshelf.

    BearShelf uses file-based storage with multiple format options (JSONL, JSON, YAML, XML, TOML).
    The format is determined by the file extension in the database path/name.
    """

    _scheme: ClassVar[Schemas] = "bearshelf"


__all__ = ["BearShelfDB", "DatabaseManager", "MySQLDB", "PostgresDB", "SqliteDB"]
