"""A module defining line types for JSONL datastore format."""

from __future__ import annotations

from typing import Any, Literal, NamedTuple

from pydantic import BaseModel, Field

LineType = Literal["schema", "record", "header", "null"]

Schema: LineType = Field(alias="$type", serialization_alias="$type", default="schema")
Record: LineType = Field(alias="$type", serialization_alias="$type", default="record")
Header: LineType = Field(alias="$type", serialization_alias="$type", default="header")
NullType: LineType = Field(alias="$type", serialization_alias="$type", default="null")


class LinePrimitive(BaseModel):
    """The primitive representation of a line."""

    model_config = {"serialize_by_alias": True, "extra": "ignore", "validate_by_name": True}

    line_type: LineType = NullType
    table: str | None = None
    columns: list | None = None
    data: dict[str, Any] | None = None
    count: int | None = None

    def render(self, **kwargs) -> dict[str, Any]:
        """Render the line as a JSON string."""
        default: dict[str, Any] = {"exclude_none": True}
        default.update(kwargs)
        return self.model_dump(**default)


class HeaderLine(LinePrimitive):
    """The header line."""

    line_type: LineType = Header


class SchemaLine(LinePrimitive):
    """The schema line."""

    line_type: LineType = Schema


class RecordLine(LinePrimitive):
    """The record line."""

    line_type: LineType = Record


class NullLine(LinePrimitive):
    """A null line."""

    line_type: LineType = NullType


class OrderedLines(NamedTuple):
    """A named tuple to hold ordered lines."""

    idx: int
    line: str


__all__ = [
    "HeaderLine",
    "LinePrimitive",
    "NullLine",
    "OrderedLines",
    "RecordLine",
    "SchemaLine",
]
