"""Common utilities and dataclasses for the Bear Shelf SQLAlchemy dialect."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, NamedTuple

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import ReflectedForeignKeyConstraint
    from sqlalchemy.engine.url import URL

    from bear_shelf.datastore.storage._common import StorageChoices

TRUE_VALUES: tuple = (True, "auto")
"""Values that represent True for autoincrement."""


def ensure_file_extension(path: Path, storage_type: StorageChoices) -> Path:
    """Ensure the database path has the correct extension for the storage type.

    Args:
        path (Path): The original database file path
        storage_type (StorageChoices): The storage backend type

    Returns:
        Path with the correct extension for the storage type
    """
    from bear_shelf.config import STORAGE_TO_EXT  # noqa: PLC0415

    if storage_type == "memory":
        return path

    expected_ext: str = STORAGE_TO_EXT.get(storage_type, ".jsonl")

    if not path.suffix or path.suffix != expected_ext:
        return path.with_suffix(expected_ext)
    return path


def get_database_path_from_url(url: URL, storage_type: StorageChoices = "jsonl") -> DatabasePathInfo:
    """Determine the database file path from the given URL.

    Args:
        url (URL): The SQLAlchemy database URL
        storage_type (StorageChoices): The storage backend type

    Returns:
        tuple[str, StorageChoices]: A tuple containing the database file path and storage type
    """
    from bear_shelf.config import APP_CONFIG, EXT_TO_STORAGE  # noqa: PLC0415

    if url.database and not url.host:
        database_path = Path(url.database)
    elif url.database and url.host:
        database_path: Path = (Path(url.host) / url.database).absolute()
    else:
        database_path = Path(f"./default{APP_CONFIG.info.default_extension}")

    if database_path.suffix in APP_CONFIG.info.valid_extensions:
        storage_type = EXT_TO_STORAGE[database_path.suffix]
    else:
        database_path = ensure_file_extension(database_path, storage_type)
    return DatabasePathInfo(str(database_path), storage_type)


class DatabasePathInfo(NamedTuple):
    """Dataclass to store database path information."""

    path: str
    """The database file path."""
    storage: StorageChoices
    """The storage backend type."""


class DBPathReturn(NamedTuple):
    """Dataclass to store database path return information."""

    path: list[str]
    """The database file path."""
    opts: dict[str, str]
    """The options dictionary."""


class Result(NamedTuple):
    """Result of an aggregate function."""

    n: float


@dataclass(slots=True)
class AggregateResult:
    """Dataclass to store aggregate function result."""

    _value: Result | None
    """The aggregate value."""
    _label: str | None
    """The label for the aggregate value."""

    @property
    def not_null(self) -> bool:
        """Check if both value and label are not None."""
        return self._value is not None and self._label is not None

    @property
    def value(self) -> Result:
        """Get the aggregate value."""
        if self._value is None:
            raise ValueError("Aggregate value is None")
        return self._value

    @property
    def label(self) -> str:
        """Get the label for the aggregate value."""
        if self._label is None:
            raise ValueError("Aggregate label is None")
        return self._label


NULL_RESULT: Final = AggregateResult(None, None)


@dataclass(slots=True)
class FKInfo:
    """Dataclass to store foreign key information."""

    name: str | None = None
    comment: str | None = None
    referred_schema: str | None = None
    referred_table: str = ""
    constrained_columns: list[str] = field(default_factory=list)
    referred_columns: list[str] = field(default_factory=list)
    options: dict[str, Any] | None = None

    def output(self, exclude: set[str] | None = None) -> ReflectedForeignKeyConstraint:
        """Output the foreign key information as a dictionary, excluding specified fields.

        Args:
            exclude (set[str] | None): A set of field names to exclude from the output
        Returns:
            ReflectedForeignKeyConstraint: The foreign key information as a dictionary
        """
        fields: dict[str, Any] = {
            "name": self.name,
            "comment": self.comment,
            "referred_schema": self.referred_schema,
            "referred_table": self.referred_table,
            "constrained_columns": self.constrained_columns,
            "referred_columns": self.referred_columns,
            "options": self.options,
        }

        if exclude is None:
            exclude = set()

        return {field: getattr(self, field) for field in fields if field not in exclude}  # pyright: ignore[reportReturnType]


def make_statement(*strs: str) -> str:
    """Concatenate multiple strings into a single SQL statement.

    Args:
        *strs (str): The strings to concatenate

    Returns:
        str: The concatenated SQL statement
    """
    return " ".join(strs).strip()
