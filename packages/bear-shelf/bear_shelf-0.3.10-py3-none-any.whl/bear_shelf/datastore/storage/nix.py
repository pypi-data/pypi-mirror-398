"""Nix storage backend for the datastore.

Provides Nix file storage using the unified data format.
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
    from codec_cub.config import NixCodecConfig
    from codec_cub.general.helpers import touch
    from codec_cub.nix.codec import NixCodec
    from codec_cub.nix.file_handler import NixFileHandler
else:
    get_logger = lazy("bear_shelf._logger", "get_logger")
    NixCodecConfig = lazy("codec_cub.config", "NixCodecConfig")
    NixCodec = lazy("codec_cub.nix.codec", "NixCodec")
    NixFileHandler = lazy("codec_cub.nix.file_handler", "NixFileHandler")
    touch = lazy("codec_cub.general.helpers", "touch")
    UnifiedDataFormat = lazy("bear_shelf.datastore.unified_data", "UnifiedDataFormat")


class NixStorage(Storage):
    """A Nix file storage backend using the unified data format."""

    def __init__(self, file: str | Path, file_mode: str = "r+", encoding: str = "utf-8") -> None:  # noqa: ARG002
        """Initialize Nix storage.

        Args:
            file: Path to the Nix file
            file_mode: File mode (unused, kept for API consistency)
            encoding: Text encoding to use (default: "utf-8")
        """
        super().__init__()
        self.logger: Logger = get_logger("NixStorage")
        self.file: Path = touch(file, mkdir=True, create_file=True)
        self.codec = NixCodec(NixCodecConfig(inline_arrays=True, sort_keys=False, inline_lists=False))
        self.handler = NixFileHandler(self.file, touch=True, codec=self.codec)
        self.logger.debug(f"NixStorage initialized with file: {self.file}")

    def read(self) -> UnifiedDataFormat | None:
        """Read data from Nix file.

        Returns:
            UnifiedDataFormat instance or None if empty.
        """
        try:
            handler: NixFileHandler = self.handler
            data: Any | None = handler.read()
            model: UnifiedDataFormat = (
                UnifiedDataFormat.model_validate(data) if data is not None else UnifiedDataFormat()
            )
            self.logger.debug(f"Read data from Nix storage at {self.file}: {model}")
            return model
        except (ValueError, OSError, ValidationError) as e:
            self.logger.error(f"Error reading Nix storage from {self.file}: {e}")
            return None

    def write(self, data: UnifiedDataFormat) -> None:
        """Write data to Nix file with pretty formatting.

        Args:
            data: UnifiedDataFormat instance to write.
        """
        nix_data: dict[str, Any] = data.model_dump(exclude_none=True)
        self.logger.debug(f"Writing data to Nix storage at {self.file}: {nix_data}")
        self.handler.write(nix_data)

    def close(self) -> None:
        """Close the file handle."""
        self.logger.debug(f"Closing NixStorage for file: {self.file}: {self.closed=}")
        if self.closed:
            return
        self.handler.close()

    @property
    def closed(self) -> bool:
        """Check if the storage is closed."""
        return self.handler.closed


__all__ = ["NixStorage"]
