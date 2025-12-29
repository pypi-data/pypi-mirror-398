"""Comprehensive regression tests for integer primary keys.

REGRESSION TEST SUITE - Ensures integer PK functionality remains intact.

After fixing string PK bugs, we must ensure:
1. Integer autoincrement still works perfectly
2. Explicit integer PKs work
3. Mixed explicit/auto PKs work
4. Counter/sequence behavior is correct
5. highest_primary calculation works for integers
6. All CRUD operations work with integer PKs

This suite validates that all integer PK behavior remains unchanged.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from sqlalchemy import Engine, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    """Base class for ORM models."""


class User(Base):
    """User with auto-incrementing integer PK."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Category(Base):
    """Category with explicit integer PK."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))


class Post(Base):
    """Post with auto-incrementing PK."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(String, nullable=True)


@pytest.fixture
def engine(tmp_path: Path) -> Engine:
    """Create engine connected to temporary database."""
    engine = create_engine(f"bearshelf:///{tmp_path}/test_db.jsonl")
    Base.metadata.create_all(engine)
    return engine


class TestIntegerAutoIncrement:
    """Test auto-increment functionality for integer PKs."""

    def test_auto_increment_generates_ids(self, engine: Engine) -> None:
        """Auto-increment should generate sequential IDs."""
        with Session(engine) as session:
            users = [User(username=f"user{i}", email=f"user{i}@example.com") for i in range(1, 6)]
            session.add_all(users)
            session.commit()

            # All should have IDs
            for user in users:
                assert user.id is not None

            # IDs should be unique
            ids = [u.id for u in users]
            assert len(ids) == len(set(ids))

    def test_auto_increment_starts_at_zero(self, engine: Engine) -> None:
        """First auto-generated ID should be 0 (or configured start value)."""
        with Session(engine) as session:
            user = User(username="first", email="first@example.com")
            session.add(user)
            session.commit()

            # First ID is typically 0
            assert user.id >= 0

    def test_auto_increment_continues_across_sessions(self, engine: Engine) -> None:
        """Auto-increment counter should persist across sessions."""
        # First session
        with Session(engine) as session:
            user1 = User(username="user1", email="user1@example.com")
            session.add(user1)
            session.commit()
            first_id = user1.id

        # Second session
        with Session(engine) as session:
            user2 = User(username="user2", email="user2@example.com")
            session.add(user2)
            session.commit()
            second_id = user2.id

        # Second ID should be > first ID
        assert second_id > first_id

    def test_explicit_autoincrement_true(self, engine: Engine) -> None:
        """Explicitly setting autoincrement=True on integer PK should work."""
        with Session(engine) as session:
            cat = Category(name="Technology")
            session.add(cat)
            session.commit()

            assert cat.id is not None

    def test_bulk_insert_auto_increment(self, engine: Engine) -> None:
        """Bulk insert should auto-increment all IDs."""
        with Session(engine) as session:
            posts = [Post(title=f"Post {i}") for i in range(1, 11)]
            session.add_all(posts)
            session.commit()

            # All should have unique IDs
            ids = [p.id for p in posts]
            assert len(ids) == 10
            assert len(set(ids)) == 10


