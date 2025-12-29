"""Configuration management for JSONL Database."""

from os import getenv
from typing import Final, Literal, NamedTuple

from bear_shelf._internal._info import METADATA, _ProjectMetadata

CUSTOM_TYPE_MAP: Final[dict[str, type]] = {"epochtimestamp": int, "datetime": str}

type StorageChoices = Literal["json", "toon", "jsonl", "memory", "msgpack", "nix", "toml", "xml", "yaml", "default"]

UNIFIED_DATA_VERSION = "1.1.0"
"""The current version of the unified data format."""


STORAGE_TO_EXT: Final[dict[StorageChoices, str]] = {
    "jsonl": ".jsonl",
    "json": ".json",
    "toml": ".toml",
    "xml": ".xml",
    "yaml": ".yaml",
    "msgpack": ".msgpack",
    "nix": ".nix",
    "toon": ".toon",
    "memory": ":memory:",  # We use :memory: to indicate in-memory storage
}
"""Mapping of storage backend types to file extensions."""

EXT_TO_STORAGE: Final[dict[str, StorageChoices]] = {
    ".jsonl": "jsonl",
    ".json": "json",
    ".toml": "toml",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".msgpack": "msgpack",
    ".nix": "nix",
    ".toon": "toon",
    ":memory:": "memory",
}
"""Mapping of file extensions to storage backend types."""


VALID_EXTENSIONS: frozenset[str] = frozenset(EXT_TO_STORAGE.keys())
"""A frozenset of valid file extensions for database files."""
VALID_STORAGES: frozenset[StorageChoices] = frozenset(STORAGE_TO_EXT.keys())
"""A frozenset of valid storage backend types."""

assert len(VALID_EXTENSIONS) == len(EXT_TO_STORAGE), "EXT_TO_STORAGE mapping has duplicate extensions."  # noqa: S101
assert len(VALID_STORAGES) == len(STORAGE_TO_EXT), "STORAGE_TO_EXT mapping has duplicate storage types."  # noqa: S101


class DialectInfo(NamedTuple):
    """Dataclass to store SQLAlchemy dialect information."""

    dialect: str = "bearshelf"
    """The name of the dialect."""
    driver: str = "bearshelf"
    """The name of the driver."""
    param_style: str = "named"
    """The parameter style used by the dialect."""
    default_extension: str = ".jsonl"
    """The default file extension for database files."""
    ddl_comment_prefix: str = "/* bearshelf:"
    """The prefix for DDL comments in compiled statements."""
    module_path: str = "bear_shelf.dialect.bear_dialect"
    """The module path for the dialect."""
    class_name: str = "BearShelfDialect"
    """The class name of the dialect."""
    valid_storages: frozenset[StorageChoices] = VALID_STORAGES
    """A tuple of valid storage backend types."""
    valid_extensions: frozenset[str] = VALID_EXTENSIONS
    """A tuple of valid file extensions for database files."""
    unified_data_version: str = UNIFIED_DATA_VERSION
    """The version of the unified data format."""


class AppConfig(NamedTuple):
    """Application configuration model."""

    env: str = getenv(METADATA.env_variable, "prod")
    debug: bool = getenv(f"{METADATA.name_upper}_DEBUG", "false").lower() in {"1", "true", "yes", "on"}
    log_to_console: bool = True
    """Whether to log to the console."""
    log_to_file: bool = False
    """Whether to log to a file."""
    log_file_path: str = "logs/bear_shelf.log"
    """The path to the log file."""
    log_level: str = "INFO"
    """The logging level."""
    max_file_size_mb: int = 5 * (1024 * 1024)
    """The maximum size of the log file in megabytes."""
    backup_count: int = 3
    """The number of backup log files to keep."""
    info: DialectInfo = DialectInfo()
    """Dialect information."""
    metadata: _ProjectMetadata = METADATA
    """Project metadata."""
    debug_env_var: str = f"{METADATA.name_upper}_DEBUG"
    """The environment variable to enable debug mode."""


APP_CONFIG: Final[AppConfig] = AppConfig()

__all__ = ["APP_CONFIG", "UNIFIED_DATA_VERSION", "AppConfig", "StorageChoices"]
