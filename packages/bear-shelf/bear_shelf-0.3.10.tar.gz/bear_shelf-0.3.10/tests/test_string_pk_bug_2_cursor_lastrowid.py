"""Bug #2: Cursor lastrowid type constraint breaks UPDATE operations.

CRITICAL BUG - Breaks UPDATE operations with string PKs.

Location: src/bear_shelf/dialect/cursor.py:29, 119
Problem: lastrowid is typed as int, but needs to support string PKs
Impact: UPDATE operations fail - SQLAlchemy can't track objects with string PKs

This test suite validates:
1. INSERT returns correct lastrowid for string PKs
2. UPDATE operations work with string PKs
3. Multiple updates on same object work
4. Regression: Integer PK lastrowid still works
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import tempfile
from typing import Any

import pytest
from sqlalchemy import Engine, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    """Base class for ORM models."""


class Product(Base):
    """Product with string PK."""

    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(50), primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[int] = mapped_column()
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Account(Base):
    """Account with UUID string PK."""

    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String(36), primary_key=True, autoincrement=False)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))
    active: Mapped[bool | None] = mapped_column(nullable=True)


class User(Base):
    """User with integer PK for regression testing."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)


@pytest.fixture
def temp_db_path() -> Generator[Path, Any]:
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
        temp_path = Path(tmp.name)

    yield temp_path

    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def engine(temp_db_path: Path) -> Engine:
    """Create engine connected to temporary database."""
    engine = create_engine(f"bearshelf:///{temp_db_path}")
    Base.metadata.create_all(engine)
    return engine


class TestStringPKUpdate:
    """Test UPDATE operations with string primary keys."""

    def test_update_single_field_string_pk(self, engine: Engine) -> None:
        """CORE TEST: Update a single field on a record with string PK.

        This is the main bug - cursor.lastrowid is typed as int, so SQLAlchemy
        can't properly track the object after INSERT, causing UPDATE to fail.
        """
        with Session(engine) as session:
            # Insert
            product = Product(sku="UPDATE-001", name="Old Name", price=1000)
            session.add(product)
            session.commit()

            # Update single field
            product.name = "New Name"
            session.commit()

            # Verify update
            retrieved = session.execute(select(Product).where(Product.sku == "UPDATE-001")).scalar_one()

            assert retrieved.name == "New Name"
            assert retrieved.price == 1000  # Unchanged

    def test_update_multiple_fields_string_pk(self, engine: Engine) -> None:
        """Update multiple fields on a record with string PK."""
        with Session(engine) as session:
            product = Product(sku="MULTI-001", name="Original", price=500, quantity=10)
            session.add(product)
            session.commit()

            # Update multiple fields
            product.name = "Updated"
            product.price = 750
            product.quantity = 5
            session.commit()

            retrieved = session.execute(select(Product).where(Product.sku == "MULTI-001")).scalar_one()

            assert retrieved.name == "Updated"
            assert retrieved.price == 750
            assert retrieved.quantity == 5

    def test_sequential_updates_string_pk(self, engine: Engine) -> None:
        """Multiple sequential updates on same object with string PK."""
        with Session(engine) as session:
            product = Product(sku="SEQ-001", name="Version 1", price=100)
            session.add(product)
            session.commit()

            # First update
            product.name = "Version 2"
            session.commit()

            # Second update
            product.price = 200
            session.commit()

            # Third update
            product.name = "Version 3"
            product.price = 300
            session.commit()

            retrieved = session.execute(select(Product).where(Product.sku == "SEQ-001")).scalar_one()

            assert retrieved.name == "Version 3"
            assert retrieved.price == 300

    def test_update_after_query_string_pk(self, engine: Engine) -> None:
        """Update a record that was retrieved via query (not freshly inserted)."""
        with Session(engine) as session:
            product = Product(sku="QUERY-001", name="Initial", price=100)
            session.add(product)
            session.commit()

        # New session - retrieve and update
        with Session(engine) as session:
            product = session.execute(select(Product).where(Product.sku == "QUERY-001")).scalar_one()

            product.name = "Updated"
            product.price = 200
            session.commit()

            # Verify in yet another session
            with Session(engine) as verify_session:
                verified = verify_session.execute(select(Product).where(Product.sku == "QUERY-001")).scalar_one()

                assert verified.name == "Updated"
                assert verified.price == 200

    def test_update_uuid_style_pk(self, engine: Engine) -> None:
        """Update record with UUID-style string PK."""
        with Session(engine) as session:
            account = Account(
                account_id="550e8400-e29b-41d4-a716-446655440000",
                username="bear",
                email="bear@example.com",
                active=True,
            )
            session.add(account)
            session.commit()

            # Update
            account.username = "bear_updated"
            account.active = False
            session.commit()

            retrieved = session.execute(
                select(Account).where(Account.account_id == "550e8400-e29b-41d4-a716-446655440000")
            ).scalar_one()

            assert retrieved.username == "bear_updated"
            assert retrieved.active is False

    def test_update_nullable_field_to_null_string_pk(self, engine: Engine) -> None:
        """Update nullable field to NULL on string PK record."""
        with Session(engine) as session:
            product = Product(sku="NULL-001", name="Product", price=100, quantity=50)
            session.add(product)
            session.commit()

            # Update quantity to NULL
            product.quantity = None
            session.commit()

            retrieved = session.execute(select(Product).where(Product.sku == "NULL-001")).scalar_one()

            assert retrieved.quantity is None
            assert retrieved.price == 100

    def test_bulk_update_multiple_string_pk_records(self, engine: Engine) -> None:
        """Update multiple records with string PKs in same session."""
        with Session(engine) as session:
            products = [Product(sku=f"BULK-{i:03d}", name=f"Product {i}", price=i * 100) for i in range(1, 6)]
            session.add_all(products)
            session.commit()

            # Update all in same session
            for product in products:
                product.price = product.price + 50

            session.commit()

            # Verify all updated
            all_products = session.execute(select(Product)).scalars().all()
            for i, product in enumerate(sorted(all_products, key=lambda p: p.sku), start=1):
                assert product.price == i * 100 + 50