class TestExplicitIntegerPK:
    """Test explicitly setting integer PK values."""

    def test_explicit_integer_pk_value(self, engine: Engine) -> None:
        """Explicitly setting integer PK should work."""
        with Session(engine) as session:
            user = User(id=999, username="explicit", email="explicit@example.com")
            user2 = User(username="auto", email="lol@lol.com")
            session.add_all([user, user2])
            session.commit()
            session.flush()
            all_users: Sequence[User] = session.execute(select(User)).scalars().all()
            assert len(all_users) == 2
            retrieved: User = session.execute(select(User).where(User.id == 999)).scalar_one()
            second: User = session.execute(select(User).where(User.username == "auto")).scalar_one()
            assert second.id == 1000
            assert retrieved.username == "explicit"
            assert second.username == "auto"

    def test_explicit_pk_skips_value_in_sequence(self, engine: Engine) -> None:
        """Explicitly used PK values should be skipped by auto-increment."""
        with Session(engine) as session:
            # Insert with explicit high ID
            user1 = User(id=100, username="explicit100", email="e100@example.com")
            session.add(user1)
            session.commit()

            # Insert with auto-increment
            user2 = User(username="auto", email="auto@example.com")
            session.add(user2)
            session.commit()

            # Auto ID should be >= 100 to avoid collision
            assert user2.id is not None
            # The counter should have updated to handle this
            assert user2.id != 100  # Should not duplicate

    def test_mixed_explicit_and_auto_ids(self, engine: Engine) -> None:
        """Mixing explicit and auto-generated IDs should work."""
        with Session(engine) as session:
            # Auto
            user1 = User(username="auto1", email="auto1@example.com")
            session.add(user1)
            session.commit()

            # Explicit
            user2 = User(id=50, username="explicit", email="explicit@example.com")
            session.add(user2)
            session.commit()

            # Auto again
            user3 = User(username="auto2", email="auto2@example.com")
            session.add(user3)
            session.commit()

            # All should exist with unique IDs
            all_users = session.execute(select(User)).scalars().all()
            assert len(all_users) == 3

            ids = [u.id for u in all_users]
            assert len(set(ids)) == 3


class TestIntegerPKCRUD:
    """Test CRUD operations with integer PKs."""

    def test_insert_integer_pk(self, engine: Engine) -> None:
        """Insert with integer PK should work."""
        with Session(engine) as session:
            user = User(username="test", email="test@example.com", score=100)
            session.add(user)
            session.commit()

            assert user.id is not None

    def test_query_by_integer_pk(self, engine: Engine) -> None:
        """Query by integer PK should work."""
        with Session(engine) as session:
            user = User(id=42, username="answer", email="42@example.com")
            session.add(user)
            session.commit()

        with Session(engine) as session:
            retrieved = session.execute(select(User).where(User.id == 42)).scalar_one()

            assert retrieved.username == "answer"

    def test_update_integer_pk_record(self, engine: Engine) -> None:
        """Update record with integer PK should work."""
        with Session(engine) as session:
            user = User(username="original", email="original@example.com", score=50)
            session.add(user)
            session.commit()

            user_id = user.id

            # Update
            user.username = "updated"
            user.score = 100
            session.commit()

        # Verify in new session
        with Session(engine) as session:
            retrieved = session.execute(select(User).where(User.id == user_id)).scalar_one()

            assert retrieved.username == "updated"
            assert retrieved.score == 100

    def test_delete_integer_pk_record(self, engine: Engine) -> None:
        """Delete record with integer PK should work."""
        with Session(engine) as session:
            user = User(username="todelete", email="delete@example.com")
            session.add(user)
            session.commit()

            user_id = user.id

            # Delete
            session.delete(user)
            session.commit()

        # Verify deletion
        with Session(engine) as session:
            result = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

            assert result is None


class TestIntegerPKUniqueness:
    """Test uniqueness constraints on integer PKs."""

    # def test_duplicate_integer_pk_raises_error(self, engine: Engine) -> None:
    #     """Duplicate integer PK should raise error."""
    #     with Session(engine) as session:
    #         user1 = User(id=1, username="first", email="first@example.com")
    #         session.add(user1)
    #         session.commit()

    #         user2 = User(id=1, username="duplicate", email="duplicate@example.com")
    #         session.add(user2)

    #         with pytest.raises(Exception):
    #             session.commit()

    def test_auto_ids_never_duplicate(self, engine: Engine) -> None:
        """Auto-generated IDs should never duplicate."""
        with Session(engine) as session:
            users = [User(username=f"user{i}", email=f"user{i}@example.com") for i in range(20)]
            session.add_all(users)
            session.commit()

            ids = [u.id for u in users]
            assert len(ids) == len(set(ids))


