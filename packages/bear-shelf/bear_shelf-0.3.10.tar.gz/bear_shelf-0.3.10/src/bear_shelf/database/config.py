"""Database configuration utilities."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

from lazy_bear import lazy

from bear_shelf.models import Password

if TYPE_CHECKING:
    from pydantic import SecretStr

    from bear_shelf.database.schemas import DatabaseConfig, DBConfig, Schemas, get_defaults
    from bear_shelf.datastore.storage._common import StorageChoices
else:
    DatabaseConfig, DBConfig, Schemas, get_defaults = lazy("bear_shelf.database.schemas").to(
        "DatabaseConfig", "DBConfig", "Schemas", "get_defaults"
    )


def get_default_config(
    schema: Schemas,
    host: str | None = None,
    port: int | None = None,
    name: str | None = None,
    path: str | None = None,
    user: str | None = None,
    password: str | SecretStr | None = None,
) -> DatabaseConfig:
    """Get the default database configuration for a given scheme."""
    defaults: DBConfig = get_defaults(schema)
    return DatabaseConfig(
        scheme=schema,
        host=host or defaults.host,
        port=port or defaults.port,
        name=name or (defaults.name if schema not in {"sqlite", "bearshelf"} else None),
        path=path or (defaults.name if schema in {"sqlite", "bearshelf"} else None),
        username=user or defaults.username,
        password=Password.load(password) if password else None,
    )


def sqlite_memory_db() -> DatabaseConfig:
    """Get a SQLite in-memory database configuration."""
    return DatabaseConfig(scheme="sqlite", name=":memory:")


def sqlite_default_db() -> DatabaseConfig:
    """Get a SQLite default database configuration."""
    return get_default_config(schema="sqlite")


def mysql_default_db() -> DatabaseConfig:
    """Get a MySQL default database configuration."""
    return get_default_config(schema="mysql")


def postgres_default_db() -> DatabaseConfig:
    """Get a PostgreSQL default database configuration."""
    return get_default_config(schema="postgresql")


DEFAULT_STORAGE: Final[str] = "toml"


def bearshelf_default_db(
    path: Path | str,
    storage: StorageChoices | None = None,
    default: StorageChoices = DEFAULT_STORAGE,
) -> DatabaseConfig:
    """Get a BearShelf default database configuration.

    Args:
        path: Path to the database file. The file extension determines the storage format:
            - .jsonl: JSON Lines format
            - .json: JSON format
            - .yaml or .yml: YAML format
            - .xml: XML format
            - .toml: TOML format (default)
            - .msgpack: MessagePack format
        storage: Optional storage backend specification. If provided, overrides file extension.
        default: Default storage format to use if no extension or storage specified.

    Returns:
        DatabaseConfig: A BearShelf database configuration.
    """
    from bear_shelf.config import EXT_TO_STORAGE, STORAGE_TO_EXT  # noqa: PLC0415

    path_obj = Path(path)
    suffix: str = path_obj.suffix.lower()

    if storage is not None:
        chosen_storage: StorageChoices = storage
    elif suffix in EXT_TO_STORAGE:
        chosen_storage = EXT_TO_STORAGE[suffix]
    else:
        chosen_storage = default
    expected_extension: str = STORAGE_TO_EXT.get(chosen_storage, f".{chosen_storage}")
    final_path: Path | str = (
        path_obj.with_suffix(expected_extension) if not suffix or suffix != expected_extension else path
    )
    return get_default_config(schema="bearshelf", path=str(final_path))


__all__ = [
    "bearshelf_default_db",
    "get_default_config",
    "mysql_default_db",
    "postgres_default_db",
    "sqlite_default_db",
    "sqlite_memory_db",
]
