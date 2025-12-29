"""Tests for JSONL adapter conversion between JSONL lines and UnifiedDataFormat."""

import json

import pytest

from bear_shelf.config import APP_CONFIG
from bear_shelf.datastore.adapter.jsonl._convert import (
    Converter,
    from_jsonl_lines,
    get_line_model,
    get_record_lines,
    get_schema_lines,
    to_jsonl_lines,
)
from bear_shelf.datastore.adapter.jsonl.line_types import (
    HeaderLine,
    LinePrimitive,
    NullLine,
    OrderedLines,
    RecordLine,
    SchemaLine,
)
from bear_shelf.datastore.columns import Columns
from bear_shelf.datastore.record import Record
from bear_shelf.datastore.tables.data import TableData
from bear_shelf.datastore.unified_data import UnifiedDataFormat


@pytest.fixture
def sample_unified_data() -> UnifiedDataFormat:
    """Create sample UnifiedDataFormat for testing."""
    data = UnifiedDataFormat()
    data.new_table(
        name="users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
            Columns(name="age", type="int"),
        ],
    )
    data.table("users").insert(Record(root={"id": 1, "name": "Bear", "age": 30}))
    data.table("users").insert(Record(root={"id": 2, "name": "Shannon", "age": 25}))
    return data


@pytest.fixture
def sample_jsonl_lines() -> list[str]:
    """Create sample JSONL lines for testing."""
    return [
        '{"$type": "header", "data": {"version": "0.1.0", "tables": ["users"]}}',
        '{"$type": "schema", "table": "users", "columns": [{"name": "id", "type": "int", "primary_key": true}, {"name": "name", "type": "str", "primary_key": false}, {"name": "age", "type": "int", "primary_key": false}], "count": 2}',
        '{"$type": "record", "table": "users", "data": {"id": 1, "name": "Bear", "age": 30}}',
        '{"$type": "record", "table": "users", "data": {"id": 2, "name": "Shannon", "age": 25}}',
    ]


class TestGetLineModel:
    """Tests for get_line_model function."""

    def test_get_line_model_header_string(self) -> None:
        """Test identifying header line from JSON string."""
        line = '{"$type": "header", "data": {}}'
        assert get_line_model(line) == HeaderLine

    def test_get_line_model_schema_string(self) -> None:
        """Test identifying schema line from JSON string."""
        line = '{"$type": "schema", "table": "users"}'
        assert get_line_model(line) == SchemaLine

    def test_get_line_model_record_string(self) -> None:
        """Test identifying record line from JSON string."""
        line = '{"$type": "record", "table": "users", "data": {}}'
        assert get_line_model(line) == RecordLine

    def test_get_line_model_header_dict(self) -> None:
        """Test identifying header line from dict."""
        line = {"$type": "header", "data": {}}
        assert get_line_model(line) == HeaderLine

    def test_get_line_model_invalid_json(self) -> None:
        """Test handling invalid JSON string."""
        line = "{not valid json}"
        assert get_line_model(line) == NullLine

    def test_get_line_model_missing_type(self) -> None:
        """Test handling missing $type field."""
        line = '{"table": "users", "data": {}}'
        assert get_line_model(line) == NullLine

    def test_get_line_model_unknown_type(self) -> None:
        """Test handling unknown $type value."""
        line = '{"$type": "unknown", "data": {}}'
        assert get_line_model(line) == NullLine


class TestGetSchemaLines:
    """Tests for get_schema_lines function."""

    def test_get_schema_lines_single(self) -> None:
        """Test extracting single schema line."""
        lines: list[str] = [
            '{"$type": "schema", "table": "users", "columns": [], "count": 0}',
        ]
        result: list[SchemaLine] = get_schema_lines(lines)
        assert len(result) == 1
        assert isinstance(result[0], SchemaLine)
        assert result[0].table == "users"

    def test_get_schema_lines_multiple(self) -> None:
        """Test extracting multiple schema lines."""
        lines: list[str] = [
            '{"$type": "schema", "table": "users", "columns": [], "count": 0}',
            '{"$type": "record", "table": "users", "data": {}}',
            '{"$type": "schema", "table": "posts", "columns": [], "count": 0}',
        ]
        result: list[SchemaLine] = get_schema_lines(lines)
        assert len(result) == 2
        assert result[0].table == "users"
        assert result[1].table == "posts"

    def test_get_schema_lines_empty(self) -> None:
        """Test with no schema lines."""
        lines: list[str] = [
            '{"$type": "header", "data": {}}',
            '{"$type": "record", "table": "users", "data": {}}',
        ]
        result: list[SchemaLine] = get_schema_lines(lines)
        assert len(result) == 0


