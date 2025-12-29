"""Tests for LIKE and NOT LIKE operator support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import Engine, Integer, Select, String, create_engine, select
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

Base = declarative_base()


class User(Base):
    """Test user model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)


@pytest.fixture
def engine(tmp_path: Path) -> Engine:
    """Create test engine with bear-shelf dialect."""
    db_path = tmp_path / "test.jsonl"
    return create_engine(f"bearshelf:///{db_path}")


@pytest.fixture
def session(engine: Engine) -> Generator[Session, Any]:
    """Create test session and populate with test data."""
    Base.metadata.create_all(engine)

    with Session(engine) as sess:
        sess.add_all(
            [
                User(name="Bear", email="bear@example.com"),
                User(name="Bea", email="bea@test.com"),
                User(name="Carl", email="carl@example.com"),
                User(name="Alice", email="alice@other.org"),
                User(name="Bob", email="bob@example.com"),
            ]
        )
        sess.commit()

    with Session(engine) as sess:
        yield sess


def test_like_starts_with(session: Session) -> None:
    """Test LIKE with pattern matching prefix (B%)."""
    stmt = select(User).where(User.name.like("B%"))
    results = session.execute(stmt).scalars().all()

    assert len(results) == 3
    names = {u.name for u in results}
    assert names == {"Bear", "Bea", "Bob"}


def test_like_ends_with(session):
    """Test LIKE with pattern matching suffix (%ar)."""
    stmt: Select[tuple[User]] = select(User).where(User.name.like("%ar"))
    results = session.execute(stmt).scalars().all()

    assert len(results) == 1
    assert results[0].name == "Bear"


def test_like_contains(session):
    """Test LIKE with pattern matching substring (%a%)."""
    stmt = select(User).where(User.name.like("%a%"))
    results = session.execute(stmt).scalars().all()

    assert len(results) == 3
    names = {u.name for u in results}
    assert names == {"Bear", "Carl", "Bea"}  # All contain 'a'


def test_like_single_char_wildcard(session):
    """Test LIKE with single character wildcard (Be_)."""
    stmt = select(User).where(User.name.like("Be_"))
    results = session.execute(stmt).scalars().all()

    assert len(results) == 1
    assert results[0].name == "Bea"


def test_like_exact_match(session):
    """Test LIKE with no wildcards (exact match)."""
    stmt: Select[tuple[User]] = select(User).where(User.name.like("Bear"))
    results = session.execute(stmt).scalars().all()

    assert len(results) == 1
    assert results[0].name == "Bear"


def test_like_no_match(session):
    """Test LIKE with pattern that matches nothing."""
    stmt = select(User).where(User.name.like("Z%"))
    results = session.execute(stmt).scalars().all()

    assert len(results) == 0


def test_like_email_domain(session):
    """Test LIKE matching email domain."""
    stmt = select(User).where(User.email.like("%@example.com"))
    results = session.execute(stmt).scalars().all()

    assert len(results) == 3
    names = {u.name for u in results}
    assert names == {"Bear", "Carl", "Bob"}


def test_not_like_starts_with(session):
    """Test NOT LIKE with pattern excluding prefix (B%)."""
    stmt = select(User).where(User.name.notlike("B%"))
    results = session.execute(stmt).scalars().all()

    assert len(results) == 2
    names = {u.name for u in results}
    assert names == {"Carl", "Alice"}


def test_not_like_contains(session):
    """Test NOT LIKE with pattern excluding substring (%a%)."""
    stmt: Select[tuple[User]] = select(User).where(User.name.notlike("%a%"))
    results = session.execute(stmt).scalars().all()

    assert len(results) == 2
    names = {u.name for u in results}
    assert names == {"Alice", "Bob"}  # Don't contain 'a' (Alice has 'i', Bob has 'o')


def test_not_like_email_domain(session):
    """Test NOT LIKE excluding email domain."""
    stmt: Select[tuple[User]] = select(User).where(User.email.notlike("%@example.com"))
    results = session.execute(stmt).scalars().all()

    assert len(results) == 2
    names = {u.name for u in results}
    assert names == {"Bea", "Alice"}


def test_like_special_chars(session):
    """Test LIKE with special regex characters in pattern."""
    # Add user with special characters
    session.add(User(name="user.name", email="test@example.com"))
    session.commit()

    stmt: Select[tuple[User]] = select(User).where(User.name.like("user.%"))
    results = session.execute(stmt).scalars().all()

    # Should match "user.name" (dot is literal, % matches rest)
    assert len(results) == 1
    assert results[0].name == "user.name"


def test_like_combined_wildcards(session):
    """Test LIKE with multiple wildcards in one pattern."""
    stmt: Select[tuple[User]] = select(User).where(User.name.like("B_a%"))
    results = session.execute(stmt).scalars().all()

    # Matches "Bear" (B-e-a-r) and "Bea" (B-e-a)
    assert len(results) == 2
    names = {u.name for u in results}
    assert names == {"Bear", "Bea"}


def test_like_case_sensitive(session):
    """Test that LIKE is case-sensitive."""
    stmt: Select[tuple[User]] = select(User).where(User.name.like("bear"))  # lowercase
    results = session.execute(stmt).scalars().all()

    # Should NOT match "Bear" (uppercase B)
    assert len(results) == 0
