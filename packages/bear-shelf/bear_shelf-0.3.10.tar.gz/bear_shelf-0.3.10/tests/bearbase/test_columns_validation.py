"""Test to reproduce column duplication issue."""

from pathlib import Path

import pytest

from bear_shelf.datastore.columns import Columns
from bear_shelf.datastore.record import Record
from bear_shelf.datastore.storage.toml import TomlStorage
from bear_shelf.datastore.storage.xml import XMLStorage
from bear_shelf.datastore.unified_data import HeaderData, TableData, UnifiedDataFormat


def test_simple_write_read_columns(tmp_path: Path) -> None:
    """Test that a simple write and read preserves column count."""
    data = UnifiedDataFormat(
        header=HeaderData(version="0.1.0", tables=["settings"]),
        tables={
            "settings": TableData(
                name="settings",
                columns=[
                    Columns(name="id", type="int", nullable=False, primary_key=True),
                    Columns(name="key", type="str", nullable=False),
                    Columns(name="value", type="str", nullable=False),
                    Columns(name="type", type="str", nullable=False),
                ],
                records=[
                    {"id": 1, "key": "test", "value": "hello", "type": "str"},
                ],  # pyright: ignore[reportArgumentType]
            )
        },
    )

    assert len(data.tables["settings"].columns) == 4
    toml_path: Path = tmp_path / "test_duplication.toml"
    toml_storage = TomlStorage(toml_path, file_mode="w+", encoding="utf-8")
    toml_storage.write(data)

    toml_storage.close()
    xml_path: Path = tmp_path / "test_duplication.xml"
    xml_storage = XMLStorage(xml_path, file_mode="w+", encoding="utf-8")
    xml_storage.write(data)

    xml_storage.close()
    assert len(data.tables["settings"].columns) == 4, f"Expected 4 columns, got {len(data.tables['settings'].columns)}"
    toml_storage = TomlStorage(toml_path, file_mode="r", encoding="utf-8")
    loaded_toml: UnifiedDataFormat | None = toml_storage.read()
    toml_storage.close()

    xml_storage = XMLStorage(xml_path, file_mode="r", encoding="utf-8")
    loaded_xml: UnifiedDataFormat | None = xml_storage.read()
    xml_storage.close()

    assert loaded_toml is not None
    assert len(loaded_toml.tables["settings"].columns) == 4
    assert loaded_xml is not None
    assert len(loaded_xml.tables["settings"].columns) == 4


def test_duplicate_column_names_rejected() -> None:
    """Test that TableData rejects duplicate column names."""
    with pytest.raises(ValueError, match="Duplicate column names found"):
        TableData(
            name="test_table",
            columns=[
                Columns(name="id", type="int", nullable=False, primary_key=True),
                Columns(name="name", type="str", nullable=False),
                Columns(name="name", type="str", nullable=False),  # duplicate!
            ],
        )


def test_multiple_duplicate_column_names_rejected() -> None:
    """Test that TableData reports all duplicate column names."""
    with pytest.raises(ValueError, match="'id', 'name'"):
        TableData(
            name="test_table",
            columns=[
                Columns(name="id", type="int", nullable=False, primary_key=True),
                Columns(name="name", type="str", nullable=False),
                Columns(name="id", type="int", nullable=False),
                Columns(name="name", type="str", nullable=False),
            ],
        )


def test_no_primary_key_rejected() -> None:
    """Test that TableData requires at least one primary key."""
    with pytest.raises(ValueError, match="At least one column must be designated as primary_key=True"):
        TableData(
            name="test_table",
            columns=[
                Columns(name="id", type="int", nullable=False),
                Columns(name="name", type="str", nullable=False),
            ],
        )


def test_multiple_primary_keys_rejected() -> None:
    """Test that TableData rejects multiple primary keys."""
    with pytest.raises(ValueError, match="Exactly one column must be designated as primary key"):
        TableData(
            name="test_table",
            columns=[
                Columns(name="id", type="int", nullable=False, primary_key=True),
                Columns(name="uuid", type="str", nullable=False, primary_key=True),
            ],
        )


def test_nullable_primary_key_rejected() -> None:
    """Test that primary key cannot be nullable."""
    with pytest.raises(ValueError, match="Primary key column 'id' cannot be nullable"):
        TableData(
            name="test_table",
            columns=[
                Columns(name="id", type="int", nullable=True, primary_key=True),
                Columns(name="name", type="str", nullable=False),
            ],
        )


def test_autoincrement_on_non_primary_key_rejected() -> None:
    """Test that autoincrement requires primary_key=True."""
    with pytest.raises(ValueError, match="Autoincrement can only be set on primary key columns"):
        TableData(
            name="test_table",
            columns=[
                Columns(name="id", type="int", nullable=False, primary_key=True),
                Columns(name="counter", type="int", nullable=False, autoincrement=True),  # type: ignore[arg-type]
            ],
        )


def test_autoincrement_on_non_integer_rejected() -> None:
    """Test that autoincrement requires integer type."""
    with pytest.raises(ValueError, match="Autoincrement can only be set on integer columns"):
        TableData(
            name="test_table",
            columns=[
                Columns(name="id", type="str", nullable=False, primary_key=True, autoincrement=True),  # type: ignore[arg-type]
            ],
        )


def test_empty_column_name_rejected() -> None:
    """Test that column names cannot be empty."""
    with pytest.raises(ValueError, match="Column name cannot be empty"):
        TableData(
            name="test_table",
            columns=[
                Columns(name="", type="int", nullable=False, primary_key=True),
            ],
        )


