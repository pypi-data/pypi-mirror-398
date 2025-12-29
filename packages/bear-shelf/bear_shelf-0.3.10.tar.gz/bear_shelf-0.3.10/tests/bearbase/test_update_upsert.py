"""Tests for update() and upsert() operations in BearBase."""

from pathlib import Path

import pytest

from bear_shelf.datastore import BearBase
from bear_shelf.datastore.columns import Columns
from bear_shelf.datastore.record import Record, Records
from bear_shelf.datastore.tables.table import Table
from funcy_bear.api import increment
from funcy_bear.query import query
from funcy_bear.query.query_mapping import where


def test_table_update_with_dict(tmp_path: Path):
    """Test updating records with a dictionary of fields."""
    db = BearBase(file=tmp_path / "test.json", storage="json")
    db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
            Columns(name="status", type="str"),
        ],
    )

    table: Table = db.table("users")
    table.insert(id=1, name="Bear", status="active")
    table.insert(id=2, name="Claude", status="active")
    table.insert(id=3, name="Shannon", status="inactive")

    # Update all active users
    q = query("mapping")()
    updated_count: int = table.update({"status": "online"}, cond=q.status == "active")

    assert updated_count == 2

    results: list[Record] = table.all()
    assert results[0]["status"] == "online"
    assert results[1]["status"] == "online"
    assert results[2]["status"] == "inactive"

    db.close()


def test_table_update_with_kwargs(tmp_path: Path):
    """Test updating records with keyword arguments."""
    with BearBase(file=tmp_path / "test.json", storage="json") as db:
        db.create_table(
            "products",
            columns=[
                Columns(name="id", type="int", primary_key=True),
                Columns(name="name", type="str"),
                Columns(name="price", type="float"),
                Columns(name="in_stock", type="bool"),
            ],
        )

        table = db.table("products")
        table.insert(id=1, name="Widget", price=9.99, in_stock=True)
        table.insert(id=2, name="Gadget", price=19.99, in_stock=True)

        # Update using kwargs
        q = query("mapping")()
        updated_count = table.update(price=14.99, in_stock=False, cond=q.id == 2)

        assert updated_count == 1

        product = table.get(id=2).first()
        assert product is not None
        assert product["price"] == 14.99
        assert product["in_stock"] is False


def test_table_update_with_callable(tmp_path: Path):
    """Test that callable updates are not supported and raise TypeError."""
    with BearBase(file=tmp_path / "test.json", storage="json") as db:
        db.create_table(
            "counters",
            columns=[
                Columns(name="name", type="str", primary_key=True),
                Columns(name="count", type="int"),
            ],
        )

        table = db.table("counters")
        table.insert(name="views", count=10)
        table.insert(name="likes", count=5)

        q = query("mapping")()
        # Callable updates should raise TypeError
        with pytest.raises(TypeError, match="Update fields must be a dict"):
            table.update(increment("count"), cond=q.name == "views")


def test_table_update_all_records(tmp_path: Path):
    """Test updating all records when no condition is provided."""
    db: BearBase = BearBase(file=tmp_path / "test.json", storage="json")
    db.create_table(
        "items",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="archived", type="bool"),
        ],
    )

    table: Table = db.table("items")
    table.insert(id=1, archived=False)
    table.insert(id=2, archived=False)
    table.insert(id=3, archived=False)

    # Update all without condition
    updated_count = table.update({"archived": True})

    assert updated_count == 3
    assert all(rec["archived"] for rec in table.all(list_recs=True))

    db.close()


def test_table_update_no_matches(tmp_path: Path) -> None:
    """Test updating when no records match the condition."""
    with BearBase(file=tmp_path / "test.json", storage="json") as db:
        db.create_table(
            "data",
            columns=[
                Columns(name="id", type="int", primary_key=True),
                Columns(name="value", type="str"),
            ],
        )

        table = db.table("data")
        table.insert(id=1, value="foo")

        q = query("mapping")()
        updated_count: int = table.update({"value": "bar"}, cond=q.id == 999)
        assert updated_count == 0
        assert table.get(id=1).first()["value"] == "foo"  # Unchanged


def test_table_upsert_insert_new(tmp_path: Path):
    """Test upsert inserting a new record when none exists."""
    with BearBase(file=tmp_path / "test.json", storage="json") as db:
        db.create_table(
            "settings",
            columns=[
                Columns(name="key", type="str", primary_key=True),
                Columns(name="value", type="str"),
            ],
        )

        table = db.table("settings")
        q = query("mapping")()

        # Upsert new record
        table.upsert({"key": "theme", "value": "dark"}, cond=q.key == "theme")

        assert len(table.all()) == 1
        assert table.get(key="theme").first()["value"] == "dark"


def test_table_upsert_update_existing(tmp_path: Path) -> None:
    """Test upsert updating an existing record."""
    with BearBase(file=tmp_path / "test.json", storage="json") as db:
        db.create_table(
            "settings",
            columns=[
                Columns(name="key", type="str", primary_key=True),
                Columns(name="value", type="str"),
            ],
        )

        table = db.table("settings")
        q = query("mapping")()

        # Insert initial record
        table.insert(key="theme", value="light")

        # Upsert should update
        table.upsert({"key": "theme", "value": "dark"}, cond=q.key == "theme")

        assert len(table.all()) == 1  # Still only one record
        assert table.get(key="theme").first()["value"] == "dark"  # Updated


