"""YAML storage backend for the datastore.

Provides YAML file storage using the unified data format.
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
    from codec_cub.yamls.file_handler import FlowDict, YamlFileHandler
else:
    get_logger = lazy("bear_shelf._logger", "get_logger")
    touch = lazy("codec_cub.general.helpers", "touch")
    YamlFileHandler, FlowDict = lazy("codec_cub.yamls.file_handler", "YamlFileHandler", "FlowDict")
    UnifiedDataFormat = lazy("bear_shelf.datastore.unified_data", "UnifiedDataFormat")


class YamlStorage(Storage):
    """A YAML file storage backend using the unified data format."""

    def __init__(self, file: str | Path, file_mode: str = "r+", encoding: str = "utf-8") -> None:  # noqa: ARG002
        """Initialize YAML storage.

        Args:
            file: Path to the YAML file
            file_mode: File mode (unused, kept for API consistency)
            encoding: Text encoding to use (default: "utf-8")
        """
        super().__init__()
        self.logger: Logger = get_logger("YamlStorage")
        self.file: Path = touch(file, mkdir=True, create_file=True)
        self.handler: YamlFileHandler = YamlFileHandler(self.file, encoding=encoding, safe_mode=False, width=120)
        self.logger.debug(f"YamlStorage initialized with file: {self.file}")

    def read(self) -> UnifiedDataFormat | None:
        """Read data from YAML file.

        Returns:
            UnifiedDataFormat instance or empty if file doesn't exist.
        """
        try:
            yaml_data: dict[str, Any] | None = self.handler.read()
            if not yaml_data:
                return UnifiedDataFormat()
            return UnifiedDataFormat.model_validate(yaml_data)
        except (ValueError, OSError, ValidationError) as e:
            self.logger.error(f"Error reading YAML storage from {self.file}: {e}")
            return None

    def write(self, data: UnifiedDataFormat) -> None:
        """Write data to YAML file with pretty formatting.

        Args:
            data: UnifiedDataFormat instance to write.
        """
        yaml_data: dict = data.model_dump(exclude_none=True)
        for table in yaml_data.get("tables", {}).values():
            if "columns" in table:
                table["columns"] = [FlowDict(c) for c in table["columns"]]
            if "records" in table:
                table["records"] = [FlowDict(r) for r in table["records"]]

        self.logger.debug(f"Writing data to YAML storage at {self.file}: {yaml_data}")
        self.handler.write(yaml_data)

    def close(self) -> None:
        """Close the file handle (no-op for YAML handler)."""
        self.logger.debug(f"Closing YamlStorage for file: {self.file} {self.closed=}")
        if self.closed:
            return
        self.handler.close()

    @property
    def closed(self) -> bool:
        """Check if the storage is closed (always returns False for YAML)."""
        return False


__all__ = ["YamlStorage"]
