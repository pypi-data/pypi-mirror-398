"""MessagePack storage backend for the datastore.

Provides binary MessagePack file storage using the unified data format.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy
from pydantic import ValidationError

from ._common import Storage

if TYPE_CHECKING:
    from logging import Logger
    from pathlib import Path

    from bear_shelf._logger import get_logger
    from bear_shelf.datastore.unified_data import UnifiedDataFormat
    from codec_cub.general.helpers import touch
    from codec_cub.message_pack.file_handler import MsgPackFileHandler
else:
    get_logger = lazy("bear_shelf._logger", "get_logger")
    touch = lazy("codec_cub.general.helpers", "touch")
    MsgPackFileHandler = lazy("codec_cub.message_pack.file_handler", "MsgPackFileHandler")
    UnifiedDataFormat = lazy("bear_shelf.datastore.unified_data", "UnifiedDataFormat")


class MsgPackStorage(Storage):
    """A MessagePack binary file storage backend using the unified data format."""

    def __init__(self, file: str | Path, file_mode: str = "r+b") -> None:
        """Initialize the MessagePack storage.

        Args:
            file: Path to the MessagePack file
            file_mode: File mode for opening (default: "r+b" for binary read/write)
        """
        super().__init__()
        self.logger: Logger = get_logger("MsgPackStorage")
        self.file: Path = touch(file, mkdir=True, create_file=True)
        self.handler: MsgPackFileHandler = MsgPackFileHandler(file=self.file, mode=file_mode)
        self.logger.debug(f"MsgPackStorage initialized with file: {self.file}")

    def read(self) -> UnifiedDataFormat | None:
        """Read data from the MessagePack file.

        Returns:
            UnifiedDataFormat instance or None if empty.
        """
        try:
            data: Any = self.handler.read()
            self.logger.debug(f"Read data from MsgPack storage at {self.file}: {data}")
            if data is None:
                return UnifiedDataFormat()
            return UnifiedDataFormat.model_validate(data)
        except (ValueError, OSError, ValidationError) as e:
            self.logger.error(f"Error reading MsgPack storage from {self.file}: {e}")
            return None

    def write(self, data: UnifiedDataFormat) -> None:
        """Write data to the MessagePack file, replacing existing content.

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
        self.logger.debug(f"Writing data to MsgPack storage at {self.file}: {data_dict}")
        self.handler.write(data_dict)

    def close(self) -> None:
        """Close all file handles."""
        self.logger.debug(f"Closing MsgPackStorage for file: {self.file}: {self.closed=}")
        if self.closed:
            return
        self.handler.close()

    @property
    def closed(self) -> bool:
        """Check if all file handles are closed."""
        return self.handler.closed


__all__ = ["MsgPackStorage"]
