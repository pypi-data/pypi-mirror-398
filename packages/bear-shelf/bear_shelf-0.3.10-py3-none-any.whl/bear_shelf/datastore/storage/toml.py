"""TOML storage backend for the datastore.

Provides TOML file storage using the unified data format.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

from lazy_bear import lazy
from pydantic import ValidationError

from ._common import Storage

if TYPE_CHECKING:
    from logging import Logger
    from pathlib import Path
    from tomllib import loads as tomllib_loads

    from tomlkit import TOMLDocument, array, document as toml_document, dumps as tomlkit_dumps, table as toml_table
    from tomlkit.api import inline_table
    from tomlkit.items import Array, InlineTable, Table

    from bear_shelf._logger import get_logger
    from bear_shelf.datastore.record import Record
    from bear_shelf.datastore.unified_data import UnifiedDataFormat
    from codec_cub.general.helpers import touch
    from codec_cub.text.file_handler import TextFileHandler
    from funcy_bear.ops.strings.manipulation import truncate
    from funcy_bear.tools import FrozenDict
else:
    TOMLDocument, array, toml_table, tomlkit_dumps, toml_document = lazy(
        "tomlkit", "TOMLDocument", "array", "table", "dumps", "document"
    )
    UnifiedDataFormat = lazy("bear_shelf.datastore.unified_data", "UnifiedDataFormat")
    Array, InlineTable, Table = lazy("tomlkit.items", "Array", "InlineTable", "Table")
    inline_table = lazy("tomlkit.api", "inline_table")
    TextFileHandler = lazy("codec_cub.text.file_handler", "TextFileHandler")
    touch = lazy("codec_cub.general.helpers", "touch")
    truncate = lazy("funcy_bear.ops.strings.manipulation", "truncate")
    tomllib_loads = lazy("tomllib", "loads")
    get_logger = lazy("bear_shelf._logger", "get_logger")
    UnifiedDataFormat = lazy("bear_shelf.datastore.unified_data", "UnifiedDataFormat")
    Record = lazy("bear_shelf.datastore.record", "Record")


def get_arr() -> Array:
    """Return a new multiline TOML array."""
    arr: Array = array()
    arr.multiline(multiline=True)
    return arr


ARBITRARY_CACHE_SIZE: int = 256


@lru_cache(maxsize=ARBITRARY_CACHE_SIZE)  # Cache Value is Arbitrary 🤷 Deal with it Claude
def get_cached_header(header_data: FrozenDict) -> Table:
    """Get cached header from TOML storage."""
    header: Table = toml_table()
    for k, v in header_data.items():
        header[k] = v
    return header


def get_columns_array(columns_frozen: tuple) -> tuple[Array, tuple[str]]:
    """Cache the columns array for a table."""
    arr: Array = get_arr()
    for col_dict in columns_frozen:
        col_table: InlineTable = inline_table()
        for k, v in col_dict.items():
            col_table[k] = v
        arr.append(col_table)
    return arr, tuple(col_dict["name"] for col_dict in columns_frozen)


# @lru_cache(maxsize=ARBITRARY_CACHE_SIZE)  # 💙🐢✨
def get_cached_records_array(records_frozen: tuple, valid_columns: tuple[str]) -> Array:
    """Cache the records for a table, filtering by valid columns."""
    records_arr: Array = get_arr()
    for record_dict in records_frozen:
        record_table: InlineTable = inline_table()
        filtered_record: dict[str, Any] = {k: v for k, v in record_dict.items() if k in valid_columns}
        for k, v in filtered_record.items():
            if v is None:
                continue
            record_table[k] = v
        records_arr.append(record_table)
    return records_arr


class TomlStorage(Storage):
    """A TOML file storage backend using the unified data format."""

    def __init__(self, file: str | Path, file_mode: str = "r+", encoding: str = "utf-8") -> None:
        """Initialize TOML storage.

        Args:
            file: Path to the TOML file
            file_mode: File mode for opening (default: "r+" for read/write)
            encoding: Text encoding to use (default: "utf-8")
        """
        super().__init__()
        self.logger: Logger = get_logger("TomlStorage")
        self.file: Path = touch(file, mkdir=True, create_file=True)
        self.handler: TextFileHandler = TextFileHandler(self.file, mode=file_mode, encoding=encoding)
        self.logger.debug(f"TomlStorage initialized with file: {self.file}")

    def read(self) -> UnifiedDataFormat | None:
        """Read data from TOML file.

        Returns:
            UnifiedDataFormat instance or None if empty.

        Note:
            Extra fields in records not matching the schema columns are filtered out.
        """
        try:
            text: str = self.handler.read()
            self.logger.debug(f"Raw text read from TOML file {self.file}: {truncate(text, max_length=50)}")
            if text.strip():
                data: dict[str, Any] = tomllib_loads(text)
                unified: UnifiedDataFormat = UnifiedDataFormat.model_validate(data)
                self.logger.debug(f"Read data from TOML storage at {self.file}: {unified}")
                for table_data in unified.tables.values():
                    valid_columns: set[str] = {col.name for col in table_data.columns}
                    filtered_records: list[Record] = []
                    for record in table_data.records:
                        filtered_record: dict[str, Any] = {k: v for k, v in record.items() if k in valid_columns}
                        filtered_records.append(Record(**filtered_record))
                    table_data.records = filtered_records
                return unified
            return UnifiedDataFormat()
        except (ValueError, OSError, ValidationError) as e:
            self.logger.error(f"Error reading TOML storage from {self.file}: {e}")
            return None

    def write(self, data: UnifiedDataFormat) -> None:
        """Write data to TOML file with pretty inline formatting.

        Args:
            data: UnifiedDataFormat instance to write.
        """
        doc: TOMLDocument = toml_document()
        header: Table = get_cached_header(data.header.frozen_dump())
        doc.add("header", header)

        tables: Table = toml_table()
        for table_name, table_data in data.tables.items():
            table: Table = toml_table()
            frozen_cols: tuple[FrozenDict, ...] = tuple(col.frozen_dump() for col in table_data.columns)
            columns_arr, valid_columns = get_columns_array(frozen_cols)
            table.add("columns", columns_arr)
            frozen_recs = tuple(rec.frozen_dump() for rec in table_data.records)
            records_arr: Array = get_cached_records_array(frozen_recs, valid_columns)
            table.add("records", records_arr)
            tables.add(table_name, table)
        doc.add("tables", tables)
        self.logger.debug(f"Writing data to TOML storage at {self.file}: {doc}")
        self.handler.write(tomlkit_dumps(doc))

    def close(self) -> None:
        """Close the file handle."""
        self.logger.debug(f"Closing TomlStorage for file: {self.file}: {self.closed=}")
        if self.closed:
            return
        self.handler.close()

    @property
    def closed(self) -> bool:
        """Check if the storage is closed."""
        return self.handler.closed


__all__ = ["TomlStorage"]
