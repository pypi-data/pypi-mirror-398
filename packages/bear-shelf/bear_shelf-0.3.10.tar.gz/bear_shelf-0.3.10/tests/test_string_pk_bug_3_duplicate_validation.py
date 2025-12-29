"""Bug #3: No duplicate primary key validation.

HIGH PRIORITY BUG - Data integrity violation.

Location: src/bear_shelf/datastore/tables/data.py:224
Problem: No validation that primary key values are unique before insert
Impact: Duplicate PKs are silently allowed, violating data integrity

This test suite validates:
1. Duplicate string PKs are rejected with appropriate error
2. Duplicate integer PKs are rejected (regression)
3. Case-sensitive string PK uniqueness
4. Uniqueness across sessions/commits
5. Bulk insert with duplicates is rejected
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import Engine, Integer, String, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from bear_shelf.database import DatabaseManager


class Base(DeclarativeBase):
    """Base class for ORM models."""


class Product(Base):
    """Product with string PK."""

    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(50), primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[int] = mapped_column()


class Account(Base):
    """Account with UUID string PK."""

    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String(36), primary_key=True, autoincrement=False)
    username: Mapped[str] = mapped_column(String(50))


class User(Base):
    """User with integer PK."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50))


@pytest.fixture
def engine(tmp_path: Path) -> Engine:
    """Create engine connected to temporary database."""
    engine = create_engine(f"bearshelf:///{tmp_path / 'test_db.jsonl'}")
    Base.metadata.create_all(engine)
    return engine


class TestDuplicateStringPKValidation:
    """Test that duplicate string primary keys are properly rejected."""

    def test_duplicate_string_pk_same_session_raises_error(self, tmp_path: Path) -> None:
        """CORE TEST: Inserting duplicate string PK in same session should raise error.

        This is the main bug - no uniqueness validation on primary keys.
        Should raise IntegrityError or similar.
        """

        class ProductDB(DatabaseManager):
            """Base class for ORM models."""

        ProductBase = ProductDB.get_base()  # noqa: N806

        class Product(ProductBase):
            """Product with string PK."""

            __tablename__ = "products"

            sku: Mapped[str] = mapped_column(String(50), primary_key=True)
            name: Mapped[str] = mapped_column(String(100))
            price: Mapped[int] = mapped_column()

        db_path = tmp_path / "duplicate_pk_db.jsonl"

        db = ProductDB(path=str(db_path), schema="bearshelf")
        db.register_record(Product)
        db.create_tables()

        session = db.get_session()
        product1 = Product(sku="DUP-001", name="First", price=1000)
        session.add(product1)
        session.commit()
        product2 = Product(sku="DUP-001", name="Duplicate", price=2000)
        session.add(product2)
        with pytest.raises(ValueError, match="Duplicate primary key"):
            session.commit()

    def test_duplicate_string_pk_different_sessions_raises_error(self, engine: Engine) -> None:
        """Inserting duplicate string PK in different session should raise error."""
        # First session - insert original
        with Session(engine) as session:
            product = Product(sku="DUP-002", name="Original", price=500)
            session.add(product)
            session.commit()

        # Second session - try to insert duplicate
        with Session(engine) as session:
            duplicate = Product(sku="DUP-002", name="Duplicate", price=999)
            session.add(duplicate)

            with pytest.raises((IntegrityError, ValueError, RuntimeError)):
                session.commit()

    def test_duplicate_uuid_pk_raises_error(self, engine: Engine) -> None:
        """Duplicate UUID-style string PK should raise error."""
        uuid = "550e8400-e29b-41d4-a716-446655440000"

        with Session(engine) as session:
            account1 = Account(account_id=uuid, username="first")
            session.add(account1)
            session.commit()

            account2 = Account(account_id=uuid, username="duplicate")
            session.add(account2)

            with pytest.raises((IntegrityError, ValueError, RuntimeError)):
                session.commit()

    def test_case_sensitive_string_pk_uniqueness(self, engine: Engine) -> None:
        """String PKs should be case-sensitive (BEAR-001 != bear-001)."""
        with Session(engine) as session:
            product1 = Product(sku="BEAR-001", name="Uppercase", price=100)
            product2 = Product(sku="bear-001", name="Lowercase", price=200)

            session.add_all([product1, product2])
            session.commit()

            # Both should exist (different keys)
            all_products = session.execute(select(Product)).scalars().all()
            assert len(all_products) == 2

            sku = {p.sku for p in all_products}
            assert sku == {"BEAR-001", "bear-001"}

    def test_duplicate_in_bulk_insert_raises_error(self, engine: Engine) -> None:
        """Bulk insert with duplicate PKs should raise error."""
        with Session(engine) as session:
            products = [
                Product(sku="BULK-001", name="First", price=100),
                Product(sku="BULK-002", name="Second", price=200),
                Product(sku="BULK-001", name="Duplicate", price=300),  # Duplicate!
            ]

            session.add_all(products)

            with pytest.raises((IntegrityError, ValueError, RuntimeError)):
                session.commit()

    def test_duplicate_after_delete_allows_reinsert(self, engine: Engine) -> None:
        """After deleting a PK, the same value can be reused."""
        with Session(engine) as session:
            product = Product(sku="REUSE-001", name="Original", price=100)
            session.add(product)
            session.commit()

            # Delete it
            session.delete(product)
            session.commit()

        # Should be able to insert same PK again
        with Session(engine) as session:
            new_product = Product(sku="REUSE-001", name="New Product", price=200)
            session.add(new_product)
            session.commit()

            retrieved = session.execute(select(Product).where(Product.sku == "REUSE-001")).scalar_one()

            assert retrieved.name == "New Product"
            assert retrieved.price == 200

    def test_whitespace_in_string_pk_is_significant(self, engine: Engine) -> None:
        """Whitespace should be significant in string PKs."""
        with Session(engine) as session:
            product1 = Product(sku="TEST", name="No space", price=100)
            product2 = Product(sku="TEST ", name="Trailing space", price=200)
            product3 = Product(sku=" TEST", name="Leading space", price=300)

            session.add_all([product1, product2, product3])
            session.commit()

            # All three should exist (different keys)
            all_products = session.execute(select(Product)).scalars().all()
            assert len(all_products) == 3

    def test_empty_string_pk_uniqueness(self, engine: Engine) -> None:
        """Empty string as PK should be unique (only one allowed)."""
        with Session(engine) as session:
            product1 = Product(sku="", name="Empty PK 1", price=100)
            session.add(product1)
            session.commit()

            # Try to add another with empty string PK
            product2 = Product(sku="", name="Empty PK 2", price=200)
            session.add(product2)

            with pytest.raises((IntegrityError, ValueError, RuntimeError)):
                session.commit()


