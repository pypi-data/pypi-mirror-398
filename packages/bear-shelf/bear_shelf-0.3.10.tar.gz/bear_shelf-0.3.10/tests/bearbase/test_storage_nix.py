"""Test Nix storage backend with comprehensive round-trip tests."""

from pathlib import Path

import pytest
from sqlalchemy import Boolean, Engine, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeMeta, Mapped, Session, mapped_column

from bear_shelf.database import BearShelfDB

BearShelfDB.clear_base()
Base: DeclarativeMeta = BearShelfDB.get_base()


class User(Base):
    """User model for testing."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)


class Product(Base):
    """Product model for testing multiple tables."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Float)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Create a temporary database path for testing."""
    return tmp_path / "test_database.nix"


def test_nix_storage_create(temp_db_path: Path) -> None:
    """Test creating a Nix database and writing data."""
    engine: Engine = create_engine(f"bearshelf:///{temp_db_path}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        users: list[User] = [
            User(id=1, name="Bear", email="bear@example.com", is_active=True, score=95.5),
            User(id=2, name="Claire", email="claire@example.com", is_active=True, score=98.2),
            User(id=3, name="Shannon", email="shannon@example.com", is_active=False, score=92.0),
        ]
        session.add_all(users)
        session.commit()

    assert temp_db_path.exists(), "Nix database file was not created"


def test_nix_storage_read(temp_db_path: Path) -> None:
    """Test reading data from a Nix database."""
    engine: Engine = create_engine(f"bearshelf:///{temp_db_path}")
    Base.metadata.create_all(engine)

    # Write test data
    with Session(engine) as session:
        users = [
            User(id=1, name="Bear", email="bear@example.com", is_active=True, score=95.5),
            User(id=2, name="Claire", email="claire@example.com", is_active=True, score=98.2),
        ]
        session.add_all(users)
        session.commit()

    # Read and verify
    with Session(engine) as session:
        result: User | None = session.query(User).filter_by(name="Bear").first()
        assert result is not None
        assert result.email == "bear@example.com"
        assert result.is_active is True
        assert result.score == 95.5


def test_nix_storage_round_trip(temp_db_path: Path) -> None:
    """Test complete round-trip: write, read, modify, read again."""
    engine: Engine = create_engine(f"bearshelf:///{temp_db_path}")
    Base.metadata.create_all(engine)

    # Initial write
    with Session(engine) as session:
        user = User(id=1, name="Bear", email="bear@example.com", is_active=True, score=85.0)
        session.add(user)
        session.commit()

    # Read and modify
    with Session(engine) as session:
        user: User | None = session.query(User).filter_by(id=1).first()
        assert user is not None
        assert user.score == 85.0

        user.score = 95.5
        user.is_active = False
        session.commit()

    # Verify modifications persisted
    with Session(engine) as session:
        user: User | None = session.query(User).filter_by(id=1).first()
        assert user is not None
        assert user.score == 95.5
        assert user.is_active is False


def test_nix_storage_multiple_tables(temp_db_path: Path) -> None:
    """Test Nix storage with multiple tables."""
    engine: Engine = create_engine(f"bearshelf:///{temp_db_path}")
    Base.metadata.create_all(engine)

    # Add data to both tables
    with Session(engine) as session:
        users = [
            User(id=1, name="Bear", email="bear@example.com", is_active=True, score=95.5),
            User(id=2, name="Claire", email="claire@example.com", is_active=True, score=98.2),
        ]
        products = [
            Product(id=1, name="Widget", price=19.99, in_stock=True),
            Product(id=2, name="Gadget", price=29.99, in_stock=False),
            Product(id=3, name="Doohickey", price=9.99, in_stock=True),
        ]
        session.add_all(users)
        session.add_all(products)
        session.commit()

    # Verify both tables
    with Session(engine) as session:
        users: list[User] = session.query(User).all()
        products: list[Product] = session.query(Product).all()

        assert len(users) == 2
        assert len(products) == 3

        user_names: set[str] = {user.name for user in users}
        assert user_names == {"Bear", "Claire"}

        in_stock_products: list[Product] = session.query(Product).filter_by(in_stock=True).all()
        assert len(in_stock_products) == 2


