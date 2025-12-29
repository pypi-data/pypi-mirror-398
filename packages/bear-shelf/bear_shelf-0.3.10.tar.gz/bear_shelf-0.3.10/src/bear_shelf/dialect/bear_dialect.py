"""Bear Shelf SQLAlchemy dialect implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy
from sqlalchemy.engine.default import DefaultDialect

DIALECT = "bearshelf"

if TYPE_CHECKING:
    from collections.abc import MutableMapping, Sequence
    from logging import Logger

    import sqlalchemy
    from sqlalchemy import Table
    from sqlalchemy.engine import Engine
    from sqlalchemy.engine.base import Connection
    from sqlalchemy.engine.interfaces import (
        DBAPIConnection,
        ReflectedColumn,
        ReflectedForeignKeyConstraint,
        ReflectedPrimaryKeyConstraint,
    )
    from sqlalchemy.engine.url import URL
    from sqlalchemy.event import listens_for

    from bear_shelf._logger import get_logger
    from bear_shelf._timer import TimerManager, get_timer
    from bear_shelf.datastore.columns import Columns, ForeignKey
    from bear_shelf.datastore.database import BearBase
    from bear_shelf.datastore.record import Record
    from bear_shelf.datastore.tables.table import Table as BearTable
    from bear_shelf.dialect.compilers import BearDDLCompiler
    from bear_shelf.dialect.cursor import BearCursor
    from bear_shelf.dialect.database_api import BearDBAPI
    from bear_shelf.dialect.executor import DMLExecutor
    from bear_shelf.dialect.helpers import _extract_values as ext
    from funcy_bear.query import QueryInstance
else:
    BearDBAPI = lazy("bear_shelf.dialect.database_api", "BearDBAPI")
    DMLExecutor = lazy("bear_shelf.dialect.executor", "DMLExecutor")
    ext = lazy("bear_shelf.dialect.helpers", "_extract_values")
    BearDDLCompiler = lazy("bear_shelf.dialect.compilers", "BearDDLCompiler")
    sqlalchemy = lazy("sqlalchemy")
    listens_for = lazy("sqlalchemy.event", "listens_for")
    get_logger = lazy("bear_shelf._logger", "get_logger")
    get_timer = lazy("bear_shelf._timer", "get_timer")


class BearShelfDialect(DefaultDialect):
    """SQLAlchemy dialect for Bear Shelf multi-format storage (JSONL, JSON, TOML)."""

    name: str = DIALECT
    driver: str = DIALECT
    supports_alter = False  # TODO: Eventually support ALTER TABLE operations
    supports_pk_autoincrement = True
    supports_default_values = True
    supports_empty_insert = True
    supports_unicode_statements = True
    supports_unicode_binds = True
    supports_native_decimal = True
    supports_native_boolean = True
    supports_statement_cache = True
    supports_is_distinct_from = True
    supports_sane_rowcount = True
    supports_sane_multi_rowcount = True
    supports_simple_order_by_label = True
    has_terminate = True
    default_paramstyle: str = "named"

    def __init__(self, **kwargs) -> None:
        """Initialize the dialect."""
        super().__init__(**kwargs)
        self.ddl_compiler = BearDDLCompiler
        self._db: BearBase | None = None
        self._dbapi: BearDBAPI = kwargs.get("dbapi", self.import_dbapi())
        self._tables: dict[str, Table] = {}
        self._executor: DMLExecutor | None = None

    @classmethod
    def import_dbapi(cls) -> BearDBAPI:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Import the mock DBAPI module."""
        return BearDBAPI()

    @property
    def executor(self) -> DMLExecutor:
        """Get the DML executor."""
        if self._executor is None:
            self._executor = DMLExecutor(self)
        return self._executor

    @property
    def dbapi(self) -> BearDBAPI:
        """Get the DBAPI module."""
        if self._dbapi is None:
            self._dbapi = self.import_dbapi()
        return self._dbapi

    @dbapi.setter
    def dbapi(self, value: BearDBAPI) -> None:
        """Set the DBAPI module."""
        self._dbapi = value

    @property
    def base(self) -> BearBase:
        """Get the BearBase instance."""
        if self._db is None:
            self._db = self.dbapi.base
        return self._db

    @base.setter
    def base(self, value: BearBase) -> None:
        """Set the BearBase instance."""
        self._db = value

    @classmethod
    def engine_created(cls, engine: Engine) -> None:
        """Register any necessary events on the DBAPI connection."""
        logger: Logger = get_logger("bear_dialect")
        timer: TimerManager = get_timer("bear_dialect", logger=logger)

        @listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany) -> None:  # noqa: ARG001
            """Log the start time of query execution."""
            timer.start("cursor_execute")
            logger.debug(f"Start Query: {statement}")

        @listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor: BearCursor, statement, parameters, context, executemany) -> None:  # noqa: ARG001
            """Log the total time taken for query execution."""
            elapsed: float = timer.stop("cursor_execute")
            logger.debug(f"Query Complete! Time taken: {elapsed:.2f}ms")

        @listens_for(sqlalchemy.Table, "before_create")
        def _bear_before_create(table: Table, connection, **_) -> None:
            """Handle table creation via DDL events."""
            if connection.dialect.name == DIALECT:
                dialect: BearShelfDialect = connection.dialect  # pyright: ignore[reportAssignmentType]
                dialect._create_storage_file(table, connection)
                logger.debug(f"Created storage for table '{table.name}'.")

        @listens_for(sqlalchemy.Table, "before_drop")
        def _bear_before_drop(table: Table, connection, **_) -> None:
            """Handle table drop via DDL events."""
            if connection.dialect.name == DIALECT:
                dialect: BearShelfDialect = connection.dialect  # pyright: ignore[reportAssignmentType]
                dialect._drop_storage_file(table, connection)
                logger.debug(f"Dropped storage for table '{table.name}'.")

    def create_connect_args(self, url: URL) -> tuple[Sequence[str], MutableMapping[str, Any]]:
        """Parse the database URL to get the file path and infer storage type from extension.

        URL format: bearshelf:///path/to/file.{ext}
        Example: bearshelf:///./database.jsonl   (uses JSONL storage)
                 bearshelf:///./database.xml     (uses XML storage)
                 bearshelf:///./database.toml    (uses TOML storage)
        """
        from bear_shelf.dialect.common import DatabasePathInfo, DBPathReturn, get_database_path_from_url

        db_info: DatabasePathInfo = get_database_path_from_url(url)
        return DBPathReturn(path=[db_info.path], opts={"storage": db_info.storage})

    def do_rollback(self, dbapi_connection) -> None:
        """Handle rollback - calls to a no-op on the DBAPI connection."""
        dbapi_connection.rollback()

    def do_commit(self, dbapi_connection) -> None:
        """Handle commit - write changes to storage file."""
        dbapi_connection.commit()

    def do_executemany(self, cursor: BearCursor, statement, parameters, context: Any = None) -> Any:  # type: ignore[override]
        """Execute many statements (for bulk operations)."""
        return self.do_execute(cursor, statement, parameters, context)

    def do_execute(  # type: ignore[override]
        self,
        cursor: BearCursor,
        statement: Any,
        parameters: Any,
        context: Any = None,
    ) -> Any:
        """Execute a statement - DDL handled by events, SELECT handled here."""
        if isinstance(statement, str) and statement.startswith("/* bearshelf:"):
            return cursor
        return self.executor.do_execute(
            cursor,
            statement,
            parameters,
            context,
            self._tables,
        )

    def do_terminate(self, dbapi_connection: DBAPIConnection) -> None:
        """Terminate the DBAPI connection."""
        self.do_close(dbapi_connection)

    def do_close(self, dbapi_connection: DBAPIConnection) -> None:
        """Close the DBAPI connection."""
        dbapi_connection.close()

    def _get_records(
        self,
        tbl: BearTable,
        order_by_info: list[tuple[str, bool]],
        where_clause: QueryInstance | None = None,
    ) -> list[Record]:
        """Retrieve records from the table applying WHERE and ORDER BY clauses."""
        if order_by_info:
            name, is_desc = order_by_info[0]  # Only apply the first ORDER BY clause for now
            if where_clause is None:
                return tbl.all(list_recs=False).order_by(name, desc=is_desc).all()
            return tbl.search(where_clause).order_by(name, desc=is_desc).all()
        return tbl.search(where_clause).all() if where_clause is not None else tbl.all()

    def _create_storage_file(self, table: Table, connection: Connection) -> None:
        """Create table in BearBase from SQLAlchemy Table."""
        table_name = str(table.name)
        self._tables[table_name] = table
        columns: list[Columns] = ext.get_columns(table)
        try:
            if self.not_name_in_table(table_name):
                self.base.create_table(table_name, columns=columns, save=True, enable_wal=self.base.enable_wal)
        except Exception as e:
            raise RuntimeError(f"Failed to create table '{table_name}' in storage.") from e

    def _drop_storage_file(self, table: Table, connection: Connection) -> None:
        """Drop table from BearBase."""
        table_name = str(table.name)
        if self.name_in_table(table_name):
            self.base.drop_table(table_name)
            self._tables.pop(table_name, None)

    def not_name_in_table(self, name: str) -> bool:
        """Check if a table name does NOT exist in the database."""
        return not self.name_in_table(name)

    def name_in_table(self, name: str) -> bool:
        """Check if a table name exists in the database."""
        return name in self.base.tables()

    def get_table(self, table_name: str) -> Table | None:
        """Get the SQLAlchemy Table object for a given table name."""
        return self._tables.get(table_name)

    def get_table_names(self, connection: Connection, schema: str | None = None, **kw: Any) -> list[str]:
        """Return a list of table names in the database."""
        return list(self.base.tables())

    def get_ddl(self, connection: Connection, table_name: str, schema: str | None = None, **kw: Any) -> str:
        """Return the DDL statement for creating the table."""
        if not self.has_table(connection, table_name):
            raise ValueError(f"Table '{table_name}' does not exist in the database.")
        table: BearTable = self.base.table(table_name)
        cols: str = ", ".join([f"{col.name} {col.type}" for col in table.get_columns()])
        return f"CREATE TABLE {table_name} ({cols})"

    def get_columns(
        self,
        connection: Connection,
        table_name: str,
        schema: str | None = None,
        **kw: Any,
    ) -> list[ReflectedColumn]:
        """Return column information for the given table.

        Returns:
            A list of dictionaries, each representing a column with keys:
            - name: column name
            - type: column type
            - nullable: whether the column is nullable
            - default: default value for the column (if any)
            - autoincrement
        """
        if not self.has_table(connection, table_name):
            return []

        columns_info: list[ReflectedColumn] = []
        for column in self.base.table(table_name).get_columns():
            col_info: ReflectedColumn = {
                "name": column.name,
                "type": ext.map_from_sqlalchemy_type(column.type),
                "nullable": column.nullable,
                "default": column.default,
                "autoincrement": column.autoincrement or False,
            }
            columns_info.append(col_info)
        return columns_info

    def has_table(self, connection: Connection, table_name: str, schema=None, **kw) -> bool:
        """Check if a table exists."""
        return table_name in self.base.tables()

    def get_fk_constraint(
        self,
        connection: Connection,
        table_name: str,
        fk_name: str,
        schema: str | None = None,
        **kw: Any,
    ) -> ReflectedForeignKeyConstraint | None:
        """Return foreign key constraint information for the given foreign key name.

        Returns a dictionary with the following keys:
        - name: constraint name
        - constrained_columns: list of local column names
        - referred_table: name of the referenced table
        - referred_columns: list of referenced column names
        - options: dict of additional options (optional)
        """
        if not self.has_table(connection, table_name):
            return None

        for fk in self.get_foreign_keys(connection, table_name):
            if fk.get("name") == fk_name:
                return fk
        return None

    def get_pk_constraint(
        self,
        connection: Connection,
        table_name: str,
        schema: str | None = None,
        **kw: Any,
    ) -> ReflectedPrimaryKeyConstraint:
        """Return primary key constraint information for the table.

        Returns a dictionary with the following keys:
        - constrained_columns: list of column names that make up the primary key
        - name: name of the primary key constraint (optional)
        """
        if not self.has_table(connection, table_name):
            return {"constrained_columns": [], "name": None}

        pk_columns: list[str] = []
        for column in self.base.table(table_name).get_columns():
            if column.primary_key:
                pk_columns.append(column.name)

        return {"constrained_columns": pk_columns, "name": None}

    def get_foreign_keys(
        self,
        connection: Connection,
        table_name: str,
        schema: str | None = None,
        **kw: Any,
    ) -> list[ReflectedForeignKeyConstraint]:
        """Return foreign key constraint information for the table.

        Returns a list of dictionaries, each representing a foreign key constraint:
        - name: constraint name (optional)
        - constrained_columns: list of local column names
        - referred_table: name of the referenced table
        - referred_columns: list of referenced column names
        - options: dict of additional options (optional)
        """
        from bear_shelf.dialect.common import FKInfo

        if not self.has_table(connection, table_name):
            return []

        foreign_keys: list[ReflectedForeignKeyConstraint] = []

        for column in self.base.table(table_name).get_columns():
            if column.foreign_key is not None:
                fk: ForeignKey = column.split_foreign_key
                if not fk.is_notset:
                    fk_info = FKInfo(
                        constrained_columns=[column.name],
                        referred_table=fk.table,
                        referred_columns=[fk.column],
                    )
                    foreign_keys.append(fk_info.output(exclude={"comment"}))
        return foreign_keys


# For Reference but keep this commented out:
# from sqlalchemy.dialects import registry
# registry.register(APP_CONFIG.info.dialect, APP_CONFIG.info.module_path, APP_CONFIG.info.class_name)

# ruff: noqa: ARG002 ANN001 PLC0415
