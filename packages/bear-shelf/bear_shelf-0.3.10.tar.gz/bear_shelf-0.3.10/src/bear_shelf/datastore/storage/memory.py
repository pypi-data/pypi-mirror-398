"""In-memory storage backend for the datastore."""

from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
from pathlib import Path
from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

from ._common import Storage

if TYPE_CHECKING:
    from logging import Logger

    from bear_shelf._logger import get_logger
    from bear_shelf.datastore.unified_data import UnifiedDataFormat
else:
    get_logger = lazy("bear_shelf._logger", "get_logger")
    UnifiedDataFormat = lazy("bear_shelf.datastore.unified_data", "UnifiedDataFormat")


class InMemoryStorage(Storage):
    """Simple in-memory storage backend for testing or temporary data."""

    class _Handle:
        def __init__(self, closer: Callable[[], None] | None = None) -> None:
            self.clear_callback: Callable[[], None] | None = closer

        def clear(self) -> None:
            if self.clear_callback is not None:
                self.clear_callback()
                self.clear_callback = None

    def __init__(self, file: str | Path | None = None, data: UnifiedDataFormat | None = None) -> None:
        """Initialize empty in-memory storage."""
        super().__init__()
        self.logger: Logger = get_logger("InMemoryStorage")
        self.file: Path = Path.cwd() if file is None else Path(file)
        self.handle = self._Handle(self.close)
        self._data: UnifiedDataFormat = data if data is not None else UnifiedDataFormat()
        self.logger.debug(f"InMemoryStorage initialized with file: {self.file}")

    def read(self) -> UnifiedDataFormat:
        """Read data from memory.

        Returns:
            Stored data or None if empty
        """
        return self._data

    def get(self, k: str, default: Any = None) -> Any:
        """Get attribute from stored data.

        Args:
            k: Attribute name
            default: Default value if attribute not found
        Returns:
            Attribute value or default
        """
        return getattr(self._data, k, default)

    def write(self, data: UnifiedDataFormat | None = None, **kwargs) -> None:
        """Write data to memory.

        Args:
            data: Data to store
        """
        if data is not None:
            self._data = data
        if kwargs:
            for key, value in kwargs.items():
                setattr(self._data, key, value)

    def close(self) -> None:
        """Clear the stored data."""
        self.logger.debug(f"In memory storage close called for file: {self.file}: {self.closed=}")
        if self._data is not None:
            self._data.clear()

    @property
    def closed(self) -> bool:
        """Check if the storage is closed (empty)."""
        return self._data is None


__all__ = ["InMemoryStorage"]