class TestGetRecordLines:
    """Tests for get_record_lines function."""

    def test_get_record_lines_single(self) -> None:
        """Test extracting single record line."""
        lines: list[str] = [
            '{"$type": "record", "table": "users", "data": {"id": 1}}',
        ]
        result: list[RecordLine] = get_record_lines(lines)
        assert len(result) == 1
        assert isinstance(result[0], RecordLine)
        assert result[0].data == {"id": 1}

    def test_get_record_lines_multiple(self) -> None:
        """Test extracting multiple record lines."""
        lines: list[str] = [
            '{"$type": "schema", "table": "users", "columns": [], "count": 2}',
            '{"$type": "record", "table": "users", "data": {"id": 1}}',
            '{"$type": "record", "table": "users", "data": {"id": 2}}',
        ]
        result: list[RecordLine] = get_record_lines(lines)
        assert len(result) == 2
        assert result[0].data == {"id": 1}
        assert result[1].data == {"id": 2}

    def test_get_record_lines_empty(self) -> None:
        """Test with no record lines."""
        lines: list[str] = [
            '{"$type": "header", "data": {}}',
            '{"$type": "schema", "table": "users", "columns": [], "count": 0}',
        ]
        result: list[RecordLine] = get_record_lines(lines)
        assert len(result) == 0


class TestConverterToJsonLines:
    """Tests for Converter.to_json_lines method."""

    def test_to_json_lines_basic(self, sample_unified_data):
        """Test basic conversion to JSONL lines."""
        converter: Converter = Converter(data=sample_unified_data)
        lines: list[LinePrimitive] = converter.to_json_lines()

        assert len(lines) >= 4  # header + schema + 2 records
        assert isinstance(lines[0], HeaderLine)
        assert isinstance(lines[1], SchemaLine)
        assert isinstance(lines[2], RecordLine)
        assert isinstance(lines[3], RecordLine)

    def test_to_json_lines_header_content(self, sample_unified_data):
        """Test header line contains correct data."""
        converter: Converter = Converter(data=sample_unified_data)
        lines: list[LinePrimitive] = converter.to_json_lines()

        header: HeaderLine = HeaderLine.model_validate(lines[0].model_dump())
        assert header.data is not None
        assert header.data["version"] == APP_CONFIG.info.unified_data_version
        assert "users" in header.data["tables"]

    def test_to_json_lines_schema_content(self, sample_unified_data: UnifiedDataFormat):
        """Test schema line contains correct structure."""
        converter: Converter[UnifiedDataFormat] = Converter(data=sample_unified_data)
        lines: list[LinePrimitive] = converter.to_json_lines()

        schema: LinePrimitive = lines[1]
        assert schema.table == "users"
        assert schema.columns is not None
        assert len(schema.columns) == 3
        assert schema.count == 2

    def test_to_json_lines_record_content(self, sample_unified_data: UnifiedDataFormat) -> None:
        """Test record lines contain correct data."""
        converter: Converter[UnifiedDataFormat] = Converter(data=sample_unified_data)
        lines: list[LinePrimitive] = converter.to_json_lines()

        record1: LinePrimitive = lines[2]
        assert record1.table == "users"
        assert record1.columns is None

        assert record1.data is not None
        data = record1.data["root"]
        assert data["id"] == 1
        assert data["name"] == "Bear"
        assert data["age"] == 30
        assert record1.count is None

    def test_to_json_lines_empty_data(self) -> None:
        """Test conversion with empty data."""
        converter: Converter[UnifiedDataFormat] = Converter(data=UnifiedDataFormat())
        lines: list[LinePrimitive] = converter.to_json_lines()

        assert len(lines) == 1  # Only header
        assert isinstance(lines[0], HeaderLine)

    def test_to_json_lines_no_data_provided(self) -> None:
        """Test conversion when no data provided."""
        converter: Converter = Converter()
        lines: list[LinePrimitive] = converter.to_json_lines()
        assert len(lines) == 0


