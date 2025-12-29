"""JSONL storage backend for the datastore."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

from ._common import Storage

if TYPE_CHECKING:
    from logging import Logger
    from pathlib import Path

    from bear_shelf._logger import get_logger
    from bear_shelf.datastore.adapter import LinePrimitive, OrderedLines
    from bear_shelf.datastore.adapter.jsonl import from_jsonl_lines, to_jsonl_lines
    from bear_shelf.datastore.unified_data import UnifiedDataFormat
    from codec_cub.general.helpers import touch
    from codec_cub.jsonl.file_handler import JSONLFileHandler
else:
    touch = lazy("codec_cub.general.helpers", "touch")
    get_logger = lazy("bear_shelf._logger", "get_logger")
    JSONLFileHandler = lazy("codec_cub.jsonl.file_handler", "JSONLFileHandler")
    from_jsonl_lines, to_jsonl_lines = lazy("bear_shelf.datastore.adapter.jsonl", "from_jsonl_lines", "to_jsonl_lines")
    LinePrimitive, OrderedLines = lazy("bear_shelf.datastore.adapter", "LinePrimitive", "OrderedLines")
    UnifiedDataFormat = lazy("bear_shelf.datastore.unified_data", "UnifiedDataFormat")


class JSONLStorage(Storage):
    """A JSONL (JSON Lines) file storage backend.

    Each line in the file represents one JSON object/record.
    This format is append-friendly and easily parsable line-by-line.
    """

    def __init__(self, file: str | Path, file_mode: str = "a+", encoding: str = "utf-8") -> None:
        """Initialize JSONL storage.

        Args:
            file: Path to the JSONL file
            file_mode: File mode for opening (default: "a+" for read/append)
            encoding: Text encoding to use (default: "utf-8")
        """
        super().__init__()
        self.logger: Logger = get_logger("JSONLStorage")
        self.file: Path = touch(file, mkdir=True, create_file=True)
        self.file_mode: str = file_mode
        self.encoding: str = encoding
        self.handler: JSONLFileHandler = JSONLFileHandler(file=self.file, mode=file_mode, encoding=encoding)  # pyright: ignore[reportIncompatibleVariableOverride]
        self.logger.debug(f"JSONLStorage initialized with file: {self.file}")

    def read(self, **kwargs) -> UnifiedDataFormat | None:
        """Read data from JSONL file.

        Returns:
            UnifiedDataFormat instance or None if empty.

        Note:
            JSONL format stores structured lines with $type field.
            Lines are parsed into the unified format with header, schema, and records.
        """
        try:
            lines: list[str] = kwargs.pop("data", None) or self.readlines()
            self.logger.debug(f"Raw lines read from JSONL file {self.file}: #{len(lines)}")
            if not lines:
                return UnifiedDataFormat()
            return from_jsonl_lines(lines)
        except (ValueError, OSError) as e:
            self.logger.error(f"Error reading JSONL storage from {self.file}: {e}")
            return None

    def readlines(self) -> list[str]:
        """Read raw lines from the JSONL file."""
        return self.handler.splitlines()

    def ordered_lines(self, data: list[str] | None = None) -> list[OrderedLines]:
        """Read and parse lines into OrderedLines."""
        output_lines: list[OrderedLines] = []
        data = data or self.readlines()
        for index, line in enumerate(data):
            output_lines.append(OrderedLines(idx=index, line=line))
        return output_lines

    def write_from_strings(self, lines: list[str]) -> None:
        """Write raw JSONL lines to the file.

        Args:
            lines: List of JSON strings, each representing a line in JSONL format.
        """
        if not lines:
            return
        self.handler.clear()
        self.handler.writelines(lines)

    def write(self, data: UnifiedDataFormat) -> None:
        """Write data to JSONL file.

        The entire file content is replaced so for larger datasets this would
        be fairly inefficient.

        TODO: Right now we do not take advantage of the fact that JSONL is append friendly
        and fast because of that since we read and write the whole file at once.
        In the future, we could implement more efficient methods for appending records
        if there is only a single table since it would be more efficient to just append lines
        rather than rewriting the whole file.

        Please see https://github.com/sicksubroutine/bear-dereth/issues/28 for more details.

        Args:
            data: UnifiedDataFormat instance to write.
                  Converts to JSONL line format with header, schema, and record lines.
        """
        lines: list[LinePrimitive] = to_jsonl_lines(data)
        line_dicts: list[dict[str, Any]] = [line.render() for line in lines]
        self.handler.clear()
        if line_dicts:
            self.handler.writelines(line_dicts)

    def close(self) -> None:
        """Close the file handle."""
        self.logger.debug(f"Closing JSONLStorage for file: {self.file}: {self.closed=}")
        if self.closed:
            return
        self.handler.close()

    @property
    def closed(self) -> bool:
        """Check if the storage is closed."""
        return self.handler.closed


__all__ = ["JSONLStorage"]
