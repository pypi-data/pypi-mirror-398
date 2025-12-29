"""A set of models and utilities for handling JSONL lines in the datastore."""

from typing import TYPE_CHECKING

from lazy_bear import lazy

if TYPE_CHECKING:
    from bear_shelf.datastore.adapter.jsonl._convert import get_line_model, get_record_lines, get_schema_lines
    from bear_shelf.datastore.adapter.jsonl.line_types import (
        HeaderLine,
        LinePrimitive,
        LineType,
        NullLine,
        OrderedLines,
        RecordLine,
        SchemaLine,
    )
else:
    get_line_model, get_record_lines, get_schema_lines = lazy("bear_shelf.datastore.adapter.jsonl._convert").to(
        "get_line_model", "get_record_lines", "get_schema_lines"
    )
    HeaderLine, LinePrimitive, LineType, NullLine, OrderedLines, RecordLine, SchemaLine = lazy(
        "bear_shelf.datastore.adapter.jsonl.line_types"
    ).to(
        "HeaderLine",
        "LinePrimitive",
        "LineType",
        "NullLine",
        "OrderedLines",
        "RecordLine",
        "SchemaLine",
    )

__all__ = [
    "HeaderLine",
    "LinePrimitive",
    "LineType",
    "NullLine",
    "OrderedLines",
    "RecordLine",
    "SchemaLine",
    "get_line_model",
    "get_record_lines",
    "get_schema_lines",
]
