"""Tests for INSERT operations with SQLAlchemy ORM."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import shutil
import tempfile
from typing import Any

import pytest
from sqlalchemy import Boolean, Engine, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


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


@pytest.fixture
def temp_db_path() -> Generator[Path, Any]:
    """Create a temporary database file for testing."""
    sample_db = Path("sample_database.jsonl")
    if not sample_db.exists():
        pytest.skip("sample_database.jsonl not found")

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
        temp_path = Path(tmp.name)

    shutil.copy(sample_db, temp_path)

    yield temp_path

    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def engine(temp_db_path: Path) -> Engine:
    """Create engine connected to temporary database."""
    return create_engine(f"bearshelf:///{temp_db_path}")


class TestORMInsert:
    """Test INSERT operations using SQLAlchemy ORM."""

    def test_insert_single_user(self, engine: Engine) -> None:
        """Test inserting a single user."""
        with Session(engine) as session:
            # Insert a new user
            new_user = User(id=99, name="NewUser", email="newuser@example.com", age=25, is_active=True)
            session.add(new_user)
            session.commit()

            # Verify it was inserted
            user: User = session.execute(select(User).where(User.id == 99)).scalar_one()

            assert user.name == "NewUser"
            assert user.email == "newuser@example.com"
            assert user.age == 25
            assert user.is_active is True

    def test_insert_user_with_nullable_field(self, engine):
        """Test inserting a user with NULL age."""
        with Session(engine) as session:
            new_user = User(id=100, name="NoAge", email="noage@example.com", age=None, is_active=False)
            session.add(new_user)
            session.commit()

            user: User = session.execute(select(User).where(User.name == "NoAge")).scalar_one()

            assert user.age is None
            assert user.is_active is False

    def test_insert_multiple_users(self, engine):
        """Test inserting multiple users in one session."""
        with Session(engine) as session:
            user1 = User(id=101, name="User1", email="user1@test.com", age=20)
            user2 = User(id=102, name="User2", email="user2@test.com", age=30)
            user3 = User(id=103, name="User3", email="user3@test.com", age=40)

            session.add_all([user1, user2, user3])
            session.commit()
            users = session.execute(select(User).where(User.id >= 101)).scalars().all()
            assert len(users) == 3
            names: set[str] = {u.name for u in users}
            assert names == {"User1", "User2", "User3"}

    def test_insert_persists_across_sessions(self, engine):
        """Test that inserted data persists when reopening the database."""
        with Session(engine) as session:
            new_user = User(id=200, name="Persistent", email="persist@example.com", age=50)
            session.add(new_user)
            session.commit()

        # Verify in new session (reopens the file)
        with Session(engine) as session:
            user: User = session.execute(select(User).where(User.id == 200)).scalar_one()

            assert user.name == "Persistent"
            assert user.email == "persist@example.com"

    def test_insert_with_default_values(self, engine):
        """Test inserting with default values (is_active defaults to True)."""
        with Session(engine) as session:
            # Don't set is_active, should default to True
            new_user = User(id=300, name="DefaultActive", email="default@example.com", age=35)
            session.add(new_user)
            session.commit()

            # Verify default was applied
            user: User = session.execute(select(User).where(User.id == 300)).scalar_one()

            assert user.is_active is True
