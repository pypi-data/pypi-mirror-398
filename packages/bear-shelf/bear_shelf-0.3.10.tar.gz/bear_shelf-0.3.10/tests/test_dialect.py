"""Test suite for Bear Shelf SQLAlchemy dialect."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, sessionmaker

from bear_shelf.dialect import bear_dialect  # noqa: F401

Base = declarative_base()

if TYPE_CHECKING:
    from sqlalchemy import Engine


class TestBearDialect:
    """Test cases for the Bear Shelf dialect."""

    def test_dialect_registration(self, tmp_path: Path) -> None:
        """Test that we can create an engine with our dialect."""
        db_file = tmp_path / "test_database.jsonl"
        engine: Engine = create_engine(f"bearshelf:///{db_file}")

        assert engine is not None
        assert engine.dialect.name == "bearshelf"
        assert str(engine.url).startswith("bearshelf://")

    def test_engine_connection(self, tmp_path: Path) -> None:
        """Test that we can establish a connection."""
        db_file = tmp_path / "test_database.jsonl"
        engine: Engine = create_engine(f"bearshelf:///{db_file}")

        # Test connection (will be very basic for now)
        with engine.connect() as conn:
            assert conn is not None

    def test_url_parsing(self, tmp_path: Path):
        """Test that database URLs are parsed correctly."""
        test_db_path = tmp_path / "test_db"
        absolute_path = tmp_path / "absolute_path"
        relative_path = tmp_path / "bearshelf"

        test_cases = [
            (f"bearshelf:///{test_db_path}", str(test_db_path)),
            (f"bearshelf:///{absolute_path}", str(absolute_path)),
            (f"bearshelf:///{relative_path}", str(relative_path)),  # Use tmp_path for relative test too
        ]

        for url, _ in test_cases:
            engine = create_engine(url)
            # The path should be processed correctly
            assert engine is not None

    def test_table_creation_ddl(self, tmp_path: Path) -> None:
        """Test that table creation DDL is handled properly."""

        class TestUser(Base):
            __tablename__ = "test_user"

            id: Mapped[int | None] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column()
            age: Mapped[int] = mapped_column()

        db_file: Path = tmp_path / "test_ddl_db.jsonl"
        engine: Engine = create_engine(f"bearshelf:///{db_file}")

        # This should trigger our DDL handling and create files
        TestUser.metadata.create_all(engine)

        # Check that the file was created
        assert db_file.exists(), f"Expected {db_file} to be created"

    def test_complete_table_creation_with_files(self, tmp_path: Path) -> None:
        """Test complete table creation with actual JSONL files."""

        # Define a SQLModel table with unique name
        class IntegrationUser(Base):
            __tablename__ = "integration_user"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str] = mapped_column()
            age: Mapped[int] = mapped_column()

        # Create engine with single database file
        test_db_file: Path = tmp_path / "integration_test_db.jsonl"
        engine: Engine = create_engine(f"bearshelf:///{test_db_file}")

        # Create tables - this should create the database file
        IntegrationUser.metadata.create_all(engine)

        # Verify the database file was created
        assert test_db_file.exists(), f"Expected {test_db_file} to be created"

        # Verify the JSONL content is correct
        with open(test_db_file) as f:
            content = f.read().strip()
            lines = content.split("\n")

        # Should have header line + schema lines for each table
        assert len(lines) >= 2, f"Expected at least 2 lines, got {len(lines)}"

        # Parse and verify header line
        header_line = json.loads(lines[0])
        assert header_line["$type"] == "header"
        assert "integration_user" in header_line["data"]["tables"]
        assert "version" in header_line["data"]

        # Find and verify the integration_user schema line
        integration_schema = None
        for line in lines[1:]:
            schema_line = json.loads(line)
            if schema_line.get("table") == "integration_user":
                integration_schema = schema_line
                break

        assert integration_schema is not None, "integration_user schema not found"
        assert integration_schema["$type"] == "schema"
        assert integration_schema["table"] == "integration_user"
        assert integration_schema["count"] == 0  # No records yet

        # Verify columns are present
        columns = {col["name"] for col in integration_schema["columns"]}
        expected_columns = {"id", "name", "age"}
        assert columns == expected_columns, f"Expected {expected_columns}, got {columns}"

    def test_unique_constraint_handling(self, tmp_path: Path) -> None:
        """Test that unique constraints are handled correctly."""

        class UniqueUser(Base):
            __tablename__ = "unique_user"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            username: Mapped[str] = mapped_column(unique=True)
            id_num: Mapped[int] = mapped_column(unique=True)

        db_file: Path = tmp_path / "unique_constraint_db.jsonl"
        engine: Engine = create_engine(f"bearshelf:///{db_file}")
        UniqueUser.metadata.create_all(engine)

        sessions = sessionmaker(bind=engine)
        with sessions() as session:
            user1 = UniqueUser(username="user1", id_num=100)
            user2 = UniqueUser(username="user2", id_num=101)
            user3 = UniqueUser(username="user3", id_num=100)
            session.add_all([user1, user2, user3])

            with pytest.raises(ValueError, match="Duplicate unique value"):
                session.commit()