def test_nix_storage_empty_table(temp_db_path: Path) -> None:
    """Test Nix storage with an empty table."""
    engine: Engine = create_engine(f"bearshelf:///{temp_db_path}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        users: list[User] = session.query(User).all()
        assert len(users) == 0


def test_nix_storage_update_operations(temp_db_path: Path) -> None:
    """Test various update operations on Nix storage."""
    engine: Engine = create_engine(f"bearshelf:///{temp_db_path}")
    Base.metadata.create_all(engine)

    # Initial data
    with Session(engine) as session:
        users = [
            User(id=1, name="Bear", email="bear@example.com", is_active=True, score=80.0),
            User(id=2, name="Claire", email="claire@example.com", is_active=True, score=90.0),
            User(id=3, name="Shannon", email="shannon@example.com", is_active=False, score=70.0),
        ]
        session.add_all(users)
        session.commit()

    # Bulk update
    with Session(engine) as session:
        session.query(User).filter(User.is_active == True).update({"score": 100.0})  # noqa: E712
        session.commit()

    # Verify bulk update
    with Session(engine) as session:
        active_users: list[User] = session.query(User).filter_by(is_active=True).all()
        for user in active_users:
            assert user.score == 100.0

        inactive_user: User | None = session.query(User).filter_by(is_active=False).first()
        assert inactive_user is not None
        assert inactive_user.score == 70.0  # Should not have changed


def test_nix_storage_delete_operations(temp_db_path: Path) -> None:
    """Test delete operations on Nix storage."""
    engine: Engine = create_engine(f"bearshelf:///{temp_db_path}")
    Base.metadata.create_all(engine)

    # Initial data
    with Session(engine) as session:
        users = [
            User(id=1, name="Bear", email="bear@example.com", is_active=True, score=80.0),
            User(id=2, name="Claire", email="claire@example.com", is_active=True, score=90.0),
            User(id=3, name="Shannon", email="shannon@example.com", is_active=False, score=70.0),
        ]
        session.add_all(users)
        session.commit()

    # Delete one user
    with Session(engine) as session:
        user: User | None = session.query(User).filter_by(name="Shannon").first()
        assert user is not None
        session.delete(user)
        session.commit()

    # Verify deletion
    with Session(engine) as session:
        users: list[User] = session.query(User).all()
        assert len(users) == 2
        names: set[str] = {user.name for user in users}
        assert "Shannon" not in names


def test_nix_storage_special_values(temp_db_path: Path) -> None:
    """Test Nix storage handles special values correctly."""
    db: BearShelfDB = BearShelfDB(
        path=str(temp_db_path),
        schema="bearshelf",
        engine_create=True,
        echo=False,
        tables_create=True,
        long_lived=True,
    )

    with db.open_session() as session:
        users: list[User] = [
            User(name="Empty Score", email="test1@example.com", is_active=True, score=0.0),
            User(name="Negative Score", email="test2@example.com", is_active=False, score=-5.5),
            User(name="Large Score", email="test3@example.com", is_active=True, score=999.999),
        ]
        session.add_all(users)

    with db.open_session() as session:
        users: list[User] = session.query(User).order_by(User.id).all()
        assert len(users) == 3
        assert users[0].score == 0.0
        assert users[1].score == -5.5
        assert users[2].score == 999.999
    db.close()


def test_nix_file_content_is_valid(temp_db_path: Path) -> None:
    """Test that the Nix file content is valid Nix syntax."""
    engine: Engine = create_engine(f"bearshelf:///{temp_db_path}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(id=1, name="Bear", email="bear@example.com", is_active=True, score=95.5)
        session.add(user)
        session.commit()

    # Read the raw file content
    content: str = temp_db_path.read_text()

    # Basic checks for Nix syntax
    assert "{" in content
    assert "}" in content
    assert "=" in content
    assert "users" in content  # Table name should be in the file

    # Should not have Python-specific syntax
    assert "None" not in content  # Python None should be converted to null
    assert "True" not in content  # Python True should be converted to true
    assert "False" not in content  # Python False should be converted to false