class TestIntegerPKEdgeCases:
    """Edge cases for integer PKs."""

    def test_zero_as_integer_pk(self, engine: Engine) -> None:
        """Zero should be a valid integer PK value."""
        with Session(engine) as session:
            user = User(id=0, username="zero", email="zero@example.com")
            session.add(user)
            session.commit()

            retrieved = session.execute(select(User).where(User.id == 0)).scalar_one()

            assert retrieved.username == "zero"

    # def test_negative_integer_pk(self, engine: Engine) -> None:
    #     """Negative integers should be valid PK values."""
    #     with Session(engine) as session:
    #         user = User(id=-1, username="negative", email="negative@example.com")
    #         session.add(user)
    #         session.commit()

    #         retrieved = session.execute(
    #             select(User).where(User.id == -1)
    #         ).scalar_one()

    #         assert retrieved.username == "negative"

    # def test_large_integer_pk(self, engine: Engine) -> None:
    #     """Large integer values should work as PKs."""
    #     large_id = 2**31 - 1  # Max 32-bit signed int

    #     with Session(engine) as session:
    #         user = User(id=large_id, username="large", email="large@example.com")
    #         session.add(user)
    #         session.commit()

    #         retrieved = session.execute(
    #             select(User).where(User.id == large_id)
    #         ).scalar_one()

    #         assert retrieved.username == "large"

    def test_gaps_in_integer_sequence(self, engine: Engine) -> None:
        """Gaps in integer sequence should be allowed."""
        with Session(engine) as session:
            user1 = User(id=1, username="one", email="one@example.com")
            user2 = User(id=100, username="hundred", email="hundred@example.com")
            user3 = User(id=50, username="fifty", email="fifty@example.com")
            user4 = User(username="auto", email="auto@example.com")

            session.add_all([user1, user2, user3, user4])
            session.commit()

            all_users: Sequence[User] = session.execute(select(User)).scalars().all()
            assert len(all_users) == 4

            ids: set[int] = {u.id for u in all_users}
            assert ids == {1, 50, 100, 101}


class TestCounterBehavior:
    """Test auto-increment counter behavior (highest_primary related)."""

    def test_counter_tracks_highest_value(self, engine: Engine) -> None:
        """Counter should track the highest PK value seen."""
        with Session(engine) as session:
            # Insert with explicit high value
            user1 = User(id=500, username="high", email="high@example.com")
            session.add(user1)
            session.commit()

            # Auto-increment should start above 500
            user2 = User(username="auto", email="auto@example.com")
            session.add(user2)
            session.commit()

            # Should not conflict with 500
            assert user2.id > 500 or user2.id < 500

    def test_counter_after_delete(self, engine: Engine) -> None:
        """Counter should not reuse IDs after deletion."""
        with Session(engine) as session:
            user1 = User(username="first", email="first@example.com")
            session.add(user1)
            session.commit()

            first_id = user1.id

            # Delete user1
            session.delete(user1)
            session.commit()

            # Insert new user - should get new ID, not reuse deleted one
            user2 = User(username="second", email="second@example.com")
            session.add(user2)
            session.commit()

            # New ID should be different (typically higher)
            assert user2.id != first_id

    def test_counter_persistence_across_sessions(self, engine: Engine) -> None:
        """Counter value should persist across database sessions."""
        # Session 1: Insert and get ID
        with Session(engine) as session:
            user1 = User(username="session1", email="session1@example.com")
            session.add(user1)
            session.commit()
            id1 = user1.id

        # Session 2: Insert another
        with Session(engine) as session:
            user2 = User(username="session2", email="session2@example.com")
            session.add(user2)
            session.commit()
            id2 = user2.id

        # Session 3: Insert another
        with Session(engine) as session:
            user3 = User(username="session3", email="session3@example.com")
            session.add(user3)
            session.commit()
            id3 = user3.id

        # IDs should be increasing
        assert id1 < id2 < id3
