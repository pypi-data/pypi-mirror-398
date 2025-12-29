"""Smoke tests for BearBase MVP functionality."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from funcy_bear.query import query

if TYPE_CHECKING:
    from bear_shelf.datastore import BearBase


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Create a temporary database file path."""
    return tmp_path / "test.json"


@pytest.fixture
def memory_db() -> BearBase:
    """Create an in-memory database for testing."""
    from bear_shelf.datastore import BearBase

    return BearBase(":memory:")


def test_create_table_and_insert(memory_db: BearBase) -> None:
    """Test creating a table and inserting records."""
    from bear_shelf.datastore import Columns

    memory_db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
            Columns(name="email", type="str", nullable=True),
        ],
    )

    users = memory_db.table("users")
    users.insert(id=1, name="Bear")
    users.insert(id=2, name="Shannon", email="shannon@example.com")

    assert len(users) == 2


def test_insert_dict_style(memory_db: BearBase) -> None:
    """Test inserting with dict syntax."""
    from bear_shelf.datastore import Columns

    memory_db.create_table(
        "posts",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="title", type="str"),
        ],
    )

    posts = memory_db.table("posts")
    posts.insert({"id": 1, "title": "First Post"})

    assert len(posts) == 1


def test_all_records(memory_db: BearBase) -> None:
    """Test retrieving all records."""
    from bear_shelf.datastore import Columns

    memory_db.create_table(
        "items",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    items = memory_db.table("items")
    items.insert(id=1, name="Item 1")
    items.insert(id=2, name="Item 2")
    items.insert(id=3, name="Item 3")

    all_items = items.all()
    assert len(all_items) == 3


def test_get_by_primary_key(memory_db: BearBase) -> None:
    """Test getting a record by primary key."""
    from bear_shelf.datastore import Columns

    memory_db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    users = memory_db.table("users")
    users.insert(id=1, name="Bear")
    users.insert(id=2, name="Shannon")

    bear = users.get(id=1).first()
    assert bear is not None
    assert bear["name"] == "Bear"


def test_search_with_query(memory_db: BearBase) -> None:
    """Test searching with QueryMapping."""
    from bear_shelf.datastore import Columns

    memory_db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
            Columns(name="age", type="int"),
        ],
    )

    users = memory_db.table("users")
    users.insert(id=1, name="Bear", age=30)
    users.insert(id=2, name="Shannon", age=25)
    users.insert(id=3, name="Claude", age=35)

    q = query("mapping")()
    results = users.search(q.age > 28).all()

    assert len(results) == 2
    names = {r["name"] for r in results}
    assert names == {"Bear", "Claude"}


def test_validation_unknown_field(memory_db: BearBase) -> None:
    """Test that unknown fields are rejected."""
    from bear_shelf.datastore import Columns

    memory_db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    users = memory_db.table("users")

    with pytest.raises(ValueError, match="Unknown fields"):
        users.insert(id=1, name="Bear", invalid_field="oops")


def test_validation_missing_required_field(memory_db: BearBase) -> None:
    """Test that missing required fields are rejected."""
    from bear_shelf.datastore import Columns

    memory_db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    users = memory_db.table("users")

    with pytest.raises(ValueError, match="Missing required fields"):
        users.insert(id=1)


def test_insert_without_schema_fails(memory_db: BearBase) -> None:
    """Test that inserting without creating table fails."""
    with pytest.raises(ValueError, match="does not exist"):
        memory_db.table("users")


def test_persistence_json(temp_db_path: Path) -> None:
    """Test that data persists across database instances."""
    from bear_shelf.datastore import BearBase, Columns

    db1: BearBase = BearBase(str(temp_db_path), storage="json")
    db1.create_table(
        name="users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    db1.insert(id=1, name="Bear")
    db1.close()

    db2 = BearBase(str(temp_db_path), storage="json")
    users2 = db2.table("users")
    all_users = users2.all()

    assert len(all_users) == 1
    assert all_users[0]["name"] == "Bear"
    db2.close()


# ruff: noqa: PLC0415
