"""Tests for ORDER BY, LIMIT, OFFSET operations with SQLAlchemy ORM."""

from pathlib import Path
import shutil
import tempfile
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import Boolean, Engine, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

if TYPE_CHECKING:
    from collections.abc import Sequence


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


class TestOrderBy:
    """Test ORDER BY operations."""

    def test_order_by_ascending(self, engine):
        """Test ordering by a column in ascending order."""
        with Session(engine) as session:
            users = session.execute(select(User).order_by(User.age)).scalars().all()

            # Should be ordered by age (ascending)
            ages = [u.age for u in users if u.age is not None]
            assert ages == sorted(ages)

    def test_order_by_descending(self, engine):
        """Test ordering by a column in descending order."""
        with Session(engine) as session:
            users = session.execute(select(User).order_by(User.age.desc())).scalars().all()

            # Should be ordered by age (descending)
            ages: list[int] = [u.age for u in users if u.age is not None]
            assert ages == sorted(ages, reverse=True)

    def test_order_by_name(self, engine: Engine) -> None:
        """Test ordering by string column."""
        with Session(engine) as session:
            users: Sequence[User] = session.execute(select(User).order_by(User.name)).scalars().all()

            # Should be ordered by name alphabetically
            names: list[str] = [u.name for u in users]
            assert names == sorted(names)

    def test_order_by_with_where(self, engine: Engine) -> None:
        """Test ORDER BY combined with WHERE clause."""
        with Session(engine) as session:
            users = session.execute(select(User).where(User.age > 20).order_by(User.age)).scalars().all()

            # All should have age > 20 and be ordered
            ages: list[int | None] = [u.age for u in users]
            assert all(age is not None and age > 20 for age in ages)
            assert ages == sorted(age for age in ages if age is not None)


class TestLimit:
    """Test LIMIT operations."""

    def test_limit_basic(self, engine):
        """Test basic LIMIT functionality."""
        with Session(engine) as session:
            users = session.execute(select(User).limit(2)).scalars().all()

            assert len(users) == 2

    def test_limit_one(self, engine):
        """Test LIMIT 1."""
        with Session(engine) as session:
            users = session.execute(select(User).limit(1)).scalars().all()

            assert len(users) == 1

    def test_limit_with_order_by(self, engine):
        """Test LIMIT combined with ORDER BY."""
        with Session(engine) as session:
            # Get the 2 youngest users
            users = session.execute(select(User).order_by(User.age).limit(2)).scalars().all()

            assert len(users) == 2
            # Verify they're the youngest
            ages: list[int] = [u.age for u in users if u.age is not None]
            if ages:
                assert ages == sorted(ages)

    def test_limit_larger_than_result_set(self, engine):
        """Test LIMIT larger than the number of results."""
        with Session(engine) as session:
            all_users = session.execute(select(User)).scalars().all()
            limited_users = session.execute(select(User).limit(1000)).scalars().all()

            # Should return all users when limit > total
            assert len(limited_users) == len(all_users)


class TestOffset:
    """Test OFFSET operations."""

    def test_offset_basic(self, engine):
        """Test basic OFFSET functionality."""
        with Session(engine) as session:
            all_users = session.execute(select(User).order_by(User.id)).scalars().all()
            offset_users = session.execute(select(User).order_by(User.id).offset(1)).scalars().all()

            # Should skip the first user
            assert len(offset_users) == len(all_users) - 1
            assert offset_users[0].id == all_users[1].id

    def test_offset_with_order_by(self, engine):
        """Test OFFSET combined with ORDER BY."""
        with Session(engine) as session:
            all_ordered = session.execute(select(User).order_by(User.name)).scalars().all()
            offset_ordered = session.execute(select(User).order_by(User.name).offset(2)).scalars().all()

            # Should skip first 2 users
            assert len(offset_ordered) == len(all_ordered) - 2
            if len(all_ordered) > 2:
                assert offset_ordered[0].name == all_ordered[2].name


class TestPagination:
    """Test LIMIT and OFFSET together for pagination."""

    def test_pagination_first_page(self, engine):
        """Test pagination: first page."""
        with Session(engine) as session:
            page_1 = session.execute(select(User).order_by(User.id).limit(2).offset(0)).scalars().all()

            assert len(page_1) <= 2
            if len(page_1) > 0:
                # Should start from beginning
                all_users = session.execute(select(User).order_by(User.id)).scalars().all()
                assert page_1[0].id == all_users[0].id

    def test_pagination_second_page(self, engine):
        """Test pagination: second page."""
        with Session(engine) as session:
            page_2 = session.execute(select(User).order_by(User.id).limit(2).offset(2)).scalars().all()

            all_users = session.execute(select(User).order_by(User.id)).scalars().all()

            # Verify it's the correct slice
            if len(all_users) > 2:
                expected_count = min(2, len(all_users) - 2)
                assert len(page_2) == expected_count
                if expected_count > 0:
                    assert page_2[0].id == all_users[2].id

    def test_pagination_complete_iteration(self, engine):
        """Test paginating through all results."""
        with Session(engine) as session:
            all_users = session.execute(select(User).order_by(User.id)).scalars().all()

            page_size = 2
            collected_users = []

            for page_num in range((len(all_users) + page_size - 1) // page_size):
                page = (
                    session.execute(select(User).order_by(User.id).limit(page_size).offset(page_num * page_size))
                    .scalars()
                    .all()
                )
                collected_users.extend(page)

            # Should collect all users
            assert len(collected_users) == len(all_users)
            # Should be in same order
            assert [u.id for u in collected_users] == [u.id for u in all_users]

    def test_limit_offset_with_where(self, engine):
        """Test LIMIT and OFFSET combined with WHERE clause."""
        with Session(engine) as session:
            # Get users with age > 20, ordered, paginated
            filtered_users = session.execute(select(User).where(User.age > 20).order_by(User.age)).scalars().all()

            if len(filtered_users) > 2:
                page = (
                    session.execute(select(User).where(User.age > 20).order_by(User.age).limit(2).offset(1))
                    .scalars()
                    .all()
                )

                assert len(page) == 2
                assert page[0].id == filtered_users[1].id
                assert page[1].id == filtered_users[2].id


class TestEdgeCases:
    """Test edge cases and combinations."""

    def test_offset_beyond_results(self, engine):
        """Test OFFSET larger than result count."""
        with Session(engine) as session:
            users = session.execute(select(User).offset(1000)).scalars().all()

            # Should return empty
            assert len(users) == 0

    def test_zero_limit(self, engine):
        """Test LIMIT 0."""
        with Session(engine) as session:
            users = session.execute(select(User).limit(0)).scalars().all()

            # Should return empty
            assert len(users) == 0

    def test_order_by_limit_offset_combination(self, engine):
        """Test all three modifiers together."""
        with Session(engine) as session:
            users = session.execute(select(User).order_by(User.name).limit(2).offset(1)).scalars().all()

            # Should be ordered, skip 1, take 2
            assert len(users) <= 2
            if len(users) > 1:
                assert users[0].name < users[1].name
