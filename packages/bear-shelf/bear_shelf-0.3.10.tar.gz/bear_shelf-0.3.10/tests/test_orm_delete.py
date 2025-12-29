"""Tests for DELETE operations with SQLAlchemy ORM."""

from collections.abc import Generator, Sequence
from pathlib import Path
import shutil
import tempfile
from typing import Any

import pytest
from sqlalchemy import Boolean, Engine, Integer, Result, String, create_engine, delete, select
from sqlalchemy.engine.row import Row  # noqa: TC002
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


class TestORMDelete:
    """Test DELETE operations using SQLAlchemy ORM."""

    def test_delete_single_record(self, engine: Engine) -> None:
        """Test deleting a single record by condition."""
        with Session(engine) as session:
            # Count before delete
            count_before: Sequence[Row[tuple[User]]] = session.execute(select(User)).all()
            initial_count: int = len(count_before)

            # Delete Bear
            result: Result = session.execute(delete(User).where(User.name == "Bear"))
            session.commit()

            assert result.rowcount == 1  # type:ignore[arg-type]

            # Verify Bear is gone
            users: Sequence[User] = session.execute(select(User)).scalars().all()
            assert len(users) == initial_count - 1
            assert all(user.name != "Bear" for user in users)

    def test_delete_by_id(self, engine: Engine) -> None:
        """Test deleting a record by primary key."""
        with Session(engine) as session:
            # Get Bear's ID
            bear: User = session.execute(select(User).where(User.name == "Bear")).scalar_one()
            bear_id: int = bear.id

            # Delete by ID
            result: Result = session.execute(delete(User).where(User.id == bear_id))
            session.commit()

            assert result.rowcount == 1  # type:ignore[arg-type]

            # Verify Bear is gone
            bear_result: Row[tuple[User]] | None = session.execute(select(User).where(User.id == bear_id)).first()
            assert bear_result is None

    def test_delete_multiple_records(self, engine: Engine) -> None:
        """Test deleting multiple records with one statement."""
        with Session(engine) as session:
            # Count users with age > 25
            users_to_delete = session.execute(select(User).where(User.age > 25)).scalars().all()
            expected_deletes = len(users_to_delete)

            # Delete all users with age > 25
            result: Result = session.execute(delete(User).where(User.age > 25))
            session.commit()

            assert result.rowcount == expected_deletes  # type:ignore[arg-type]

            # Verify they're gone
            remaining_users: Sequence[User] = session.execute(select(User)).scalars().all()
            assert all(user.age is None or user.age <= 25 for user in remaining_users)

    def test_delete_with_complex_condition(self, engine: Engine):
        """Test deleting with multiple conditions."""
        with Session(engine) as session:
            # Delete inactive users with age < 25
            session.execute(delete(User).where((User.is_active.is_(False)) & (User.age < 25)))
            session.commit()

            # Verify no inactive young users remain
            remaining: Sequence[Row[tuple[User]]] = session.execute(
                select(User).where((User.is_active.is_(False)) & (User.age < 25))
            ).all()
            assert len(remaining) == 0

    def test_delete_no_match(self, engine: Engine):
        """Test deleting when no records match the condition."""
        with Session(engine) as session:
            # Try to delete user with non-existent name
            result: Result = session.execute(delete(User).where(User.name == "NonExistent"))
            session.commit()

            assert result.rowcount == 0  # type:ignore[arg-type]

    def test_delete_persists(self, engine):
        """Test that deletes persist across sessions."""
        # Delete in first session
        with Session(engine) as session:
            session.execute(delete(User).where(User.name == "Bear"))
            session.commit()

        # Verify in new session
        with Session(engine) as session:
            bear: Row[tuple[User]] | None = session.execute(select(User).where(User.name == "Bear")).first()
            assert bear is None

    def test_delete_using_orm_object(self, engine):
        """Test deleting using ORM object."""
        with Session(engine) as session:
            # Get Shannon
            shannon: User = session.execute(select(User).where(User.name == "Shannon")).scalar_one()

            # Delete using session.delete()
            session.delete(shannon)
            session.commit()

            # Verify in same session
            result: Row[tuple[User]] | None = session.execute(select(User).where(User.name == "Shannon")).first()
            assert result is None

        # Verify in new session
        with Session(engine) as session:
            result = session.execute(select(User).where(User.name == "Shannon")).first()
            assert result is None

    def test_delete_and_insert_same_id(self, engine: Engine) -> None:
        """Test that we can delete a record and insert a new one with the same ID."""
        with Session(engine) as session:
            # Get Bear's ID
            bear: User = session.execute(select(User).where(User.name == "Bear")).scalar_one()
            bear_id: int = bear.id

            # Delete Bear
            session.execute(delete(User).where(User.id == bear_id))
            session.commit()

            # Insert new user with same ID
            new_user = User(id=bear_id, name="NewBear", email="newbear@example.com", age=1, is_active=True)
            session.add(new_user)
            session.commit()

            # Verify
            user: User = session.execute(select(User).where(User.id == bear_id)).scalar_one()
            assert user.name == "NewBear"
            assert user.email == "newbear@example.com"

    def test_delete_with_or_condition(self, engine: Engine) -> None:
        """Test deleting with OR condition."""
        with Session(engine) as session:
            # Delete users named Bear OR Claire
            result: Result = session.execute(delete(User).where((User.name == "Bear") | (User.name == "Claire")))
            session.commit()

            assert result.rowcount >= 2  # type:ignore[arg-type]

            # Verify they're gone
            remaining: Sequence[Row[tuple[User]]] = session.execute(
                select(User).where((User.name == "Bear") | (User.name == "Claire"))
            ).all()
            assert len(remaining) == 0
