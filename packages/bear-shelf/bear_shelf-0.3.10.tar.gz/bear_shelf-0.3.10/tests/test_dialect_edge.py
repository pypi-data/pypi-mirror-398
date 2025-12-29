from __future__ import annotations

from collections.abc import Generator
from enum import StrEnum
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import Float, String
from sqlalchemy.orm import DeclarativeMeta, Mapped, Session, mapped_column

from bear_shelf.database import DatabaseManager
from bear_shelf.database.config import DatabaseConfig

Base: DeclarativeMeta = DatabaseManager.get_base()


class AccountType(StrEnum):
    """Enumeration of account types for agent currency transactions."""

    AGENT = "agent"
    HUMAN = "human"
    SYSTEM = "system"


class Accounts(Base):
    """A database model representing an account."""

    __tablename__ = "accounts"
    account_id: Mapped[str] = mapped_column(String, nullable=False, primary_key=True, autoincrement=False)
    account_type: Mapped[AccountType] = mapped_column(String(50), nullable=False, default="agent")
    created_at: Mapped[str] = mapped_column(String(100), nullable=False)
    balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


@pytest.fixture
def temp_db_init(tmp_path: Path) -> Generator[DatabaseManager[Any], Any]:
    """Initialize the AgentCurrency with a default value."""
    path: Path = tmp_path / "test_database.toml"
    db = DatabaseManager(
        database_config=DatabaseConfig(scheme="bearshelf", path=str(path)),
    )
    db.register_records(Accounts)
    db.create_tables()
    try:
        yield db
    finally:
        db.close()


def test_account_execute(temp_db_init: DatabaseManager[Any]) -> None:
    """Test the Accounts database model."""
    db: DatabaseManager[Any] = temp_db_init
    session: Session = db.get_session()

    # Create a new account
    new_account = Accounts(
        account_id="acc_123",
        account_type=AccountType.AGENT,
        created_at="2024-01-01T00:00:00Z",
        balance=100.0,
    )
    new_account_2 = Accounts(
        account_id="acc_124",
        account_type=AccountType.HUMAN,
        created_at="2024-01-02T00:00:00Z",
        balance=200.0,
    )
    session.add_all([new_account, new_account_2])
    session.commit()

    retrieved_account: Accounts | None = session.query(Accounts).filter_by(account_id="acc_123").first()
    assert retrieved_account is not None
    assert retrieved_account.account_type == AccountType.AGENT
    assert retrieved_account.balance == 100.0

    retrieved_account.balance += 50.0
    session.commit()

    updated_account: Accounts | None = session.query(Accounts).filter_by(account_id="acc_123").first()
    assert updated_account is not None
    assert updated_account.balance == 150.0

    session.delete(retrieved_account)
    session.commit()
    session.close()


def test_account_executemany(temp_db_init: DatabaseManager[Any]) -> None:
    """Test the Accounts database model."""
    db: DatabaseManager[Any] = temp_db_init
    session: Session = db.get_session()

    # Create a new account
    new_account = Accounts(
        account_id="acc_123",
        account_type=AccountType.AGENT,
        created_at="2024-01-01T00:00:00Z",
        balance=100.0,
    )
    new_account_2 = Accounts(
        account_id="acc_124",
        account_type=AccountType.HUMAN,
        created_at="2024-01-02T00:00:00Z",
        balance=200.0,
    )
    session.add_all([new_account, new_account_2])
    session.commit()

    retrieved_account: Accounts | None = session.query(Accounts).filter_by(account_id="acc_123").first()
    assert retrieved_account is not None
    assert retrieved_account.account_type == AccountType.AGENT
    assert retrieved_account.balance == 100.0

    account_2: Accounts | None = session.query(Accounts).filter_by(account_id="acc_124").first()
    assert account_2 is not None
    assert account_2.account_type == AccountType.HUMAN
    assert account_2.balance == 200.0

    retrieved_account.balance += 50.0
    account_2.balance += 25.0
    session.commit()

    updated_account: Accounts | None = session.query(Accounts).filter_by(account_id="acc_123").first()
    assert updated_account is not None
    assert updated_account.balance == 150.0

    updated_account_2: Accounts | None = session.query(Accounts).filter_by(account_id="acc_124").first()
    assert updated_account_2 is not None
    assert updated_account_2.balance == 225.0

    session.delete(retrieved_account)
    session.delete(account_2)
    session.commit()
    session.close()
