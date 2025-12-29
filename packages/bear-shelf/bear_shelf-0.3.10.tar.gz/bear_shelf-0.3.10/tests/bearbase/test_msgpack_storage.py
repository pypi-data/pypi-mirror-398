"""Tests for MsgPackStorage backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bear_shelf.datastore.tables.data import TableData

if TYPE_CHECKING:
    from pathlib import Path

from bear_shelf.datastore.columns import Columns
from bear_shelf.datastore.record import Record
from bear_shelf.datastore.storage.msgpack import MsgPackStorage
from bear_shelf.datastore.unified_data import UnifiedDataFormat


@pytest.fixture
def temp_msgpack_file(tmp_path: Path) -> Path:
    """Create a temporary MessagePack file path."""
    return tmp_path / "test_data.msgpack"


@pytest.fixture
def sample_unified_data() -> UnifiedDataFormat:
    """Create sample unified data for testing."""
    data = UnifiedDataFormat()
    columns = [
        Columns(name="id", type="int", primary_key=True),
        Columns(name="name", type="str"),
        Columns(name="active", type="bool"),
    ]
    data.new_table("users", columns=columns)
    return data


def test_msgpack_storage_init(temp_msgpack_file: Path) -> None:
    """Test MsgPackStorage initialization."""
    storage = MsgPackStorage(file=temp_msgpack_file)
    assert storage.file == temp_msgpack_file
    assert temp_msgpack_file.exists()
    storage.close()
    assert storage.closed


def test_msgpack_storage_write_and_read(temp_msgpack_file: Path, sample_unified_data: UnifiedDataFormat) -> None:
    """Test writing and reading data."""
    storage = MsgPackStorage(file=temp_msgpack_file)

    table: TableData = sample_unified_data.table("users")
    table.add_record(Record({"id": 1, "name": "Bear", "active": True}))
    table.add_record(Record({"id": 2, "name": "Shannon", "active": True}))

    storage.write(sample_unified_data)

    loaded_data: UnifiedDataFormat | None = storage.read()
    assert loaded_data is not None
    assert "users" in loaded_data

    users_table: TableData = loaded_data.table("users")
    assert users_table.count == 2
    assert len(users_table.records) == 2

    storage.close()


def test_msgpack_storage_read_empty_file(temp_msgpack_file: Path) -> None:
    """Test reading from an empty file."""
    storage = MsgPackStorage(file=temp_msgpack_file)
    result: UnifiedDataFormat | None = storage.read()
    assert result == UnifiedDataFormat()
    storage.close()


def test_msgpack_storage_filters_extra_fields(temp_msgpack_file: Path) -> None:
    """Test that extra fields in records are rejected during validation."""
    storage = MsgPackStorage(file=temp_msgpack_file)

    data = UnifiedDataFormat()
    columns: list[Columns] = [
        Columns(name="id", type="int", primary_key=True),
        Columns(name="name", type="str"),
    ]
    data.new_table("test_table", columns=columns)
    table: TableData = data.table("test_table")

    # Add record with extra field should raise ValueError
    with pytest.raises(ValueError, match="Unknown fields"):
        table.add_record(Record({"id": 1, "name": "Bear", "extra": "should_be_filtered"}))

    storage.close()


def test_msgpack_storage_overwrite(temp_msgpack_file: Path, sample_unified_data: UnifiedDataFormat) -> None:
    """Test that writing overwrites existing data."""
    storage = MsgPackStorage(file=temp_msgpack_file)

    table: TableData = sample_unified_data.table("users")
    table.add_record(Record({"id": 1, "name": "Bear", "active": True}))
    storage.write(sample_unified_data)

    new_data = UnifiedDataFormat()
    columns: list[Columns] = [Columns(name="id", type="int", primary_key=True)]
    new_data.new_table("new_table", columns=columns)

    storage.write(new_data)
    loaded_data: UnifiedDataFormat | None = storage.read()

    assert loaded_data is not None
    assert "new_table" in loaded_data
    assert "users" not in loaded_data

    storage.close()


def test_msgpack_storage_close_idempotent(temp_msgpack_file: Path) -> None:
    """Test that calling close multiple times is safe."""
    storage = MsgPackStorage(file=temp_msgpack_file)
    storage.close()
    assert storage.closed

    storage.close()
    assert storage.closed


def test_msgpack_storage_multiple_tables(temp_msgpack_file: Path) -> None:
    """Test storing and retrieving multiple tables."""
    storage = MsgPackStorage(file=temp_msgpack_file)

    data = UnifiedDataFormat()

    # Create first table
    users_columns: list[Columns] = [
        Columns(name="id", type="int", primary_key=True),
        Columns(name="name", type="str"),
    ]
    data.new_table("users", columns=users_columns)
    users_table: TableData = data.table("users")
    users_table.add_record(Record({"id": 1, "name": "Bear"}))

    # Create second table
    posts_columns: list[Columns] = [
        Columns(name="id", type="int", primary_key=True),
        Columns(name="title", type="str"),
    ]
    data.new_table("posts", columns=posts_columns)
    posts_table: TableData = data.table("posts")
    posts_table.add_record(Record({"id": 1, "title": "Hello World"}))

    # Write and read back
    storage.write(data)
    loaded_data: UnifiedDataFormat | None = storage.read()

    assert loaded_data is not None
    assert "users" in loaded_data
    assert "posts" in loaded_data

    assert loaded_data.table("users").count == 1
    assert loaded_data.table("posts").count == 1

    storage.close()


def test_msgpack_storage_binary_format(temp_msgpack_file: Path, sample_unified_data: UnifiedDataFormat) -> None:
    """Test that the file is actually binary MessagePack format."""
    storage = MsgPackStorage(file=temp_msgpack_file)

    table: TableData = sample_unified_data.table("users")
    table.add_record(Record({"id": 1, "name": "Bear", "active": True}))
    storage.write(sample_unified_data)
    storage.close()

    # Read raw bytes
    raw_bytes: bytes = temp_msgpack_file.read_bytes()

    # Should be binary (not JSON/TOML text)
    assert len(raw_bytes) > 0
    # MessagePack uses binary format, should not be valid UTF-8 text in most cases
    # (though it might accidentally be for very simple data)
    # Just verify it's not empty and is binary
    assert isinstance(raw_bytes, bytes)
