"""JSON storage backend for the datastore.

Provides JSON file storage using the unified data format.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy
from pydantic import ValidationError

from ._common import Storage

if TYPE_CHECKING:
    import json as _json
    from logging import Logger
    from pathlib import Path

    from bear_shelf._logger import get_logger
    from bear_shelf.datastore.unified_data import UnifiedDataFormat
    from codec_cub.general.helpers import touch
    from codec_cub.jsons.file_handler import JSONFileHandler
    from funcy_bear.constants.type_constants import JSONLike
else:
    _json = lazy("json")
    touch = lazy("codec_cub.general.helpers", "touch")
    get_logger = lazy("bear_shelf._logger", "get_logger")
    JSONFileHandler = lazy("codec_cub.jsons.file_handler", "JSONFileHandler")
    UnifiedDataFormat = lazy("bear_shelf.datastore.unified_data", "UnifiedDataFormat")


class JsonStorage(Storage):
    """A JSON file storage backend using the unified data format."""

    def __init__(self, file: str | Path, file_mode: str = "r+", encoding: str = "utf-8") -> None:
        """Initialize the JSON storage.

        Args:
            file: Path to the JSON file
            file_mode: File mode for opening (default: "r+" for read/write)
            encoding: Text encoding to use (default: "utf-8")
        """
        super().__init__()
        self.logger: Logger = get_logger("JsonStorage")
        self.file: Path = touch(file, mkdir=True, create_file=True)
        self.handler: JSONFileHandler = JSONFileHandler(file=self.file, mode=file_mode, encoding=encoding)
        self.logger.debug(f"JsonStorage initialized with file: {self.file}")

    def read(self) -> UnifiedDataFormat | None:
        """Read data from the JSON file.

        Returns:
            UnifiedDataFormat instance or None if empty.

        Note:
            Extra fields in records not matching the schema columns are filtered out.
        """
        try:
            data: JSONLike | Any = self.handler.read()
            if data:
                tables: dict[str, dict[str, Any]] = data.get("tables", {})
                for table_data in tables.values():
                    columns: list[dict[str, Any]] = table_data.get("columns", [])
                    valid_columns: set[str] = {col["name"] for col in columns}
                    records: list[dict[str, Any]] = table_data.get("records", [])
                    filtered_records: list[dict[str, Any]] = []
                    for record in records:
                        filtered_record: dict[str, Any] = {k: v for k, v in record.items() if k in valid_columns}
                        filtered_records.append(filtered_record)
                    table_data["records"] = filtered_records
                return UnifiedDataFormat.model_validate(data)
            return UnifiedDataFormat()
        except (ValueError, OSError, ValidationError) as e:
            self.logger.error(f"Error reading JSON storage from {self.file}: {e}")
            return None

    def write(self, data: UnifiedDataFormat) -> None:
        """Write data to the JSON file, replacing existing content.

        Args:
            data: UnifiedDataFormat instance to write.

        Note:
            Records are filtered to only include fields matching the schema columns.
        """
        data_dict: dict[str, Any] = data.model_dump(exclude_none=True)
        tables: dict[str, dict[str, Any]] = data_dict.get("tables", {})
        for table_data in tables.values():
            columns: list[dict[str, Any]] = table_data.get("columns", [])
            valid_columns: set[str] = {col["name"] for col in columns}
            records: list[dict[str, Any]] = table_data.get("records", [])
            filtered_records: list[dict[str, Any]] = []
            for record in records:
                filtered_record: dict[str, Any] = {k: v for k, v in record.items() if k in valid_columns}
                filtered_records.append(filtered_record)
            table_data["records"] = filtered_records
        json_str: str = _json.dumps(data_dict, indent=2)
        self.handler.write(json_str)
        self.logger.debug(f"Wrote data to JSON storage at {self.file}: {data_dict}")

    def close(self) -> None:
        """Close all file handles."""
        self.logger.debug(f"Closing JsonStorage for file: {self.file}: {self.closed=}")
        if self.closed:
            return
        self.handler.close()

    @property
    def closed(self) -> bool:
        """Check if all file handles are closed."""
        return self.handler.closed


__all__ = ["JsonStorage"]
