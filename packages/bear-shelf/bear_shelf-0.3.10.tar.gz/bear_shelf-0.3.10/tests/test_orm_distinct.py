"""Tests for DISTINCT operations with SQLAlchemy ORM."""

from pathlib import Path
import tempfile

import pytest
from sqlalchemy import Boolean, Integer, String, create_engine, select
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
def temp_db_with_duplicates():
    """Create a temporary database with duplicate data for testing."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
        temp_path = Path(tmp.name)

    engine = create_engine(f"bearshelf:///{temp_path}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Add users with some duplicate names and ages
        users = [
            User(id=1, name="Alice", email="alice1@example.com", age=25, is_active=True),
            User(id=2, name="Bob", email="bob@example.com", age=30, is_active=True),
            User(id=3, name="Alice", email="alice2@example.com", age=25, is_active=False),
            User(id=4, name="Charlie", email="charlie@example.com", age=30, is_active=True),
            User(id=5, name="Alice", email="alice3@example.com", age=35, is_active=True),
        ]
        session.add_all(users)
        session.commit()

    yield temp_path, engine

    if temp_path.exists():
        temp_path.unlink()


class TestDistinct:
    """Test DISTINCT operations."""

    def test_distinct_single_column(self, temp_db_with_duplicates):
        """Test DISTINCT on a single column."""
        _, engine = temp_db_with_duplicates

        with Session(engine) as session:
            # Get distinct names (should be: Alice, Bob, Charlie)
            names = session.execute(select(User.name).distinct()).scalars().all()

            assert len(names) == 3
            assert set(names) == {"Alice", "Bob", "Charlie"}

    def test_distinct_single_column_with_duplicates(self, temp_db_with_duplicates):
        """Test DISTINCT removes duplicates from single column."""
        _, engine = temp_db_with_duplicates

        with Session(engine) as session:
            # Get distinct ages (should be: 25, 30, 35)
            ages = session.execute(select(User.age).distinct()).scalars().all()

            assert len(ages) == 3
            assert set(ages) == {25, 30, 35}

    def test_distinct_whole_record(self, temp_db_with_duplicates):
        """Test DISTINCT on entire records."""
        _, engine = temp_db_with_duplicates

        with Session(engine) as session:
            # All records are unique (different IDs), so should return all 5
            users = session.execute(select(User).distinct()).scalars().all()

            assert len(users) == 5

    def test_distinct_multiple_columns(self, temp_db_with_duplicates):
        """Test DISTINCT on multiple columns."""
        _, engine = temp_db_with_duplicates

        with Session(engine) as session:
            # Get distinct (name, age) combinations
            results = session.execute(select(User.name, User.age).distinct()).all()

            # Should have 4 unique combinations:
            # (Alice, 25), (Bob, 30), (Alice, 35), (Charlie, 30)
            assert len(results) == 4

            name_age_pairs = {(row[0], row[1]) for row in results}
            assert name_age_pairs == {
                ("Alice", 25),
                ("Bob", 30),
                ("Alice", 35),
                ("Charlie", 30),
            }

    def test_distinct_with_where(self, temp_db_with_duplicates):
        """Test DISTINCT combined with WHERE clause."""
        _, engine = temp_db_with_duplicates

        with Session(engine) as session:
            # Get distinct names of active users only
            names = session.execute(select(User.name).where(User.is_active.is_(True)).distinct()).scalars().all()

            # Should be: Alice, Bob, Charlie (all active)
            assert len(names) == 3
            assert set(names) == {"Alice", "Bob", "Charlie"}

    def test_distinct_with_order_by(self, temp_db_with_duplicates):
        """Test DISTINCT combined with ORDER BY."""
        _, engine = temp_db_with_duplicates

        with Session(engine) as session:
            # Get distinct names, ordered alphabetically
            names = session.execute(select(User.name).distinct().order_by(User.name)).scalars().all()

            assert names == ["Alice", "Bob", "Charlie"]

    def test_distinct_with_limit(self, temp_db_with_duplicates):
        """Test DISTINCT combined with LIMIT."""
        _, engine = temp_db_with_duplicates

        with Session(engine) as session:
            # Get first 2 distinct names
            names = session.execute(select(User.name).distinct().limit(2)).scalars().all()

            assert len(names) == 2
            # Should be a subset of distinct names
            assert all(name in {"Alice", "Bob", "Charlie"} for name in names)

    def test_distinct_without_duplicates(self, temp_db_with_duplicates):
        """Test DISTINCT when there are no duplicates."""
        _, engine = temp_db_with_duplicates

        with Session(engine) as session:
            # Get distinct emails (all unique)
            emails = session.execute(select(User.email).distinct()).scalars().all()

            # All 5 emails are unique
            assert len(emails) == 5

    def test_distinct_with_all_modifiers(self, temp_db_with_duplicates):
        """Test DISTINCT combined with WHERE, ORDER BY, LIMIT, OFFSET."""
        _, engine = temp_db_with_duplicates

        with Session(engine) as session:
            # Complex query: distinct ages of active users, ordered, with pagination
            ages = (
                session.execute(
                    select(User.age).where(User.is_active.is_(True)).distinct().order_by(User.age).limit(2).offset(0)
                )
                .scalars()
                .all()
            )

            # Active users have ages: 25, 30, 35
            # Ordered, first 2 should be: 25, 30
            assert ages == [25, 30]
