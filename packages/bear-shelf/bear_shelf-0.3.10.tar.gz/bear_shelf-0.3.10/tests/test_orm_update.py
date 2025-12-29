"""Tests for UPDATE operations with SQLAlchemy ORM."""

from pathlib import Path
import shutil
import tempfile

import pytest
from sqlalchemy import Boolean, Integer, String, create_engine, select, update
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
def temp_db_path():
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
def engine(temp_db_path):
    """Create engine connected to temporary database."""
    return create_engine(f"bearshelf:///{temp_db_path}")


class TestORMUpdate:
    """Test UPDATE operations using SQLAlchemy ORM."""

    def test_update_single_record(self, engine):
        """Test updating a single record."""
        with Session(engine) as session:
            # Update Bear's age
            session.execute(update(User).where(User.name == "Bear").values(age=31))
            session.commit()

            # Verify the update
            bear = session.execute(select(User).where(User.name == "Bear")).scalar_one()

            assert bear.age == 31

    def test_update_multiple_fields(self, engine):
        """Test updating multiple fields at once."""
        with Session(engine) as session:
            # Update Claire's age and email
            session.execute(update(User).where(User.name == "Claire").values(age=22, email="claire_new@example.com"))
            session.commit()

            # Verify the updates
            claire = session.execute(select(User).where(User.name == "Claire")).scalar_one()

            assert claire.age == 22
            assert claire.email == "claire_new@example.com"

    def test_update_with_orm_object(self, engine):
        """Test updating using ORM object (not raw SQL)."""
        with Session(engine) as session:
            # Get Shannon and update
            shannon = session.execute(select(User).where(User.name == "Shannon")).scalar_one()

            shannon.age = 25
            shannon.is_active = True
            session.commit()

            # Verify in new session
            with Session(engine) as session2:
                shannon = session2.execute(select(User).where(User.name == "Shannon")).scalar_one()

                assert shannon.age == 25
                assert shannon.is_active is True

    def test_update_multiple_records(self, engine):
        """Test updating multiple records with one statement."""
        with Session(engine) as session:
            # Deactivate all users with age > 25
            session.execute(update(User).where(User.age > 25).values(is_active=False))
            session.commit()

            # Verify Bear (age 30) is now inactive
            bear: User = session.execute(select(User).where(User.name == "Bear")).scalar_one()

            assert bear.is_active is False

            # Verify Claire (age 21) is still active
            claire = session.execute(select(User).where(User.name == "Claire")).scalar_one()

            assert claire.is_active is True

    def test_update_to_null(self, engine):
        """Test updating a field to NULL."""
        with Session(engine) as session:
            # Set Bear's age to NULL
            session.execute(update(User).where(User.name == "Bear").values(age=None))
            session.commit()

            # Verify
            bear = session.execute(select(User).where(User.name == "Bear")).scalar_one()

            assert bear.age is None

    def test_update_persists(self, engine):
        """Test that updates persist across sessions."""
        # Update in first session
        with Session(engine) as session:
            session.execute(update(User).where(User.name == "Bear").values(age=99))
            session.commit()

        # Verify in new session
        with Session(engine) as session:
            bear = session.execute(select(User).where(User.name == "Bear")).scalar_one()

            assert bear.age == 99
