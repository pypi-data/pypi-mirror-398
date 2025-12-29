"""TDD tests for string-based primary key support."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import Engine, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class ProductBase(DeclarativeBase):
    """Base class for product model."""


class Product(ProductBase):
    """Product with string PK."""

    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[int] = mapped_column()


@pytest.fixture
def temp_engine(bearshelf_path: str) -> Generator[Engine, Any]:
    """Provide a temporary SQLAlchemy engine connected to BearShelf."""
    engine: Engine = create_engine(bearshelf_path)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def temp_session_db(temp_engine: Engine) -> Generator[sessionmaker, Any]:
    """Test creating a table with string primary key."""
    ProductBase.metadata.create_all(temp_engine)
    try:
        yield sessionmaker(bind=temp_engine)
    finally:
        ProductBase.metadata.drop_all(temp_engine)


class TestStringPrimaryKey:
    """Test string-based primary key operations."""

    def test_create_table_with_string_pk(self, temp_session_db: sessionmaker) -> None:
        """Test creating a table with string primary key."""
        with temp_session_db() as session:
            # Verify table exists by inserting a record
            new_product = Product(sku="TEST-001", name="Test Product", price=1000)
            session.add(new_product)
            session.commit()

            # Query back to verify insertion
            retrieved = session.execute(select(Product).where(Product.sku == "TEST-001")).scalar_one()

            assert retrieved.sku == "TEST-001"
            assert retrieved.name == "Test Product"
            assert retrieved.price == 1000

    def test_insert_single_record_with_string_pk(self, temp_session_db: sessionmaker) -> None:
        """Test inserting a single record with string primary key."""
        with temp_session_db() as session:
            # Insert a product with string SKU
            product = Product(sku="BEAR-001", name="Bear Plushie", price=2999)
            session.add(product)
            session.commit()

            # Verify it was inserted
            retrieved = session.execute(select(Product).where(Product.sku == "BEAR-001")).scalar_one()

            assert retrieved.sku == "BEAR-001"
            assert retrieved.name == "Bear Plushie"
            assert retrieved.price == 2999

    def test_insert_multiple_records_with_string_pk(self, temp_session_db: sessionmaker) -> None:
        """Test inserting multiple records with string primary keys."""
        with temp_session_db() as session:
            products: list[Product] = [
                Product(sku="BEAR-001", name="Bear Plushie", price=2999),
                Product(sku="BEAR-002", name="Giant Bear", price=4999),
                Product(sku="PANDA-001", name="Panda Plushie", price=3499),
            ]
            session.add_all(products)
            session.commit()

            # Verify all were inserted
            all_products = session.execute(select(Product)).scalars().all()
            assert len(all_products) == 3

            sku = {p.sku for p in all_products}
            assert sku == {"BEAR-001", "BEAR-002", "PANDA-001"}

    def test_query_by_string_pk(self, temp_session_db: sessionmaker) -> None:
        """Test querying records by string primary key."""
        with temp_session_db() as session:
            # Insert some test data
            session.add_all(
                [
                    Product(sku="SKU-A", name="Product A", price=1000),
                    Product(sku="SKU-B", name="Product B", price=2000),
                    Product(sku="SKU-C", name="Product C", price=3000),
                ]
            )
            session.commit()

            # Query by specific PK
            product_b = session.execute(select(Product).where(Product.sku == "SKU-B")).scalar_one()

            assert product_b.name == "Product B"
            assert product_b.price == 2000

    def test_update_record_with_string_pk(self, temp_session_db: sessionmaker) -> None:
        """Test updating a record identified by string primary key."""
        with temp_session_db() as session:
            # Insert initial record
            product = Product(sku="UPDATE-001", name="Old Name", price=1000)
            session.add(product)
            session.commit()

            # Update the record
            product.name = "New Name"
            product.price = 1500
            session.commit()

            # Verify update
            updated = session.execute(select(Product).where(Product.sku == "UPDATE-001")).scalar_one()

            assert updated.name == "New Name"
            assert updated.price == 1500

    def test_delete_record_with_string_pk(self, temp_session_db: sessionmaker) -> None:
        """Test deleting a record identified by string primary key."""
        with temp_session_db() as session:
            # Insert record
            product = Product(sku="DELETE-001", name="To Be Deleted", price=999)
            session.add(product)
            session.commit()

            # Delete it
            session.delete(product)
            session.commit()

            # Verify deletion
            result = session.execute(select(Product).where(Product.sku == "DELETE-001")).scalar_one_or_none()

            assert result is None

    def test_string_pk_persists_across_sessions(self, temp_session_db: sessionmaker) -> None:
        """Test that string PKs persist correctly when reopening database."""
        # Insert in first session
        with temp_session_db() as session:
            product = Product(sku="PERSIST-001", name="Persistent Product", price=5000)
            session.add(product)
            session.commit()

        # Verify in new session
        with temp_session_db() as session:
            retrieved = session.execute(select(Product).where(Product.sku == "PERSIST-001")).scalar_one()

            assert retrieved.name == "Persistent Product"
            assert retrieved.price == 5000

    def test_special_characters_in_string_pk(self, temp_session_db: sessionmaker) -> None:
        """Test string PKs with special characters."""
        with temp_session_db() as session:
            # Insert products with special characters in SKU
            products: list[Product] = [
                Product(sku="BEAR@001", name="Bear with @", price=1000),
                Product(sku="BEAR-001-A", name="Bear with dashes", price=2000),
                Product(sku="BEAR_001_B", name="Bear with underscores", price=3000),
            ]
            session.add_all(products)
            session.commit()

            # Verify all can be retrieved
            bear_at = session.execute(select(Product).where(Product.sku == "BEAR@001")).scalar_one()
            assert bear_at.name == "Bear with @"

            bear_dash = session.execute(select(Product).where(Product.sku == "BEAR-001-A")).scalar_one()
            assert bear_dash.name == "Bear with dashes"

    def test_alphanumeric_ordering_string_pk(self, temp_session_db: sessionmaker) -> None:
        """Test that string PKs can be inserted in any order."""
        with temp_session_db() as session:
            # Insert in non-alphabetical order
            products = [
                Product(sku="GAMMA", name="Third", price=300),
                Product(sku="ALPHA", name="First", price=100),
                Product(sku="BETA", name="Second", price=200),
            ]
            session.add_all(products)
            session.commit()

            # Verify all exist
            all_products = session.execute(select(Product)).scalars().all()
            assert len(all_products) == 3

            # Get them by PK to verify no ordering issues
            alpha = session.execute(select(Product).where(Product.sku == "ALPHA")).scalar_one()
            assert alpha.name == "First"

    def test_duplicate_string_pk_raises_error(self, temp_session_db: sessionmaker) -> None:
        """Test that duplicate string PKs are rejected."""
        with temp_session_db() as session:
            # Insert first product
            product1 = Product(sku="DUP-001", name="First", price=1000)
            session.add(product1)
            session.commit()

            # Try to insert duplicate
            product2 = Product(sku="DUP-001", name="Duplicate", price=2000)
            session.add(product2)

            with pytest.raises(ValueError, match="Duplicate primary key"):
                session.commit()
