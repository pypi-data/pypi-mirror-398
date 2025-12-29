"""A storage for TOON files using the unified data format."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy
from pydantic import ValidationError

from bear_shelf.datastore.columns import Columns

from ._common import Storage

if TYPE_CHECKING:
    from logging import Logger
    from pathlib import Path

    from bear_shelf._logger import get_logger
    from bear_shelf.datastore.unified_data import UnifiedDataFormat
    from codec_cub.config import ToonCodecConfig
    from codec_cub.general.helpers import touch
    from codec_cub.text.file_handler import TextFileHandler
    from codec_cub.toon import ToonFileHandler, tabular, toon_dumps
else:
    ToonCodecConfig = lazy("codec_cub.config", "ToonCodecConfig")
    TextFileHandler = lazy("codec_cub.text.file_handler", "TextFileHandler")
    ToonFileHandler, tabular, toon_dumps = lazy("codec_cub.toon", "ToonFileHandler", "tabular", "toon_dumps")
    touch = lazy("codec_cub.general.helpers", "touch")
    get_logger = lazy("bear_shelf._logger", "get_logger")
    UnifiedDataFormat = lazy("bear_shelf.datastore.unified_data", "UnifiedDataFormat")


class ToonStorage(Storage):
    """A TOON file storage backend using the unified data format."""

    def __init__(self, file: str | Path, **kwargs) -> None:
        """Initialize TOON storage.

        Args:
            file: Path to the TOON file
            file_mode: File mode for opening (default: "r+b" for binary read/write)
        """
        super().__init__()
        self.logger: Logger = get_logger("ToonStorage")
        self.file: Path = touch(file, mkdir=True, create_file=True)
        self.handler: ToonFileHandler = ToonFileHandler(file=self.file, config=ToonCodecConfig(**kwargs))
        self.txt_handler: TextFileHandler = TextFileHandler(self.file)
        self.logger.debug(f"ToonStorage initialized with file: {self.file}")

    def read(self) -> UnifiedDataFormat | None:
        """Read data from TOON file.

        Returns:
            UnifiedDataFormat instance or empty if file doesn't exist.
        """
        try:
            toon_data: dict[str, Any] | list[Any] | None = self.handler.read()
            self.logger.debug(f"Read data from TOON storage at {self.file}: {toon_data}")
            if toon_data is None:
                return UnifiedDataFormat()
            model: UnifiedDataFormat = UnifiedDataFormat.model_validate(toon_data)
            return model
        except (ValueError, OSError, ValidationError) as e:
            self.logger.error(f"Error reading TOON storage from {self.file}: {e}")
            return None

    def write(self, data: UnifiedDataFormat, exclude_none: bool = True) -> None:  # noqa: ARG002
        """Write data to TOON file.

        Args:
            data: UnifiedDataFormat instance to write.
        """
        column_fields: list[str] = Columns.fields()

        # toon_data: dict = data.model_dump(exclude_none=exclude_none)

        toon_data: dict[str, Any] = {
            "header": data.header.model_dump(),
            "tables": {},
        }

        for table_name, table_data in data.tables.items():
            record_fields: list[str] = [col.name for col in table_data.columns]
            toon_data["tables"][table_name] = {
                "columns": tabular(
                    rows=[col.model_dump() for col in table_data.columns],
                    fields=column_fields,
                ),
                "records": tabular(
                    rows=[rec.model_dump() for rec in table_data.records],
                    fields=record_fields,
                    fill_missing=True,
                ),
            }

        self.logger.debug(f"Writing data to TOON storage at {self.file}: {toon_data}")
        self.txt_handler.write(toon_dumps(toon_data))

    def close(self) -> None:
        """Close the file handle (no-op for TOON handler)."""
        self.logger.debug(f"Closing ToonStorage for file: {self.file} {self.closed=}")
        if self.closed:
            return
        self.handler.close()

    @property
    def closed(self) -> bool:
        """Check if the storage is closed."""
        return self.handler.closed
