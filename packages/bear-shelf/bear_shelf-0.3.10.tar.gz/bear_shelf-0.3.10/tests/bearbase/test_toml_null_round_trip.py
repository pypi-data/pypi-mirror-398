"""Tests for TOML null handling through the database layer."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    """Declarative base for TOML null round-trip tests."""


class Profile(Base):
    """Profile table with nullable columns for TOML persistence testing."""

    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    nickname: Mapped[str | None] = mapped_column(nullable=True)
    bio: Mapped[str | None] = mapped_column(nullable=True, default=None)


class Preferences(Base):
    """Secondary table to ensure multiple tables handle nulls independently."""

    __tablename__ = "preferences"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    theme: Mapped[str | None] = mapped_column(nullable=True)
    timezone: Mapped[str | None] = mapped_column(nullable=True)


def test_toml_database_round_trip_nulls(tmp_path: Path) -> None:
    """Ensure the bearshelf database writes and reads None values with TOML storage."""
    db_path: Path = tmp_path / "null_profiles.toml"

    engine = create_engine(f"bearshelf:///{db_path}", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all(
            [
                Profile(id=1, nickname=None, bio="first profile"),
                Profile(id=2, nickname="bear", bio=None),
            ]
        )
        session.commit()

    engine.dispose()

    reopened_engine = create_engine(f"bearshelf:///{db_path}", echo=False)
    with Session(reopened_engine) as session:
        profiles = session.query(Profile).order_by(Profile.id).all()

    reopened_engine.dispose()

    assert len(profiles) == 2
    assert profiles[0].nickname is None
    assert profiles[0].bio == "first profile"
    assert profiles[1].nickname == "bear"
    assert profiles[1].bio is None


def test_toml_database_literal_string_null_stays_string(tmp_path: Path) -> None:
    """Confirm literal string 'null' stays a string and is not coerced to None."""
    db_path: Path = tmp_path / "literal_null.toml"
    engine = create_engine(f"bearshelf:///{db_path}", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Profile(id=1, nickname="null", bio="kept"))
        session.commit()

    engine.dispose()

    reopened = create_engine(f"bearshelf:///{db_path}", echo=False)
    with Session(reopened) as session:
        profile = session.query(Profile).first()
        assert profile is not None
        assert profile.nickname == "null"  # literal string is preserved
        assert profile.bio == "kept"

    reopened.dispose()


def test_toml_database_update_to_null(tmp_path: Path) -> None:
    """Ensure updates that set values to None are persisted and restored."""
    db_path: Path = tmp_path / "update_null.toml"
    engine = create_engine(f"bearshelf:///{db_path}", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Profile(id=1, nickname="bear", bio="hello"))
        session.commit()

    # Update nickname to None
    with Session(engine) as session:
        profile = session.query(Profile).first()
        assert profile is not None
        profile.nickname = None
        session.commit()

    engine.dispose()

    reopened = create_engine(f"bearshelf:///{db_path}", echo=False)
    with Session(reopened) as session:
        updated = session.query(Profile).first()
        assert updated is not None
        assert updated.nickname is None
        assert updated.bio == "hello"

    reopened.dispose()


def test_toml_database_multiple_tables_nulls(tmp_path: Path) -> None:
    """Verify null handling when multiple tables share the same TOML file."""
    db_path: Path = tmp_path / "multi_table_nulls.toml"
    engine = create_engine(f"bearshelf:///{db_path}", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Profile(id=1, nickname=None, bio=None))
        session.add(Preferences(id=1, theme="dark", timezone=None))
        session.commit()

    engine.dispose()

    reopened = create_engine(f"bearshelf:///{db_path}", echo=False)
    with Session(reopened) as session:
        profile = session.query(Profile).first()
        pref = session.query(Preferences).first()

    reopened.dispose()

    assert profile is not None
    assert profile.nickname is None
    assert profile.bio is None
    assert pref is not None
    assert pref.theme == "dark"
    assert pref.timezone is None