class TestConverterFromJsonlLines:
    """Tests for Converter.from_jsonl_lines method."""

    def test_from_jsonl_lines_basic(self, sample_jsonl_lines: list[str]) -> None:
        """Test basic conversion from JSONL lines."""
        converter: Converter = Converter()
        result: UnifiedDataFormat = converter.from_jsonl_lines(sample_jsonl_lines)

        assert isinstance(result, UnifiedDataFormat)
        assert "users" in result.tables
        assert len(result.table("users").records) == 2

    def test_from_jsonl_lines_header_parsed(self, sample_jsonl_lines: list[str]) -> None:
        """Test header is correctly parsed."""
        converter: Converter = Converter()
        result: UnifiedDataFormat = converter.from_jsonl_lines(sample_jsonl_lines)

        assert result.header.version == "0.1.0"
        assert "users" in result.header.tables

    def test_from_jsonl_lines_schema_parsed(self, sample_jsonl_lines: list[str]) -> None:
        """Test schema is correctly parsed."""
        converter: Converter = Converter()
        result: UnifiedDataFormat = converter.from_jsonl_lines(sample_jsonl_lines)

        table: TableData = result.table("users")
        assert len(table.columns) == 3
        assert table.columns[0].name == "id"
        assert table.columns[0].primary_key is True

    def test_from_jsonl_lines_records_parsed(self, sample_jsonl_lines: list[str]) -> None:
        """Test records are correctly parsed."""
        converter: Converter = Converter()
        result: UnifiedDataFormat = converter.from_jsonl_lines(sample_jsonl_lines)

        records: list[Record] = result.table("users").records
        assert len(records) == 2
        assert records[0]["name"] == "Bear"
        assert records[1]["name"] == "Shannon"

    def test_from_jsonl_lines_empty(self) -> None:
        """Test with empty lines raises ValueError."""
        converter: Converter = Converter()
        with pytest.raises(ValueError, match="No lines to determine type"):
            converter.from_jsonl_lines([])

    def test_from_jsonl_lines_ordered(self) -> None:
        """Test with OrderedLines input."""
        lines: list[OrderedLines] = [
            OrderedLines(idx=0, line='{"$type": "header", "data": {"version": "0.1.0", "tables": ["test"]}}'),
            OrderedLines(
                idx=1,
                line='{"$type": "schema", "table": "test", "columns": [{"name": "id", "type": "int", "primary_key": true}], "count": 0}',
            ),
        ]
        converter = Converter()
        result: UnifiedDataFormat = converter.from_jsonl_lines(lines)
        assert "test" in result.tables

    def test_from_jsonl_lines_out_of_order(self) -> None:
        """Test lines reordered correctly via priority queue."""
        lines: list[OrderedLines] = [
            OrderedLines(idx=2, line='{"$type": "record", "table": "users", "data": {"id": 1}}'),
            OrderedLines(idx=0, line='{"$type": "header", "data": {"version": "0.1.0", "tables": ["users"]}}'),
            OrderedLines(
                idx=1,
                line='{"$type": "schema", "table": "users", "columns": [{"name": "id", "type": "int", "primary_key": true}], "count": 1}',
            ),
        ]
        converter = Converter()
        result: UnifiedDataFormat = converter.from_jsonl_lines(lines)
        assert "users" in result.tables
        assert len(result.table("users").records) == 1


class TestConverterInputDataType:
    """Tests for Converter.input_data_type static method."""

    def test_input_data_type_strings(self) -> None:
        """Test detecting string list."""
        lines: list[str] = ['{"$type": "header"}', '{"$type": "schema"}']
        assert Converter.input_data_type(lines) is str

    def test_input_data_type_ordered_lines(self) -> None:
        """Test detecting OrderedLines list."""
        lines: list[OrderedLines] = [OrderedLines(idx=0, line="test")]
        assert Converter.input_data_type(lines) == OrderedLines

    def test_input_data_type_empty_raises(self) -> None:
        """Test empty list raises ValueError."""
        with pytest.raises(ValueError, match="No lines to determine type"):
            Converter.input_data_type([])


class TestConverterRoundTrip:
    """Test round-trip conversion: UnifiedDataFormat -> JSONL -> UnifiedDataFormat."""

    def test_round_trip_basic(self, sample_unified_data: UnifiedDataFormat) -> None:
        """Test basic round-trip conversion."""
        # Convert to JSONL lines
        lines: list[LinePrimitive] = to_jsonl_lines(sample_unified_data)

        # Serialize to JSON strings
        json_strings: list[str] = [json.dumps(line.render()) for line in lines]

        # Convert back to UnifiedDataFormat
        result: UnifiedDataFormat = from_jsonl_lines(json_strings)

        # Verify structure preserved
        assert "users" in result.tables
        assert len(result.table("users").records) == 2
        assert result.table("users").columns[0].name == "id"

    def test_round_trip_multiple_tables(self) -> None:
        """Test round-trip with multiple tables."""
        data = UnifiedDataFormat()
        data.new_table(name="users", columns=[Columns(name="id", type="int", primary_key=True)])
        data.new_table(name="posts", columns=[Columns(name="id", type="int", primary_key=True)])
        data.table("users").insert(Record(root={"id": 1}))
        data.table("posts").insert(Record(root={"id": 100}))

        # Round trip
        lines: list[LinePrimitive] = to_jsonl_lines(data)
        json_strings: list[str] = [json.dumps(line.render()) for line in lines]
        result: UnifiedDataFormat = from_jsonl_lines(json_strings)

        assert len(result.tables) == 2
        assert "users" in result.tables
        assert "posts" in result.tables
        assert len(result.table("users").records) == 1
        assert len(result.table("posts").records) == 1


class TestModuleFunctions:
    """Test top-level module functions."""

    def test_to_jsonl_lines_function(self, sample_unified_data: UnifiedDataFormat) -> None:
        """Test to_jsonl_lines top-level function."""
        lines: list[LinePrimitive] = to_jsonl_lines(sample_unified_data)
        assert len(lines) >= 4
        assert isinstance(lines[0], HeaderLine)

    def test_from_jsonl_lines_function(self, sample_jsonl_lines: list[str]) -> None:
        """Test from_jsonl_lines top-level function."""
        result: UnifiedDataFormat = from_jsonl_lines(sample_jsonl_lines)
        assert isinstance(result, UnifiedDataFormat)
        assert "users" in result.tables
