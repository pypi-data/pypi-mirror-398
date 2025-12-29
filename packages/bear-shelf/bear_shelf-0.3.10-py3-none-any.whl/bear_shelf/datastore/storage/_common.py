"""Common dynamic storage interface and factory function."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, overload

from bear_shelf.config import StorageChoices

if TYPE_CHECKING:
    from pathlib import Path

    from .json import JsonStorage
    from .jsonl import JSONLStorage
    from .memory import InMemoryStorage
    from .msgpack import MsgPackStorage
    from .nix import NixStorage
    from .toml import TomlStorage
    from .toon import ToonStorage
    from .xml import XMLStorage
    from .yaml import YamlStorage


class Storage[T](ABC):
    """Abstract base class for all storage backends.

    A Storage handles serialization/deserialization of database state
    to/from various backends (files, memory, etc.).
    """

    file: Path
    handler: Any

    @abstractmethod
    def read(self) -> T:
        """Read the current state from storage.

        Any kind of deserialization should go here.

        Returns:
            Loaded data or None if storage is empty.
        """
        raise NotImplementedError("To be overridden!")

    @abstractmethod
    def write(self, data: T) -> None:
        """Write the current state to storage.

        Any kind of serialization should go here.

        Args:
            data: The current state of the database.
        """
        raise NotImplementedError("To be overridden!")

    def clear(self) -> None:
        """Clear all data from the storage."""
        self.handler.clear()

    @abstractmethod
    def close(self) -> None:
        """Close open file handles or cleanup resources."""

    @property
    @abstractmethod
    def closed(self) -> bool:
        """Check if the storage is closed."""
        raise NotImplementedError("To be overridden!")

    def __getattr__[V](self, name: str) -> V:  # pyright: ignore[reportInvalidTypeVarUse]
        """Forward all unknown attribute calls to the underlying storage."""
        return getattr(self, name)

    def __repr__(self) -> str:
        """Return a string representation of the storage."""
        return f"<{self.__class__.__name__} file={self.file} closed={self.closed}>"


class StorageModule(NamedTuple):
    """Storage module information."""

    path: str
    name: str

    @property
    def import_path(self) -> str:
        """The full import path for the storage module."""
        return f"bear_shelf.datastore.storage{self.path}"

    def import_it(self) -> type[Storage]:
        """Import and return the storage module class."""
        return getattr(__import__(self.import_path, fromlist=[self.name]), self.name)


_STORAGE_MODULE_MAP: dict[str, StorageModule] = {
    "json": StorageModule(".json", "JsonStorage"),
    "jsonl": StorageModule(".jsonl", "JSONLStorage"),
    "memory": StorageModule(".memory", "InMemoryStorage"),
    "msgpack": StorageModule(".msgpack", "MsgPackStorage"),
    "nix": StorageModule(".nix", "NixStorage"),
    "toml": StorageModule(".toml", "TomlStorage"),
    "xml": StorageModule(".xml", "XMLStorage"),
    "yaml": StorageModule(".yaml", "YamlStorage"),
    "toon": StorageModule(".toon", "ToonStorage"),
    "default": StorageModule(".jsonl", "JSONLStorage"),
}

_storage_cache: dict[str, type[Storage]] = {}


@overload
def get_storage(storage: Literal["json"]) -> type[JsonStorage]: ...
@overload
def get_storage(storage: Literal["jsonl"]) -> type[JSONLStorage]: ...
@overload
def get_storage(storage: Literal["memory"]) -> type[InMemoryStorage]: ...
@overload
def get_storage(storage: Literal["msgpack"]) -> type[MsgPackStorage]: ...
@overload
def get_storage(storage: Literal["toml"]) -> type[TomlStorage]: ...
@overload
def get_storage(storage: Literal["xml"]) -> type[XMLStorage]: ...
@overload
def get_storage(storage: Literal["yaml"]) -> type[YamlStorage]: ...
@overload
def get_storage(storage: Literal["toon"]) -> type[ToonStorage]: ...
@overload
def get_storage(storage: Literal["nix"]) -> type[NixStorage]: ...
@overload
def get_storage(storage: Literal["default"]) -> type[JSONLStorage]: ...
def get_storage(storage: StorageChoices) -> type[Storage]:
    """Factory function to get a storage backend by name.

    Args:
        storage: Storage backend name

    Returns:
        Storage backend class
    """
    if storage not in _STORAGE_MODULE_MAP:
        storage = "default"

    storage_type: type[Storage] | None = _storage_cache.get(storage)
    if storage_type is None:
        info: StorageModule = _STORAGE_MODULE_MAP[storage]
        storage_type = info.import_it()
        _storage_cache[storage] = storage_type
    return storage_type


__all__ = ["Storage", "StorageChoices", "get_storage"]
