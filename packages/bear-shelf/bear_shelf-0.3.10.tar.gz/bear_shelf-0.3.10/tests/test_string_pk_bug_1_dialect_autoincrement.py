"""Bug #1: Dialect autoincrement detection for string primary keys.

FOUNDATIONAL BUG - Blocks table creation with string PKs.

Location: src/bear_shelf/dialect/bear_dialect.py:167
Problem: Treats SQLAlchemy's 'auto' as True without checking column type
Impact: String PK tables cannot be created without explicit autoincrement=False

This test suite validates:
1. String PKs work WITHOUT explicit autoincrement=False (after fix)
2. Integer PKs still auto-detect autoincrement correctly
3. Explicit autoincrement=True on string PKs is rejected
4. Various string PK types (UUID, email, SKU) all work
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import Engine, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    """Base class for ORM models."""


class ProductNoAutoincrement(Base):
    """Product with string PK - NO explicit autoincrement setting."""

    __tablename__ = "products_no_autoinc"

    sku: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[int] = mapped_column()


class UserWithIntPK(Base):
    """User with integer PK - should auto-detect autoincrement."""

    __tablename__ = "users_int_pk"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))


class AccountUUID(Base):
    """Account with UUID-style string PK."""

    __tablename__ = "accounts_uuid"

    account_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(50))


class EmailPrimaryKey(Base):
    """Model using email as primary key."""

    __tablename__ = "email_pk"

    email: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


@pytest.fixture
def temp_engine(bearshelf_path: str) -> Generator[Engine, Any]:
    """Provide a temporary SQLAlchemy engine connected to BearShelf."""
    engine: Engine = create_engine(bearshelf_path)
    try:
        yield engine
    finally:
        engine.dispose()


class TestDialectAutoincrementDetection:
    """Test that dialect correctly detects when to enable autoincrement."""

    def test_string_pk_without_explicit_autoincrement_false(self, bearshelf_path: str) -> None:
        """CORE TEST: String PK should work without explicit autoincrement=False.

        This is the main bug - SQLAlchemy sets autoincrement='auto' on all PKs,
        but Bear Shelf should only treat it as True for INTEGER columns.
        """
        engine = create_engine(bearshelf_path)

        Base.metadata.create_all(engine, tables=[ProductNoAutoincrement.__table__])  # pyright: ignore[reportArgumentType]

        temp_session_db = sessionmaker(bind=engine)

        with temp_session_db() as session:
            product = ProductNoAutoincrement(sku="TEST-001", name="Test Product", price=1000)
            session.add(product)
            session.commit()

            # Verify it was inserted
            retrieved = session.execute(
                select(ProductNoAutoincrement).where(ProductNoAutoincrement.sku == "TEST-001")
            ).scalar_one()

            assert retrieved.name == "Test Product"
            assert retrieved.price == 1000

    def test_integer_pk_auto_detects_autoincrement(self, temp_engine: Engine) -> None:
        """Integer PK should automatically enable autoincrement."""
        Base.metadata.create_all(temp_engine, tables=[UserWithIntPK.__table__])  # pyright: ignore[reportArgumentType]
        temp_session_db = sessionmaker(bind=temp_engine)
        with temp_session_db() as session:
            # Insert WITHOUT specifying ID - should auto-generate
            user1 = UserWithIntPK(username="bear", email="bear@example.com")
            user2 = UserWithIntPK(username="claire", email="claire@example.com")

            session.add_all([user1, user2])
            session.commit()

            # IDs should be auto-generated
            assert user1.id is not None
            assert user2.id is not None
            assert user1.id != user2.id
        Base.metadata.drop_all(temp_engine, tables=[UserWithIntPK.__table__])  # pyright: ignore[reportArgumentType]

    def test_uuid_style_string_pk(self, temp_engine: Engine) -> None:
        """UUID-style string PKs should work without explicit autoincrement setting."""
        Base.metadata.create_all(temp_engine, tables=[AccountUUID.__table__])  # pyright: ignore[reportArgumentType]
        temp_session_db = sessionmaker(bind=temp_engine)

        with temp_session_db() as session:
            account = AccountUUID(account_id="550e8400-e29b-41d4-a716-446655440000", username="bear")
            session.add(account)
            session.commit()

            retrieved = session.execute(
                select(AccountUUID).where(AccountUUID.account_id == "550e8400-e29b-41d4-a716-446655440000")
            ).scalar_one()

            assert retrieved.username == "bear"
        Base.metadata.drop_all(temp_engine, tables=[AccountUUID.__table__])  # pyright: ignore[reportArgumentType]

    def test_email_as_primary_key(self, temp_engine: Engine) -> None:
        """Email addresses should work as primary keys."""
        Base.metadata.create_all(temp_engine, tables=[EmailPrimaryKey.__table__])  # pyright: ignore[reportArgumentType]
        temp_session_db = sessionmaker(bind=temp_engine)
        with temp_session_db() as session:
            user = EmailPrimaryKey(email="bear@example.com", name="Bear")
            session.add(user)
            session.commit()

            retrieved = session.execute(
                select(EmailPrimaryKey).where(EmailPrimaryKey.email == "bear@example.com")
            ).scalar_one()

            assert retrieved.name == "Bear"
        Base.metadata.drop_all(temp_engine, tables=[EmailPrimaryKey.__table__])  # pyright: ignore[reportArgumentType]

    def test_multiple_string_pk_tables_in_same_db(self, temp_engine: Engine) -> None:
        """Multiple tables with different string PK types should coexist."""
        Base.metadata.create_all(
            temp_engine,
            tables=[ProductNoAutoincrement.__table__, AccountUUID.__table__, EmailPrimaryKey.__table__],  # pyright: ignore[reportArgumentType]
        )
        temp_session_db = sessionmaker(bind=temp_engine)
        with temp_session_db() as session:
            # Insert into multiple tables
            product = ProductNoAutoincrement(sku="SKU-001", name="Product", price=100)
            account = AccountUUID(account_id="550e8400-e29b-41d4-a716-446655440000", username="testuser")
            email_user = EmailPrimaryKey(email="test@example.com", name="Test User")

            session.add_all([product, account, email_user])
            session.commit()

            # Verify all were inserted
            assert (
                session.execute(select(ProductNoAutoincrement).where(ProductNoAutoincrement.sku == "SKU-001"))
                .scalar_one()
                .name
                == "Product"
            )

            assert (
                session.execute(
                    select(AccountUUID).where(AccountUUID.account_id == "550e8400-e29b-41d4-a716-446655440000")
                )
                .scalar_one()
                .username
                == "testuser"
            )

            assert (
                session.execute(select(EmailPrimaryKey).where(EmailPrimaryKey.email == "test@example.com"))
                .scalar_one()
                .name
                == "Test User"
            )
        Base.metadata.drop_all(
            temp_engine,
            tables=[ProductNoAutoincrement.__table__, AccountUUID.__table__, EmailPrimaryKey.__table__],  # pyright: ignore[reportArgumentType]
        )

    def test_explicit_autoincrement_true_on_string_pk_raises_error(self, temp_engine: Engine) -> None:
        """Explicitly setting autoincrement=True on string PK should raise validation error."""

        class BadModel(Base):
            __tablename__ = "bad_model"
            sku: Mapped[str] = mapped_column(String(50), primary_key=True, autoincrement=True)
            name: Mapped[str] = mapped_column(String(100))

        with pytest.raises(ValueError, match="Cannot use autoincrement=True on non-integer type"):
            BadModel.metadata.create_all(temp_engine)


class TestRegressionIntegerPKs:
    """Regression tests to ensure integer PKs still work correctly."""

    def test_integer_pk_with_explicit_value(self, temp_engine: Engine) -> None:
        """Integer PK with explicit value should work (no auto-generation)."""
        Base.metadata.create_all(temp_engine, tables=[UserWithIntPK.__table__])  # pyright: ignore[reportArgumentType]
        temp_session_db = sessionmaker(bind=temp_engine)

        with temp_session_db() as session:
            user = UserWithIntPK(id=999, username="explicit_id", email="explicit@example.com")
            session.add(user)
            session.commit()

            retrieved = session.execute(select(UserWithIntPK).where(UserWithIntPK.id == 999)).scalar_one()

            assert retrieved.username == "explicit_id"
        Base.metadata.drop_all(temp_engine, tables=[UserWithIntPK.__table__])  # pyright: ignore[reportArgumentType]

    def test_integer_pk_auto_increment_sequence(self, temp_engine: Engine) -> None:
        """Integer PK should auto-increment correctly over multiple inserts."""
        Base.metadata.create_all(temp_engine, tables=[UserWithIntPK.__table__])  # pyright: ignore[reportArgumentType]
        temp_session_db = sessionmaker(bind=temp_engine)
        with temp_session_db() as session:
            users = [UserWithIntPK(username=f"user{i}", email=f"user{i}@example.com") for i in range(5)]
            session.add_all(users)
            session.commit()

            # Verify IDs are sequential
            all_users = session.execute(select(UserWithIntPK).order_by(UserWithIntPK.id)).scalars().all()

            assert len(all_users) == 5
            ids = [u.id for u in all_users]
            # IDs should be consecutive (or at least increasing)
            assert ids == sorted(ids)
            assert len(set(ids)) == 5  # All unique
        Base.metadata.drop_all(temp_engine, tables=[UserWithIntPK.__table__])  # pyright: ignore[reportArgumentType]

    def test_mixed_explicit_and_auto_integer_pks(self, temp_engine: Engine) -> None:
        """Mix of explicit and auto-generated integer PKs should work."""
        Base.metadata.create_all(temp_engine, tables=[UserWithIntPK.__table__])  # pyright: ignore[reportArgumentType]
        temp_session_db = sessionmaker(bind=temp_engine)
        with temp_session_db() as session:
            # Auto-generated
            user1 = UserWithIntPK(username="auto1", email="auto1@example.com")
            session.add(user1)
            session.commit()

            auto_id = user1.id

            # Explicit (higher than auto)
            user2 = UserWithIntPK(id=9999, username="explicit", email="explicit@example.com")
            session.add(user2)
            session.commit()

            # Another auto-generated (should be > 9999 or handle appropriately)
            user3 = UserWithIntPK(username="auto2", email="auto2@example.com")
            session.add(user3)
            session.commit()

            # All should exist
            all_users = session.execute(select(UserWithIntPK)).scalars().all()
            assert len(all_users) == 3
            usernames = {u.username for u in all_users}
            assert usernames == {"auto1", "explicit", "auto2"}
        Base.metadata.drop_all(temp_engine, tables=[UserWithIntPK.__table__])  # pyright: ignore[reportArgumentType]
