"""Tests for foreign key metadata preservation."""

from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import Engine, ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from bear_shelf.datastore import BearBase
from bear_shelf.datastore.record import Records
from bear_shelf.datastore.tables.data import TableData
from bear_shelf.datastore.tables.table import Table
from bear_shelf.datastore.unified_data import UnifiedDataFormat


def get_base(d: Any) -> BearBase:
    """Helper to get table data from dialect base."""
    return d.base


class TestForeignKeyMetadata:
    """Test that foreign key metadata is extracted and preserved."""

    def test_foreign_key_metadata_extracted(self, tmp_path: Path) -> None:
        """Test that FK metadata is captured from SQLAlchemy."""

        class Base(DeclarativeBase):
            """Base class for test models."""

        class User(Base):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]

        class Post(Base):
            __tablename__ = "posts"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            title: Mapped[str]
            author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

        db_file: Path = tmp_path / "fk_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")

        Base.metadata.create_all(engine)
        posts_table: Table = get_base(engine.dialect).table("posts")
        author_col: Any = next(col for col in posts_table.table_data.columns if col.name == "author_id")

        assert author_col.foreign_key == "users.id"

    def test_multiple_foreign_keys(self, tmp_path: Path) -> None:
        """Test multiple FK columns in same table."""

        class Base(DeclarativeBase):
            """Base class for test models."""

        class User(Base):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]

        class Category(Base):
            __tablename__ = "categories"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]

        class Article(Base):
            __tablename__ = "articles"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            title: Mapped[str]
            author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
            category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

        db_file: Path = tmp_path / "multi_fk_test.jsonl"
        engine: Engine = create_engine(f"bearshelf:///{db_file}")

        Base.metadata.create_all(engine)
        articles_table: Table = get_base(engine.dialect).table("articles")
        author_col: Any = next(col for col in articles_table.table_data.columns if col.name == "author_id")
        category_col: Any = next(col for col in articles_table.table_data.columns if col.name == "category_id")
        assert author_col.foreign_key == "users.id"
        assert category_col.foreign_key == "categories.id"

    def test_no_foreign_key_columns(self, tmp_path: Path) -> None:
        """Test that columns without FKs have None for foreign_key."""

        class Base(DeclarativeBase):
            """Base class for test models."""

        class SimpleTable(Base):
            __tablename__ = "simple"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]
            age: Mapped[int]

        db_file: Path = tmp_path / "no_fk_test.jsonl"
        engine: Engine = create_engine(f"bearshelf:///{db_file}")
        Base.metadata.create_all(engine)
        simple_table: Table = get_base(engine.dialect).table("simple")
        for col in simple_table.table_data.columns:
            assert col.foreign_key is None

    def test_foreign_key_insert_works(self, tmp_path: Path) -> None:
        """Test that FK columns work for basic insert/select operations."""

        class Base(DeclarativeBase):
            """Base class for test models."""

        class User(Base):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]

        class Post(Base):
            __tablename__ = "posts"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            title: Mapped[str]
            author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

        db_file: Path = tmp_path / "fk_insert_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")

        Base.metadata.create_all(engine)

        with Session(engine) as session:
            # Insert user
            user = User(name="Bear")
            session.add(user)
            session.commit()

            user_id: int = user.id

            # Insert post with FK reference
            post = Post(title="Test Post", author_id=user_id)
            session.add(post)
            session.commit()

            # Query back
            retrieved_post: Post | None = session.query(Post).filter_by(title="Test Post").first()
            assert retrieved_post is not None
            assert retrieved_post.author_id == user_id

    def test_foreign_key_nullable(self, tmp_path: Path) -> None:
        """Test that nullable FK columns work correctly."""

        class Base(DeclarativeBase):
            """Base class for test models."""

        class User(Base):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]

        class Comment(Base):
            __tablename__ = "comments"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            text: Mapped[str]
            author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

        db_file: Path = tmp_path / "fk_nullable_test.jsonl"
        engine: Engine = create_engine(f"bearshelf:///{db_file}")

        Base.metadata.create_all(engine)
        comments_table: Table = get_base(engine.dialect).table("comments")

        author_col = next(col for col in comments_table.table_data.columns if col.name == "author_id")

        assert author_col.foreign_key == "users.id"
        assert author_col.nullable is True

        # Insert comment without author
        with Session(engine) as session:
            comment = Comment(text="Anonymous comment", author_id=None)
            session.add(comment)
            session.commit()

            retrieved: Comment | None = session.query(Comment).first()
            assert retrieved is not None
            assert retrieved.author_id is None

    def test_foreign_key_schema_validation_missing_table(self) -> None:
        """Test that FK validation catches references to non-existent tables."""
        # Manually create schema with invalid FK reference
        tables_data = {
            "posts": {
                "name": "posts",
                "columns": [
                    {"name": "id", "type": "int", "primary_key": True},
                    {"name": "title", "type": "str"},
                    {"name": "author_id", "type": "int", "foreign_key": "users.id"},  # users doesn't exist!
                ],
                "records": [],
            }
        }

        # This should raise during validation
        with pytest.raises(ValueError, match="Foreign key references non-existent table 'users'"):
            UnifiedDataFormat._load_tables(tables=tables_data)

    def test_foreign_key_schema_validation_missing_column(self) -> None:
        """Test that FK validation catches references to non-existent columns."""
        # Create valid users table but reference wrong column
        tables_data = {
            "users": {
                "name": "users",
                "columns": [
                    {"name": "id", "type": "int", "primary_key": True},
                    {"name": "name", "type": "str"},
                ],
                "records": [],
            },
            "posts": {
                "name": "posts",
                "columns": [
                    {"name": "id", "type": "int", "primary_key": True},
                    {"name": "title", "type": "str"},
                    {
                        "name": "author_id",
                        "type": "int",
                        "foreign_key": "users.nonexistent_column",
                    },  # Column doesn't exist!
                ],
                "records": [],
            },
        }

        # This should raise during validation
        with pytest.raises(
            ValueError, match="Foreign key references non-existent column 'nonexistent_column' in table 'users'"
        ):
            UnifiedDataFormat._load_tables(tables=tables_data)

    def test_foreign_key_schema_validation_valid_references(self) -> None:
        """Test that valid FK references pass schema validation."""
        # Create valid schema with proper FK references
        tables_data = {
            "users": {
                "name": "users",
                "columns": [
                    {"name": "id", "type": "int", "primary_key": True},
                    {"name": "name", "type": "str"},
                ],
                "records": [],
            },
            "posts": {
                "name": "posts",
                "columns": [
                    {"name": "id", "type": "int", "primary_key": True},
                    {"name": "title", "type": "str"},
                    {"name": "author_id", "type": "int", "foreign_key": "users.id"},
                ],
                "records": [],
            },
        }

        udf: UnifiedDataFormat = UnifiedDataFormat._load_tables(tables=tables_data)
        posts_table: TableData = udf.table("posts")
        author_col = next(col for col in posts_table.columns if col.name == "author_id")
        assert author_col.foreign_key == "users.id"

    def test_get_related_records(self, tmp_path: Path) -> None:
        """Test get_related() method for traversing FK relationships."""

        class Base(DeclarativeBase):
            """Base class for test models."""

        class User(Base):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]

        class Post(Base):
            __tablename__ = "posts"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            title: Mapped[str]
            author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

        db_file: Path = tmp_path / "related_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")

        Base.metadata.create_all(engine)

        # Insert test data
        with Session(engine) as session:
            bear = User(name="Bear")
            session.add(bear)
            session.flush()
            bear_id = bear.id

            post1 = Post(title="First Post", author_id=bear_id)
            post2 = Post(title="Second Post", author_id=bear_id)
            post3 = Post(title="Third Post", author_id=bear_id)
            session.add_all([post1, post2, post3])

            # Add another user with no posts
            other_user = User(name="Other")
            session.add(other_user)
            session.flush()
            other_id = other_user.id

            session.commit()

        # Test get_related via BearBase
        base = get_base(engine.dialect)

        # Get all posts for bear
        bear_posts: Records = base.get_related("users", bear_id, "posts", "author_id")
        assert len(bear_posts) == 3
        assert all(post["author_id"] == bear_id for post in bear_posts)
        assert {post["title"] for post in bear_posts} == {"First Post", "Second Post", "Third Post"}
        other_posts: Records = base.get_related("users", other_id, "posts", "author_id")
        assert len(other_posts) == 0
