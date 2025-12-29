"""Tests for refactored DatabaseManager table API."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any, NamedTuple

import pytest
from sqlalchemy.orm import DeclarativeMeta, Mapped, declarative_base, mapped_column

from bear_shelf.database import BearShelfDB
from bear_shelf.database._extra import TableHandler, TableHandlers
from bear_shelf.database.config import DatabaseConfig


class TableReturn(NamedTuple):
    """Return type for fresh_db_class fixture."""

    db: type[BearShelfDB]
    base: DeclarativeMeta


@pytest.fixture
def fresh_db_class() -> Generator[TableReturn, Any]:
    """Create a fresh DatabaseManager subclass for each test to avoid metadata conflicts."""

    class TestDB(BearShelfDB): ...

    base: DeclarativeMeta = declarative_base()
    TestDB.set_base(base)
    try:
        yield TableReturn(db=TestDB, base=base)
    finally:
        TestDB.clear_base()


def test_create_tables_returns_handlers(tmp_path: Path, fresh_db_class: TableReturn) -> None:
    """Test that create_tables() returns TableHandlers."""
    fresh: TableReturn = fresh_db_class
    db_path: Path = tmp_path / "test.toml"

    class User(fresh.base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

    config = DatabaseConfig(scheme="bearshelf", path=str(db_path))
    db = fresh.db(database_config=config)

    tables: TableHandlers = db.create_tables()

    assert isinstance(tables, TableHandlers)
    assert "user" in tables


def test_tables_accessor_methods(tmp_path: Path, fresh_db_class: TableReturn) -> None:
    """Test table(), tables(), and table_names() methods."""
    fresh: TableReturn = fresh_db_class
    db_path: Path = tmp_path / "test.toml"

    class User(fresh.base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

    class Post(fresh.base):
        __tablename__ = "posts"
        id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str] = mapped_column()

    config = DatabaseConfig(scheme="bearshelf", path=str(db_path))
    db = fresh.db(database_config=config, tables_create=True, records={"user": User, "post": Post})

    names: list[str] = db.table_names()
    assert "user" in names
    assert "post" in names
    assert len(names) == 2

    all_tables: TableHandlers = db.tables()
    assert isinstance(all_tables, TableHandlers)
    assert len(all_tables) == 2

    user_handler: TableHandler = db.table("user")
    assert isinstance(user_handler, TableHandler)
    assert user_handler.name == "user"


def test_single_table_auto_resolution(tmp_path: Path, fresh_db_class: TableReturn) -> None:
    """Test that single-table databases auto-resolve current table."""
    fresh: TableReturn = fresh_db_class
    db_path: Path = tmp_path / "test.toml"

    class User(fresh.base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

    config = DatabaseConfig(scheme="bearshelf", path=str(db_path))
    db = fresh.db(database_config=config, records={"user": User})
    db.create_tables()

    count: int = db.count()
    assert count == 0

    all_users: list[Any] = db.get_all()
    assert all_users == []


def test_multi_table_requires_explicit_table(tmp_path: Path, fresh_db_class: TableReturn) -> None:
    """Test that multi-table databases require explicit table argument."""
    fresh: TableReturn = fresh_db_class
    db_path: Path = tmp_path / "test.toml"

    class User(fresh.base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

    class Post(fresh.base):
        __tablename__ = "posts"
        id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str] = mapped_column()

    config = DatabaseConfig(scheme="bearshelf", path=str(db_path))
    db = fresh.db(database_config=config)
    db.create_tables()

    with pytest.raises(ValueError, match="Database has 2 tables"):
        db.count()

    user_count: int = db.count(User)
    assert user_count == 0

    post_count: int = db.count(Post)
    assert post_count == 0


def test_set_table_and_get_current_table(tmp_path: Path, fresh_db_class: TableReturn) -> None:
    """Test set_table() and get_current_table() methods."""
    fresh: TableReturn = fresh_db_class
    db_path = tmp_path / "test.toml"

    class User(fresh.base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

    class Post(fresh.base):
        __tablename__ = "posts"
        id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str] = mapped_column()

    config = DatabaseConfig(scheme="bearshelf", path=str(db_path))
    db = fresh.db(database_config=config)
    db.create_tables()

    db.set_table(User)

    current = db.get_current_table()
    assert current == User

    count: int = db.count()
    assert count == 0

    db.set_table(Post)
    current = db.get_current_table()
    assert current == Post


def test_table_handlers_attribute_access(tmp_path: Path, fresh_db_class: TableReturn) -> None:
    """Test TableHandlers can be accessed via attributes."""
    fresh: TableReturn = fresh_db_class
    db_path: Path = tmp_path / "test.toml"

    class User(fresh.base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

    config = DatabaseConfig(scheme="bearshelf", path=str(db_path))
    db = fresh.db(database_config=config)
    tables: TableHandlers = db.create_tables()

    user: TableHandler = tables.user
    assert isinstance(user, TableHandler)
    assert user.name == "user"

    user_dict = tables["user"]
    assert user_dict == user


def test_table_handlers_operations(tmp_path: Path, fresh_db_class: TableReturn) -> None:
    """Test that TableHandlers allow direct operations on records."""
    fresh: TableReturn = fresh_db_class
    db_path: Path = tmp_path / "test.toml"

    class User(fresh.base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

    config = DatabaseConfig(scheme="bearshelf", path=str(db_path))
    db = fresh.db(database_config=config)
    tables: TableHandlers = db.create_tables()

    with db.open_session() as session:
        user = User(id=1, name="Bear")
        session.add(user)

    all_users = tables.user.records.all()
    assert len(all_users) == 1
    assert all_users[0].name == "Bear"


def test_resolve_table_error_message_no_tables(tmp_path: Path, fresh_db_class: TableReturn) -> None:
    """Test error message when no tables registered."""
    fresh: TableReturn = fresh_db_class
    db_path: Path = tmp_path / "test.toml"

    config = DatabaseConfig(scheme="bearshelf", path=str(db_path))
    db = fresh.db(database_config=config)

    with pytest.raises(ValueError, match="No tables have been registered yet"):
        db.count()


def test_create_tables_single_table_sets_current(tmp_path: Path, fresh_db_class: TableReturn) -> None:
    """Test that create_tables() auto-sets current table for single-table DB."""
    fresh: TableReturn = fresh_db_class
    db_path: Path = tmp_path / "test.toml"

    class User(fresh.base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

    config = DatabaseConfig(scheme="bearshelf", path=str(db_path))
    db = fresh.db(database_config=config)
    db.create_tables()

    current = db.get_current_table()
    assert current == User


def test_set_table_requires_registration(tmp_path: Path, fresh_db_class: TableReturn) -> None:
    """Test that set_table() requires table to be registered first."""
    fresh: TableReturn = fresh_db_class
    db_path: Path = tmp_path / "test.toml"

    class User(fresh.base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

    config = DatabaseConfig(scheme="bearshelf", path=str(db_path))
    db = fresh.db(database_config=config)

    assert not db.is_registered(User)

    with pytest.raises(ValueError, match="No tables have been registered yet"):
        db.set_table(User)


def test_open_session_works_without_current_table(tmp_path: Path, fresh_db_class: TableReturn) -> None:
    """Test that open_session() works even without current table set."""
    fresh: TableReturn = fresh_db_class
    db_path: Path = tmp_path / "test.toml"

    class User(fresh.base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

    config = DatabaseConfig(scheme="bearshelf", path=str(db_path))
    db = fresh.db(database_config=config)
    db.create_tables()

    with db.open_session() as session:
        user = User(id=1, name="Bear")
        session.add(user)

    all_users = db.get_all(User)
    assert len(all_users) == 1
    assert all_users[0].name == "Bear"


def test_context_manager_closes_properly(tmp_path: Path, fresh_db_class: TableReturn) -> None:
    """Test that context manager __enter__/__exit__ closes database."""
    fresh: TableReturn = fresh_db_class
    db_path: Path = tmp_path / "test.toml"

    class User(fresh.base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

    config = DatabaseConfig(scheme="bearshelf", path=str(db_path))
    db = fresh.db(database_config=config)

    with db as context_db:
        tables: TableHandlers = context_db.create_tables()
        assert "user" in tables

    assert db.instance_session is None


def test_long_lived_sessions_not_removed(tmp_path: Path, fresh_db_class: TableReturn) -> None:
    """Test that long_lived=True keeps sessions alive after open_session()."""
    fresh: TableReturn = fresh_db_class
    db_path: Path = tmp_path / "test.toml"

    class User(fresh.base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

    config = DatabaseConfig(scheme="bearshelf", path=str(db_path))
    db = fresh.db(database_config=config, long_lived=True)
    db.create_tables()

    with db.open_session() as session:
        user = User(id=1, name="Bear")
        session.add(user)

    session_handler = db.table("user").session
    assert session_handler is not None