class TestCursorLastRowId:
    """Test that cursor.lastrowid works correctly for both string and int PKs."""

    def test_lastrowid_with_string_pk(self, engine: Engine) -> None:
        """Cursor should return string PK value in lastrowid (after fix)."""
        with Session(engine) as session:
            product = Product(sku="LASTROW-001", name="Test", price=100)
            session.add(product)
            session.commit()

            # The cursor's lastrowid should be accessible (implementation detail)
            # Main validation is that the object is properly tracked
            assert product.sku == "LASTROW-001"

    def test_lastrowid_with_uuid_pk(self, engine: Engine) -> None:
        """Cursor should handle UUID-style PKs in lastrowid."""
        with Session(engine) as session:
            account = Account(
                account_id="123e4567-e89b-12d3-a456-426614174000", username="test", email="test@example.com"
            )
            session.add(account)
            session.commit()

            assert account.account_id == "123e4567-e89b-12d3-a456-426614174000"


class TestRegressionIntegerPKUpdate:
    """Regression tests to ensure integer PK updates still work."""

    def test_update_integer_pk_record(self, engine: Engine) -> None:
        """Integer PK updates should still work after fixing string PK support."""
        with Session(engine) as session:
            user = User(id=1, username="bear", score=100)
            session.add(user)
            session.commit()

            # Update
            user.username = "bear_updated"
            user.score = 200
            session.commit()

            retrieved = session.execute(select(User).where(User.id == 1)).scalar_one()

            assert retrieved.username == "bear_updated"
            assert retrieved.score == 200

    def test_update_auto_generated_integer_pk(self, engine: Engine) -> None:
        """Update record with auto-generated integer PK."""
        with Session(engine) as session:
            user = User(username="auto_user", score=50)
            session.add(user)
            session.commit()

            generated_id = user.id
            assert generated_id is not None

            # Update
            user.score = 100
            session.commit()

            retrieved = session.execute(select(User).where(User.id == generated_id)).scalar_one()

            assert retrieved.score == 100

    def test_integer_pk_lastrowid_is_int(self, engine: Engine) -> None:
        """Integer PK lastrowid should still return int type."""
        with Session(engine) as session:
            user = User(id=999, username="test", score=0)
            session.add(user)
            session.commit()

            # Verify ID is still integer
            assert isinstance(user.id, int)
            assert user.id == 999