def test_table_upsert_with_kwargs(tmp_path: Path):
    """Test upsert using keyword arguments."""
    with BearBase(file=tmp_path / "test.json", storage="json") as db:
        db.create_table(
            "config",
            columns=[
                Columns(name="key", type="str", primary_key=True),
                Columns(name="value", type="int"),
            ],
        )

        table: Table = db.table("config")
        q = query("mapping")()

        # Upsert with kwargs
        table.upsert(key="max_users", value=100, cond=q.key == "max_users")
        assert table.get(key="max_users").first()["value"] == 100

        # Upsert again to update
        table.upsert(key="max_users", value=200, cond=q.key == "max_users")
        assert table.get(key="max_users").first()["value"] == 200


def test_database_update(tmp_path: Path):
    """Test update() at the database level (delegates to default table)."""
    with BearBase(file=tmp_path / "test.json", storage="json") as db:
        db.create_table(
            "default",
            columns=[
                Columns(name="id", type="int", primary_key=True),
                Columns(name="status", type="str"),
            ],
        )
        table = db.table("default")
        table.insert({"id": 1, "status": "pending"})
        table.insert({"id": 2, "status": "pending"})

        q = query("mapping")()
        updated: int = table.update(status="complete", cond=q.id == 1)

        assert updated == 1
        assert table.get(q.id == 1).first()["status"] == "complete"
        assert table.get(q.id == 2).first()["status"] == "pending"


def test_database_upsert(tmp_path: Path):
    """Test upsert() at the database level."""
    with BearBase(file=tmp_path / "test.json", storage="json") as db:
        db.create_table(
            "default",
            columns=[
                Columns(name="id", type="int", primary_key=True),
                Columns(name="name", type="str"),
            ],
        )

        q = query("mapping")()

        db.upsert({"id": 1, "name": "Bear"}, cond=q.id == 1)
        record = db.get(q.id == 1).first()["name"] == "Bear"

        # Upsert update
        db.upsert({"id": 1, "name": "Bear Dereth"}, cond=q.id == 1)
        assert db.get(q.id == 1).first()["name"] == "Bear Dereth"
        assert len(db.all()) == 1  # Still one record


def test_update_callable_with_complex_logic(tmp_path: Path) -> None:
    """Test that callable updates with complex logic raise TypeError."""
    with BearBase(file=tmp_path / "test.json", storage="json") as db:
        db.create_table(
            "posts",
            columns=[
                Columns(name="id", type="int", primary_key=True),
                Columns(name="title", type="str"),
                Columns(name="views", type="int"),
                Columns(name="likes", type="int"),
            ],
        )

        table: Table = db.table("posts")
        table.insert(id=1, title="Hello", views=10, likes=2)
        table.insert(id=2, title="World", views=50, likes=10)

        def boost_popular(rec: Record) -> None:
            if rec["views"] > 20:
                rec["likes"] = rec["likes"] * 2
                rec["title"] = f"⭐ {rec['title']}"

        q = query("mapping")()
        # Callable updates should raise TypeError
        with pytest.raises(TypeError, match="Callable updates are not supported"):
            table.update(boost_popular, cond=q.views > 20)  # pyright: ignore[reportArgumentType]


def test_update_persistence(tmp_path: Path):
    """Test that updates persist across database instances."""
    db_file: Path = tmp_path / "persist.json"
    q = query("mapping")()

    with BearBase(file=db_file, storage="json") as db1:
        db1.create_table(
            "data",
            columns=[
                Columns(name="id", type="int", primary_key=True),
                Columns(name="value", type="str"),
            ],
        )
        db1.insert({"id": 1, "value": "initial"})
        db1.update(value="updated", cond=q.id == 1)

    with BearBase(file=db_file, storage="json", current_table="data") as db2:
        record: Record = db2.get(cond=where("id") == 1).first()
        assert record is not None
        assert record["value"] == "updated"


def test_upsert_persistence(tmp_path: Path):
    """Test that upserts persist correctly."""
    db_file = tmp_path / "persist.json"

    q = query("mapping")()

    with BearBase(file=db_file, storage="json") as db1:
        db1.create_table(
            "config",
            columns=[
                Columns(name="key", type="str", primary_key=True),
                Columns(name="value", type="str"),
            ],
        )
        db1.upsert({"key": "setting", "value": "v1"}, cond=q.key == "setting")

    with BearBase(file=db_file, storage="json", current_table="config") as db2:
        db2.upsert({"key": "setting", "value": "v2"}, cond=q.key == "setting")

    with BearBase(file=db_file, storage="json", current_table="config") as db3:
        record: Records = db3.get(cond=where("key") == "setting")
        assert record is not None
        assert record.first()["value"] == "v2"
        record = db3.table("config").get(key="setting")
        assert record is not None
        assert record.first()["value"] == "v2"


def test_update_clears_cache(tmp_path: Path):
    """Test that update operations clear the query cache."""
    with BearBase(file=tmp_path / "test.json", storage="json") as db:
        db.create_table(
            "items",
            columns=[
                Columns(name="id", type="int", primary_key=True),
                Columns(name="active", type="bool"),
            ],
        )

        table = db.table("items")
        table.insert(id=1, active=True)
        table.insert(id=2, active=False)

        q = query("mapping")()

        # Cache a query
        initial_results: Records = table.search(q.active == True)
        assert len(initial_results) == 1

        # Update should clear cache
        table.update(active=True, cond=q.id == 2)

        # Query again should get fresh results
        updated_results: Records = table.search(q.active == True)
        assert len(updated_results) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# ruff: noqa: E712
