"""Test IS NULL and IS NOT NULL operators."""

from collections.abc import Sequence
from pathlib import Path

from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column()
    email: Mapped[str | None] = mapped_column(nullable=True)
    phone: Mapped[str | None] = mapped_column(nullable=True)


def test_is_null(tmp_path: Path) -> None:
    """Test IS NULL operator - find records where a column is NULL."""
    path: Path = tmp_path / "test_is_null.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        users = [
            User(id=1, name="Alice", email="alice@example.com", phone="555-1234"),
            User(id=2, name="Bob", email="bob@example.com", phone=None),
            User(id=3, name="Charlie", email=None, phone="555-5678"),
            User(id=4, name="Diana", email=None, phone=None),
        ]
        session.add_all(users)
        session.commit()

        # Find users with NULL email
        users_null_email = session.execute(select(User).where(User.email.is_(None))).scalars().all()

        assert len(users_null_email) == 2
        assert all(u.email is None for u in users_null_email)
        assert any(u.name == "Charlie" for u in users_null_email)
        assert any(u.name == "Diana" for u in users_null_email)


def test_is_not_null(tmp_path: Path) -> None:
    """Test IS NOT NULL operator - find records where a column is NOT NULL."""
    path: Path = tmp_path / "test_is_not_null.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        users = [
            User(id=1, name="Alice", email="alice@example.com", phone="555-1234"),
            User(id=2, name="Bob", email="bob@example.com", phone=None),
            User(id=3, name="Charlie", email=None, phone="555-5678"),
            User(id=4, name="Diana", email=None, phone=None),
        ]
        session.add_all(users)
        session.commit()

        # Find users with non-NULL phone
        users_with_phone = session.execute(select(User).where(User.phone.isnot(None))).scalars().all()

        assert len(users_with_phone) == 2
        assert all(u.phone is not None for u in users_with_phone)
        assert any(u.name == "Alice" for u in users_with_phone)
        assert any(u.name == "Charlie" for u in users_with_phone)


def test_is_null_and_other_conditions(tmp_path: Path) -> None:
    """Test IS NULL combined with other WHERE conditions."""
    path: Path = tmp_path / "test_is_null_combined.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        users = [
            User(id=1, name="Alice", email="alice@example.com", phone="555-1234"),
            User(id=2, name="Bob", email="bob@example.com", phone=None),
            User(id=3, name="Charlie", email=None, phone="555-5678"),
            User(id=4, name="Diana", email=None, phone=None),
        ]
        session.add_all(users)
        session.commit()

        # Find users named 'Bob' with NULL phone
        result = session.execute(select(User).where((User.name == "Bob") & (User.phone.is_(None)))).scalars().all()

        assert len(result) == 1
        assert result[0].name == "Bob"
        assert result[0].phone is None


def test_is_not_null_or_conditions(tmp_path: Path) -> None:
    """Test IS NOT NULL with OR conditions."""
    path: Path = tmp_path / "test_is_not_null_or.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        users = [
            User(id=1, name="Alice", email="alice@example.com", phone="555-1234"),
            User(id=2, name="Bob", email="bob@example.com", phone=None),
            User(id=3, name="Charlie", email=None, phone="555-5678"),
            User(id=4, name="Diana", email=None, phone=None),
        ]
        session.add_all(users)
        session.commit()

        # Find users with either email OR phone (not both NULL)
        result: Sequence[User] = (
            session.execute(select(User).where((User.email.isnot(None)) | (User.phone.isnot(None)))).scalars().all()
        )

        assert len(result) == 3
        assert not any(u.email is None and u.phone is None for u in result)


def test_all_null(tmp_path: Path) -> None:
    """Test finding records where all optional columns are NULL."""
    path: Path = tmp_path / "test_all_null.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        users = [
            User(id=1, name="Alice", email="alice@example.com", phone="555-1234"),
            User(id=2, name="Bob", email="bob@example.com", phone=None),
            User(id=3, name="Charlie", email=None, phone="555-5678"),
            User(id=4, name="Diana", email=None, phone=None),
        ]
        session.add_all(users)
        session.commit()

        # Find users with both email AND phone NULL
        result: Sequence[User] = (
            session.execute(select(User).where((User.email.is_(None)) & (User.phone.is_(None)))).scalars().all()
        )

        assert len(result) == 1
        assert result[0].name == "Diana"
        assert result[0].email is None
        assert result[0].phone is None
