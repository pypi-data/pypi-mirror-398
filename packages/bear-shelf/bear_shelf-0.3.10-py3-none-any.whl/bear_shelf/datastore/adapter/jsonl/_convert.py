"""Convert between JSONL lines and unified data format."""

import json
from typing import TYPE_CHECKING, Any, TypedDict

from lazy_bear import lazy

from bear_shelf.datastore.record import Record
from bear_shelf.datastore.unified_data import HeaderData, TableData, UnifiedDataFormat
from funcy_bear.tools import PriorityQueue

if TYPE_CHECKING:
    from bear_shelf.datastore.adapter.jsonl import line_types
    from bear_shelf.datastore.columns import Columns
else:
    line_types = lazy("bear_shelf.datastore.adapter.jsonl", "line_types")
    Columns = lazy("bear_shelf.datastore.columns", "Columns")


def get_line_model(raw: dict[str, Any] | str) -> type[line_types.LinePrimitive]:
    """Get the appropriate line model based on the $type field."""
    try:
        line: dict[str, Any] = json.loads(raw) if isinstance(raw, str) else raw
        line_type: str | None = line.get("$type")
    except (json.JSONDecodeError, TypeError):
        return line_types.NullLine

    match line_type:
        case "header":
            return line_types.HeaderLine
        case "schema":
            return line_types.SchemaLine
        case "record":
            return line_types.RecordLine
    return line_types.NullLine


def get_schema_lines(lines: list[str]) -> list[line_types.SchemaLine]:
    """Extract schema lines from a list of JSONL strings."""
    schema_lines: list[line_types.SchemaLine] = []
    for line in lines:
        ln: type[line_types.LinePrimitive] = get_line_model(line)
        if isinstance(ln, type) and issubclass(ln, line_types.SchemaLine):
            schema_line: line_types.SchemaLine = line_types.SchemaLine.model_validate_json(line)
            schema_lines.append(schema_line)
    return schema_lines


def get_record_lines(lines: list[str]) -> list[line_types.RecordLine]:
    """Extract record lines from a list of JSONL strings."""
    record_lines: list[line_types.RecordLine] = []
    for line in lines:
        ln: type[line_types.LinePrimitive] = get_line_model(line)
        if isinstance(ln, type) and issubclass(ln, line_types.RecordLine):
            record_line: line_types.RecordLine = line_types.RecordLine.model_validate_json(line)
            record_lines.append(record_line)
    return record_lines


class Converter[T: UnifiedDataFormat]:
    def __init__(self, data: T | None = None, lines: list[Any] | None = None) -> None:
        self._output_data: T | None = data
        self._input_data: list[Any] = lines or []
        self.unified: UnifiedDataFormat = UnifiedDataFormat()
        self.queue: PriorityQueue[line_types.OrderedLines] = PriorityQueue[line_types.OrderedLines]()

    def to_json_lines(self, data: T | None = None) -> list[line_types.LinePrimitive]:
        """Convert to JSONL line format.

        Returns:
            List of line dictionaries with $type field for JSONL serialization.
        """
        if data is None:
            if self._output_data is None:
                return []
            data = self._output_data

        lines: list[line_types.LinePrimitive] = []
        lines.append(line_types.HeaderLine(data=data.header.model_dump()))
        for name, table_data in data.tables.items():
            schema = line_types.SchemaLine(
                table=name,
                columns=[col.render() for col in table_data.columns],
                count=len(table_data.records),
            )
            lines.append(schema)
            for record in table_data.records:
                lines.append(line_types.RecordLine(table=name, data=record.model_dump(exclude_none=True)))
        return lines

    @staticmethod
    def input_data_type(lines: list[Any]) -> type[line_types.LinePrimitive | str | line_types.OrderedLines]:
        if isinstance(lines, list) and lines:
            first: str | line_types.LinePrimitive | line_types.OrderedLines = lines[0]
            if isinstance(first, str):
                return str
            if isinstance(first, line_types.LinePrimitive):
                return line_types.LinePrimitive
            if isinstance(first, line_types.OrderedLines):
                return line_types.OrderedLines
            raise TypeError("Input data must be a list of strings or LinePrimitive instances.")
        raise ValueError("No lines to determine type.")

    def lines_handling(self, lines: list[Any]) -> None:
        line_type: type[line_types.LinePrimitive | str | line_types.OrderedLines] = self.input_data_type(lines)
        if line_type is str:
            for index, line in enumerate(lines):
                self.queue.put(line_types.OrderedLines(idx=index, line=line))
            return
        if line_type is line_types.OrderedLines:
            for line in lines:
                self.queue.put(line)
            return
        raise TypeError("Input data must be a list of strings or OrderedLines instances.")

    def from_jsonl_lines(self, lines: list[str] | list[line_types.OrderedLines] | None = None) -> UnifiedDataFormat:
        """Parse JSONL lines into unified format.

        Args:
            lines: List of parsed JSON objects from JSONL file.

        Returns:
            UnifiedDataFormat instance.
        """
        self.lines_handling(lines or self._input_data)
        if not self.queue:
            return UnifiedDataFormat()

        first: line_types.OrderedLines = self.queue.get()
        model_cls: type[line_types.LinePrimitive] = get_line_model(first.line)
        if not isinstance(model_cls, type) and issubclass(model_cls, line_types.HeaderLine):
            raise TypeError("The first line must be a header line.")
        header: line_types.HeaderLine = line_types.HeaderLine.model_validate_json(first.line)
        header_obj: HeaderData = HeaderData.model_validate(header.data)
        cls = UnifiedDataFormat(header=header_obj)
        tables: dict[str, TablesDict] = {}
        while self.queue:
            next_line: line_types.OrderedLines = self.queue.get()
            model_cls = get_line_model(next_line.line)
            if not isinstance(model_cls, type):
                continue
            created_line: line_types.LinePrimitive = model_cls.model_validate_json(next_line.line)
            table_name: str | None = created_line.table
            if table_name is None:
                continue
            if table_name not in tables:
                tables[table_name] = {
                    "name": table_name,
                    "columns": [],
                    "records": [],
                }
            if isinstance(created_line, line_types.SchemaLine):
                for col in created_line.columns or []:
                    tables[table_name]["columns"].append(Columns.model_validate(col))
            elif isinstance(created_line, line_types.RecordLine) and created_line.data is not None:
                tables[table_name]["records"].append(Record.model_validate(created_line.data))
        for table_data in tables.values():
            tbl = TableData(name=table_data["name"], columns=table_data["columns"], records=table_data["records"])
            cls.new_table(name=table_data["name"], table_data=tbl)
        return cls


class TablesDict(TypedDict):
    name: str
    columns: list[Columns]
    records: list[Record]


def to_jsonl_lines(data: UnifiedDataFormat) -> list[line_types.LinePrimitive]:
    converter: Converter[UnifiedDataFormat] = Converter(data=data)
    return converter.to_json_lines()


def from_jsonl_lines(lines: list[str] | list[line_types.OrderedLines]) -> UnifiedDataFormat:
    converter: Converter = Converter(lines=lines)
    return converter.from_jsonl_lines()