class TestRegressionIntegerPKUniqueness:
    """Regression tests to ensure integer PK uniqueness still works."""

    def test_duplicate_integer_pk_raises_error(self, engine: Engine) -> None:
        """Duplicate integer PK should raise error (regression test)."""
        with Session(engine) as session:
            user1 = User(id=1, username="first")
            session.add(user1)
            session.commit()

            user2 = User(id=1, username="duplicate")
            session.add(user2)

            with pytest.raises(ValueError, match="Duplicate primary key"):
                session.commit()

    def test_auto_generated_pks_are_unique(self, engine: Engine) -> None:
        """Auto-generated integer PKs should never duplicate."""
        with Session(engine) as session:
            users = [User(username=f"user{i}") for i in range(10)]
            session.add_all(users)
            session.commit()

            # All IDs should be unique
            ids = [u.id for u in users]
            assert len(ids) == len(set(ids))

    def test_explicit_integer_pk_after_auto_raises_on_duplicate(self, engine: Engine) -> None:
        """Explicitly setting an integer PK that was auto-generated should fail."""
        with Session(engine) as session:
            user1 = User(username="auto")
            session.add(user1)
            session.commit()

            auto_id = user1.id

            # Try to manually insert with same ID
            user2 = User(id=auto_id, username="manual")
            session.add(user2)

            with pytest.raises(ValueError, match="Duplicate primary key"):
                session.commit()


class TestPKUniquenessEdgeCases:
    """Edge cases for PK uniqueness validation."""

    def test_very_long_string_pk_uniqueness(self, engine: Engine) -> None:
        """Very long string PKs should still enforce uniqueness."""
        long_key = "A" * 50  # Max length for our String(50)

        with Session(engine) as session:
            product1 = Product(sku=long_key, name="First", price=100)
            session.add(product1)
            session.commit()

            product2 = Product(sku=long_key, name="Duplicate", price=200)
            session.add(product2)

            with pytest.raises((IntegrityError, ValueError, RuntimeError)):
                session.commit()

    def test_special_characters_string_pk_uniqueness(self, engine: Engine) -> None:
        """Special characters in string PKs should still enforce uniqueness."""
        special_key = "TEST@#$%^&*()"

        with Session(engine) as session:
            product1 = Product(sku=special_key, name="First", price=100)
            session.add(product1)
            session.commit()

            product2 = Product(sku=special_key, name="Duplicate", price=200)
            session.add(product2)

            with pytest.raises((IntegrityError, ValueError, RuntimeError)):
                session.commit()

    def test_unicode_string_pk_uniqueness(self, engine: Engine) -> None:
        """Unicode characters in string PKs should enforce uniqueness."""
        unicode_key = "熊-001"  # Bear in Chinese + SKU

        with Session(engine) as session:
            product1 = Product(sku=unicode_key, name="First", price=100)
            session.add(product1)
            session.commit()

            product2 = Product(sku=unicode_key, name="Duplicate", price=200)
            session.add(product2)

            with pytest.raises((IntegrityError, ValueError, RuntimeError)):
                session.commit()
