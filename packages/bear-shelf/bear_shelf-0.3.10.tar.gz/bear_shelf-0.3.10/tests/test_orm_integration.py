"""Tests for SQLAlchemy ORM integration with JSONL dialect.

These tests use the modern SQLAlchemy 2.0+ style with DeclarativeBase and mapped_column.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import Boolean, Engine, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.engine.row import Row


class Base(DeclarativeBase):
    """Base class for ORM models."""


class User(Base):
    """User model for testing."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Post(Base):
    """Post model for testing."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    author_id: Mapped[int] = mapped_column(Integer)
    published: Mapped[bool] = mapped_column(Boolean, default=False)


@pytest.fixture
def sample_db_path():
    """Path to sample database."""
    return Path("sample_database.jsonl")


@pytest.fixture
def engine(sample_db_path):
    """Create engine connected to sample database."""
    if not sample_db_path.exists():
        pytest.skip("sample_database.jsonl not found")

    return create_engine(f"bearshelf:///{sample_db_path}")


class TestORMSelectQueries:
    """Test SELECT queries using SQLAlchemy ORM."""

    def test_select_all_users(self, engine):
        """Test selecting all users from the database."""
        with Session(engine) as session:
            users: Sequence[User] = session.execute(select(User)).scalars().all()

            assert len(users) == 3
            names: set[str] = {u.name for u in users}
            assert names == {"Bear", "Claire", "Shannon"}

    def test_select_user_by_name(self, engine):
        """Test selecting a specific user by name."""
        with Session(engine) as session:
            user: User = session.execute(select(User).where(User.name == "Bear")).scalar_one()

            assert user.name == "Bear"
            assert user.email == "bear@example.com"
            assert user.age == 30
            assert user.is_active is True

    def test_select_users_with_comparison(self, engine):
        """Test selecting users with comparison operators."""
        with Session(engine) as session:
            # Users with age > 25
            users: Sequence[User] = session.execute(select(User).where(User.age > 25)).scalars().all()

            assert len(users) == 1
            assert users[0].name == "Bear"

    def test_select_with_multiple_conditions(self, engine):
        """Test selecting with multiple WHERE conditions."""
        with Session(engine) as session:
            # Active users with age > 20
            users: Sequence[User] = (
                session.execute(select(User).where(User.age > 20, User.is_active.is_(True))).scalars().all()
            )

            assert len(users) == 2
            names: set[str] = {u.name for u in users}
            assert names == {"Bear", "Claire"}

    def test_select_with_null_values(self, engine):
        """Test selecting records with NULL values."""
        with Session(engine) as session:
            # Shannon has age=None
            user: User = session.execute(select(User).where(User.name == "Shannon")).scalar_one()

            assert user.age is None
            assert user.is_active is False

    def test_select_posts(self, engine: Engine):
        """Test selecting posts."""
        with Session(engine) as session:
            posts: Sequence[Post] = session.execute(select(Post)).scalars().all()

            assert len(posts) == 3

            # Check published posts
            published_posts: Sequence[Post] = (
                session.execute(select(Post).where(Post.published.is_(True))).scalars().all()
            )

            assert len(published_posts) == 2

    def test_select_with_order_by(self, engine: Engine) -> None:
        """Test selecting with ORDER BY."""
        with Session(engine) as session:
            # Order users by age descending
            users: Sequence[User] = (
                session.execute(select(User).where(User.age.is_not(None)).order_by(User.age.desc())).scalars().all()
            )

            # Bear (30) should come before Claire (21)
            assert len(users) >= 2
            assert users[0].name == "Bear"
            assert users[1].name == "Claire"

    def test_select_count(self, engine: Engine) -> None:
        """Test counting records."""
        with Session(engine) as session:
            from sqlalchemy import func  # noqa: PLC0415

            # Count all users
            count: int | None = session.execute(select(func.count()).select_from(User)).scalar()

            assert count == 3

    def test_select_specific_columns(self, engine: Engine) -> None:
        """Test selecting specific columns."""
        with Session(engine) as session:
            # Select only name and email
            results: Sequence[Row[tuple[str, str]]] = session.execute(select(User.name, User.email)).all()

            assert len(results) == 3
            for row in results:
                assert hasattr(row, "name")
                assert hasattr(row, "email")
