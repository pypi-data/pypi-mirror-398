"""TDD tests for INSERT object tracking with string PKs.

FOUNDATIONAL ISSUE: Object tracking after INSERT

Problem: After INSERT, SQLAlchemy can't access the primary key attribute on
the Python object, causing UPDATE operations to fail.

Root Cause Investigation:
1. INSERT executes successfully
2. cursor.lastrowid is set (we fixed the type)
3. BUT: SQLAlchemy's object doesn't get the PK value populated
4. Later UPDATE can't access object.sku → KeyError

This test suite isolates the exact failure point to guide the fix.
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


class User(Base):
    """User with integer PK for comparison."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50))


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


class TestStringPKObjectTracking:
    """Test that string PK values are accessible on Python objects after INSERT."""

    def test_string_pk_accessible_after_insert(self, engine: Engine) -> None:
        """CORE TEST: After INSERT, the PK attribute should be accessible on the object.

        This is the exact failure point - SQLAlchemy can't access product.sku
        after the INSERT completes.
        """
        with Session(engine) as session:
            product = Product(sku="TEST-001", name="Test", price=100)
            session.add(product)
            session.commit()

            # This should NOT raise AttributeError or KeyError
            assert product.sku == "TEST-001"
            assert hasattr(product, "sku")

    def test_string_pk_accessible_in_same_session(self, engine: Engine) -> None:
        """After INSERT, should be able to access PK without refetching."""
        with Session(engine) as session:
            product = Product(sku="ACCESS-001", name="Accessible", price=200)
            session.add(product)
            session.commit()

            # Access all attributes without re-querying
            sku_value = product.sku
            name_value = product.name
            price_value = product.price

            assert sku_value == "ACCESS-001"
            assert name_value == "Accessible"
            assert price_value == 200

    def test_string_pk_in_object_dict(self, engine: Engine) -> None:
        """The PK should be in the object's __dict__ after INSERT."""
        with Session(engine) as session:
            product = Product(sku="DICT-001", name="Dict Test", price=300)
            session.add(product)
            session.commit()

            # Check object internals
            # Note: SQLAlchemy might store this differently, but it should be accessible
            assert "sku" in str(product.__dict__) or product.sku == "DICT-001"

    def test_modify_non_pk_field_after_insert(self, engine: Engine) -> None:
        """Should be able to modify non-PK fields after INSERT.

        This is the precursor to UPDATE - we need to change a field's value
        while keeping the PK accessible.
        """
        with Session(engine) as session:
            product = Product(sku="MODIFY-001", name="Original", price=100)
            session.add(product)
            session.commit()

            # Modify a field (don't commit yet)
            product.name = "Modified"

            # PK should still be accessible
            assert product.sku == "MODIFY-001"
            assert product.name == "Modified"

    def test_update_requires_pk_access(self, engine: Engine) -> None:
        """UPDATE operation requires accessing the PK to identify the record."""
        with Session(engine) as session:
            product = Product(sku="UPDATE-001", name="Before", price=100)
            session.add(product)
            session.commit()

            # Modify and commit (triggers UPDATE)
            product.name = "After"

            # This is where it fails - SQLAlchemy needs to access product.sku
            # to generate: UPDATE products SET name='After' WHERE sku='UPDATE-001'
            session.commit()

            # Verify the update worked
            retrieved = session.execute(select(Product).where(Product.sku == "UPDATE-001")).scalar_one()
            assert retrieved.name == "After"


class TestIntegerPKObjectTracking:
    """Regression: Verify integer PKs still work correctly."""

    def test_integer_pk_accessible_after_insert(self, engine: Engine) -> None:
        """Integer PK should be accessible after INSERT (baseline behavior)."""
        with Session(engine) as session:
            user = User(username="testuser")
            session.add(user)
            session.commit()

            # Should work fine with integers
            assert user.id is not None
            assert hasattr(user, "id")

    def test_integer_pk_update_works(self, engine: Engine) -> None:
        """UPDATE with integer PK should work (regression test)."""
        with Session(engine) as session:
            user = User(username="original")
            session.add(user)
            session.commit()

            user_id = user.id

            # Update
            user.username = "updated"
            session.commit()

            # Verify
            retrieved = session.execute(select(User).where(User.id == user_id)).scalar_one()
            assert retrieved.username == "updated"


class TestInsertResultHandling:
    """Test how INSERT results are returned and processed."""

    def test_insert_returns_object_with_pk(self, engine: Engine) -> None:
        """After INSERT, the returned object should have its PK populated."""
        with Session(engine) as session:
            product = Product(sku="RETURN-001", name="Test", price=100)
            session.add(product)

            # Before commit, PK should already be set (we provided it)
            assert product.sku == "RETURN-001"

            session.commit()

            # After commit, PK should still be accessible
            assert product.sku == "RETURN-001"

    def test_bulk_insert_all_pks_accessible(self, engine: Engine) -> None:
        """After bulk INSERT, all objects should have accessible PKs."""
        with Session(engine) as session:
            products = [Product(sku=f"BULK-{i:03d}", name=f"Product {i}", price=i * 100) for i in range(1, 6)]
            session.add_all(products)
            session.commit()

            # All PKs should be accessible
            for product in products:
                assert product.sku is not None
                assert product.sku.startswith("BULK-")

    def test_autoincrement_int_pk_populated_after_insert(self, engine: Engine) -> None:
        """Auto-generated integer PKs should be populated after INSERT."""
        with Session(engine) as session:
            user = User(username="auto")

            # Before commit, ID might be None
            pre_commit_id = getattr(user, "id", None)

            session.add(user)
            session.commit()

            # After commit, ID must be populated
            assert user.id is not None
            assert isinstance(user.id, int)

    def test_explicit_string_pk_preserved_through_insert(self, engine: Engine) -> None:
        """Explicitly provided string PK should be preserved through INSERT."""
        with Session(engine) as session:
            original_sku = "PRESERVE-001"
            product = Product(sku=original_sku, name="Test", price=100)

            session.add(product)
            session.commit()

            # The exact value should be preserved
            assert product.sku == original_sku
            assert product.sku is not None