def test_whitespace_only_column_name_rejected() -> None:
    """Test that column names cannot be only whitespace."""
    with pytest.raises(ValueError, match="Column name cannot be empty"):
        TableData(
            name="test_table",
            columns=[
                Columns(name="   ", type="int", nullable=False, primary_key=True),
            ],
        )


def test_column_name_starting_with_number_rejected() -> None:
    """Test that column names cannot start with a number."""
    with pytest.raises(ValueError, match="Column name must start with a letter or underscore"):
        TableData(
            name="test_table",
            columns=[
                Columns(name="123_id", type="int", nullable=False, primary_key=True),
            ],
        )


def test_column_name_with_spaces_rejected() -> None:
    """Test that column names cannot contain spaces."""
    with pytest.raises(ValueError, match="Column name cannot contain spaces"):
        TableData(
            name="test_table",
            columns=[
                Columns(name="my field", type="int", nullable=False, primary_key=True),
            ],
        )


def test_column_name_starting_with_xml_rejected() -> None:
    """Test that column names cannot start with 'xml'."""
    with pytest.raises(ValueError, match="Column name cannot start with 'xml'"):
        TableData(
            name="test_table",
            columns=[
                Columns(name="xmlData", type="int", nullable=False, primary_key=True),
            ],
        )


def test_empty_table_name_rejected() -> None:
    """Test that table names cannot be empty."""
    with pytest.raises(ValueError, match="Table name cannot be empty"):
        TableData(
            name="",
            columns=[
                Columns(name="id", type="int", nullable=False, primary_key=True),
            ],
        )


def test_table_name_with_spaces_rejected() -> None:
    """Test that table names cannot contain spaces."""
    with pytest.raises(ValueError, match="Table name cannot contain spaces"):
        TableData(
            name="my table",
            columns=[
                Columns(name="id", type="int", nullable=False, primary_key=True),
            ],
        )


def test_table_name_starting_with_number_rejected() -> None:
    """Test that table names cannot start with a number."""
    with pytest.raises(ValueError, match="Table name must start with a letter or underscore"):
        TableData(
            name="123_table",
            columns=[
                Columns(name="id", type="int", nullable=False, primary_key=True),
            ],
        )


def test_table_with_no_columns_rejected() -> None:
    """Test that tables must have at least one column."""
    with pytest.raises(ValueError, match="Table 'empty_table' must have at least one column"):
        TableData(name="empty_table")


def test_record_missing_non_nullable_field_rejected():
    """Test that records must provide values for non-nullable columns."""
    table = TableData(
        name="users",
        columns=[
            Columns(name="id", type="int", nullable=False, primary_key=True),
            Columns(name="username", type="str", nullable=False),
            Columns(name="email", type="str", nullable=True),
        ],
    )

    with pytest.raises(ValueError, match="Missing required fields: \\{'username'\\}"):
        table.add_record(Record(id=1, email="test@example.com"))


def test_record_with_nullable_field_omitted_accepted() -> None:
    """Test that records can omit nullable columns."""
    table = TableData(
        name="users",
        columns=[
            Columns(name="id", type="int", nullable=False, primary_key=True),
            Columns(name="username", type="str", nullable=False),
            Columns(name="email", type="str", nullable=True),
        ],
    )

    table.add_record(Record(id=1, username="john_doe"))
    assert len(table.records) == 1
    assert table.records[0]["username"] == "john_doe"


def test_default_and_default_factory_mutually_exclusive() -> None:
    """Test that both default and default_factory cannot be specified."""
    with pytest.raises(ValueError, match="Cannot specify both 'default' and 'default_factory'"):
        Columns(
            name="id",
            type="int",
            nullable=False,
            primary_key=True,
            default=1,
            default_factory=lambda: 42,
        )  # type: ignore[arg-type]


def test_default_factory_must_be_callable() -> None:
    """Test that default_factory must be callable."""
    with pytest.raises(TypeError, match="default_factory must be callable"):
        Columns(
            name="id",
            type="int",
            nullable=False,
            primary_key=True,
            default_factory="not_callable",  # type: ignore[arg-type]
        )


def test_default_factory_works() -> None:
    """Test that default_factory is called to generate defaults."""
    counter: dict[str, int] = {"value": 0}

    def increment() -> int:
        counter["value"] += 1
        return counter["value"]

    col: Columns[int] = Columns(name="id", type="int", primary_key=True, default_factory=increment)

    assert col.get_default() == 1
    assert col.get_default() == 2
    assert col.get_default() == 3


def test_default_value_works() -> None:
    """Test that default value is returned correctly."""
    col: Columns[str] = Columns(name="status", type="str", default="active")

    assert col.get_default() == "active"
    assert col.get_default() == "active"  # Should return same value


def test_no_default_returns_none() -> None:
    """Test that columns without default or default_factory return None."""
    col: Columns[str | None] = Columns(name="optional", type="str", nullable=True)

    assert col.get_default() is None


def test_factory_inside_table_data() -> None:
    """Test that TableData applies default_factory correctly."""
    from bear_epoch_time import EpochTimestamp  # noqa: PLC0415

    id_col = Columns[int](name="id", type="int", primary_key=True, default=0)

    table = TableData(
        name="items",
        columns=[
            id_col,
            Columns[EpochTimestamp](name="timestamp", nullable=False, default_factory=EpochTimestamp.now),
        ],
    )

    record = Record()

    table.add_record(record)

    assert "id" in record
    assert record.id == 0
    assert isinstance(record.id, int)
    assert "timestamp" in record
    assert isinstance(record.timestamp, EpochTimestamp)
