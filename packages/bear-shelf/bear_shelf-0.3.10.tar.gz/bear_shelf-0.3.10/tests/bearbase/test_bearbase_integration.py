"""Integration tests for BearBase - testing full workflows."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from bear_shelf.datastore.record import Records
from bear_shelf.datastore.tables.table import Table
from funcy_bear.query import QueryInstance, QueryMapping, query as query_mapping

if TYPE_CHECKING:
    from bear_shelf.datastore import BearBase


@pytest.fixture
def query() -> QueryMapping:
    """Get a QueryMapping instance for tests."""
    return query_mapping("mapping")()


@pytest.fixture
def blog_db(tmp_path: Path) -> BearBase:
    """Create a blog database with multiple related tables."""
    from bear_shelf.datastore import BearBase, Columns

    db_path: Path = tmp_path / "blog.json"
    db: BearBase = BearBase(str(db_path), storage="json")

    db.create_table(
        "authors",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
            Columns(name="email", type="str"),
        ],
    )

    db.create_table(
        "posts",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="author_id", type="int"),
            Columns(name="title", type="str"),
            Columns(name="content", type="str"),
            Columns(name="published", type="bool"),
        ],
    )

    db.create_table(
        "comments",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="post_id", type="int"),
            Columns(name="author_name", type="str"),
            Columns(name="text", type="str"),
        ],
    )

    return db


def test_full_blog_workflow(blog_db: BearBase) -> None:
    """Test a complete blog workflow: create authors, posts, comments, query."""
    authors: Table = blog_db.table("authors")
    posts: Table = blog_db.table("posts")
    comments: Table = blog_db.table("comments")

    authors.insert(id=1, name="Bear", email="bear@example.com")
    authors.insert(id=2, name="Shannon", email="shannon@example.com")

    assert len(authors) == 2

    posts.insert(
        id=1,
        author_id=1,
        title="Getting Started with BearBase",
        content="BearBase is a document database...",
        published=True,
    )
    posts.insert(
        id=2,
        author_id=1,
        title="Advanced Queries",
        content="Learn how to use QueryMapping...",
        published=False,
    )
    posts.insert(
        id=3,
        author_id=2,
        title="AI in Terminals",
        content="Warp terminal and AI assistance...",
        published=True,
    )

    assert len(posts) == 3

    comments.insert(
        id=1,
        post_id=1,
        author_name="Claude",
        text="Great introduction!",
    )
    comments.insert(
        id=2,
        post_id=1,
        author_name="Shannon",
        text="Very helpful, thanks!",
    )
    comments.insert(
        id=3,
        post_id=3,
        author_name="Bear",
        text="Love this topic!",
    )

    assert len(comments) == 3


def test_complex_queries(blog_db: BearBase, query: QueryMapping) -> None:
    """Test complex query operations."""
    authors: Table = blog_db.table("authors")
    posts: Table = blog_db.table("posts")

    authors.insert(id=1, name="Bear", email="bear@example.com")
    authors.insert(id=2, name="Shannon", email="shannon@example.com")

    posts.insert(id=1, author_id=1, title="Post 1", content="Content 1", published=True)
    posts.insert(id=2, author_id=1, title="Post 2", content="Content 2", published=False)
    posts.insert(id=3, author_id=2, title="Post 3", content="Content 3", published=True)
    posts.insert(id=4, author_id=2, title="Post 4", content="Content 4", published=False)

    published_posts: Records = posts.search(query.published == True)
    assert len(published_posts) == 2

    bear_posts: Records = posts.search(query.author_id == 1)
    assert len(bear_posts) == 2

    bear_published: Records = posts.search((query.author_id == 1) & (query.published == True))
    assert len(bear_published) == 1
    assert bear_published[0]["title"] == "Post 1"


def test_multiple_tables_persistence(tmp_path: Path) -> None:
    """Test that multiple tables persist correctly."""
    db_path: Path = tmp_path / "multi.json"
    from bear_shelf.datastore import BearBase, Columns

    with BearBase(str(db_path), storage="json") as db1:
        db1.create_table(
            name="users",
            columns=[
                Columns(name="id", type="int", primary_key=True),
                Columns(name="name", type="str"),
            ],
        )
        db1.create_table(
            "posts",
            columns=[
                Columns(name="id", type="int", primary_key=True),
                Columns(name="title", type="str"),
            ],
        )

        users = db1.table("users")
        posts = db1.table("posts")

        users.insert({"id": 1, "name": "Bear"})
        posts.insert({"id": 1, "title": "First Post"})

    with BearBase(str(db_path), storage="json") as db2:
        tables: set[str] = db2.tables()
        assert "users" in tables
        assert "posts" in tables
        users: Table = db2.table("users")
        posts: Table = db2.table("posts")
        assert len(users) == 1
        assert len(posts) == 1


def test_get_operations(blog_db: BearBase, query: QueryMapping) -> None:
    """Test various get operations."""
    from bear_shelf.datastore.record import NullRecords, Record

    authors: Table = blog_db.table("authors")

    authors.insert(id=1, name="Bear", email="bear@example.com")
    authors.insert(id=2, name="Shannon", email="shannon@example.com")
    authors.insert(id=3, name="Claude", email="claude@example.com")

    bear: Record = authors.get(id=1).first()
    assert bear is not None
    assert bear["name"] == "Bear"
    assert bear["email"] == "bear@example.com"

    shannon: Record = authors.get(cond=query.name == "Shannon").first()
    assert shannon is not None
    assert shannon["id"] == 2

    nonexistent: Records = authors.get(id=999)
    assert nonexistent is NullRecords


def test_multiple_storage_backends(tmp_path: Path) -> None:
    """Test that same data works across different storage backends."""
    from bear_shelf.datastore import BearBase, Columns
    from bear_shelf.datastore.record import Record

    data_to_insert: list[dict[str, Any]] = [
        {"id": 1, "name": "Bear"},
        {"id": 2, "name": "Shannon"},
        {"id": 3, "name": "Claude"},
    ]

    for storage_type in ["json", "toml"]:
        db_path: Path = tmp_path / f"test.{storage_type}"
        db: BearBase = BearBase(str(db_path), storage=storage_type)

        db.create_table(
            "users",
            columns=[
                Columns(name="id", type="int", primary_key=True),
                Columns(name="name", type="str"),
            ],
        )

        users: Table = db.table("users")
        for record in data_to_insert:
            users.insert(**record)

        assert len(users) == 3
        all_users: list[Record] = users.all(list_recs=True)
        assert {u["name"] for u in all_users} == {"Bear", "Shannon", "Claude"}
        db.close()


def test_caching_behavior(blog_db: BearBase, query: QueryMapping) -> None:
    """Test that query caching works correctly."""
    posts: Table = blog_db.table("posts")

    for i in range(10):
        posts.insert(
            id=i,
            author_id=1,
            title=f"Post {i}",
            content=f"Content {i}",
            published=i % 2 == 0,
        )

    published_query: QueryInstance = query.published == True

    results1: Records = posts.search(published_query)
    results2: Records = posts.search(published_query)

    assert len(results1) == 5
    assert len(results2) == 5

    assert results1 == results2

    posts.insert(id=100, author_id=1, title="New Post", content="New Content", published=True)

    results3: Records = posts.search(published_query)
    assert len(results3) == 6


def test_validation_comprehensive(blog_db: BearBase) -> None:
    """Test comprehensive validation scenarios."""
    authors = blog_db.table("authors")

    with pytest.raises(ValueError, match="Unknown fields"):
        authors.insert(id=1, name="Bear", email="bear@example.com", invalid="field")

    with pytest.raises(ValueError, match="Missing required fields"):
        authors.insert(id=1)

    with pytest.raises(ValueError, match="Missing required fields"):
        authors.insert(name="Bear")

    authors.insert(id=1, name="Bear", email="bear@example.com")
    assert len(authors) == 1


def test_table_operations(tmp_path: Path) -> None:
    """Test table-level operations."""
    from bear_shelf.datastore import BearBase, Columns

    db_path: Path = tmp_path / "tables.json"
    db: BearBase = BearBase(str(db_path), storage="json")

    assert len(db.tables()) == 0

    db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    assert len(db.tables()) == 1
    assert "users" in db.tables()

    db.create_table(
        "posts",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="title", type="str"),
        ],
    )

    assert len(db.tables()) == 2

    db.drop_table("users")
    assert len(db.tables()) == 1
    assert "users" not in db.tables()
    assert "posts" in db.tables()

    db.close()


# ruff: noqa: E712 PLC0415
