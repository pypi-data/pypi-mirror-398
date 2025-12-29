"""Database configuration schemas and defaults."""

from functools import cached_property
from typing import Literal, NamedTuple, Self

from pydantic import BaseModel, Field, SecretStr, model_validator

from bear_shelf.models import Password

Schemas = Literal["sqlite", "postgresql", "mysql", "bearshelf"]


class DBConfig(NamedTuple):
    """Information about a database schema."""

    name: str | None = None
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | Password | None = Password(None)


DEFAULT_CONFIGS: dict[str, DBConfig] = {
    "sqlite": DBConfig(name="database.db"),
    "postgresql": DBConfig(name="postgres", host="localhost", port=5432, username="postgres"),
    "mysql": DBConfig(name="mysql", host="localhost", port=3306, username="root"),
    "bearshelf": DBConfig(name="database.jsonl"),
}
FALLBACK: DBConfig = DEFAULT_CONFIGS["sqlite"]


def get_defaults(schema: Schemas) -> DBConfig:
    """Get the default database configuration for a given scheme.

    Args:
        schema (Schemas): The database schema to get the defaults for.

    Returns:
        DBConfig: The default database configuration for the given schema.
    """
    return DEFAULT_CONFIGS.get(schema, FALLBACK)


class DatabaseConfig(BaseModel):
    """Configuration for paths used in the application."""

    scheme: Schemas
    host: str | None = None
    port: int | None = Field(default=None, ge=0, le=65535)
    name: str | None = None
    path: str | None = Field(default=None, description="Path to the database file, only used for sqlite.")
    username: str | None = None
    password: Password | None = Field(default=Password(None))

    @model_validator(mode="after")
    def set_defaults(self) -> Self:
        """Set default values for missing fields based on the scheme."""
        defaults: DBConfig = get_defaults(self.scheme)
        match self.scheme:
            case "sqlite" | "bearshelf":
                self.name = self.path or self.name or defaults.name
                self.path = None  # We never use path in the db_url construction, only for config convenience
            case "postgresql" | "mysql":
                self.host = self.host or defaults.host
                self.name = self.name or defaults.name
                self.port = self.port if bool(self.port) else defaults.port
                self.username = self.username or defaults.username
        return self

    @cached_property
    def db_url(self) -> SecretStr:
        """Get the database URL as a SecretStr since it may contain a password.

        This is a little paranoid but it's better than to accidentally log a password.

        Example:
            ``postgresql://user:password@localhost:5432/dbname``

            ``mysql://user:password@localhost:3306/dbname``

            ``sqlite:///path/to/database.db``

        Returns:
            SecretStr: The database URL as a SecretStr, you will need to call
            get_secret_value() to get the string.
        """
        url: str = f"{self.scheme}://"
        if self.username:
            url += self.username
            if self.password and not self.password.is_null():
                url += f":{self.password.get_secret_value()}"
            url += "@"
        if self.host:
            url += self.host
        if self.port:
            url += f":{self.port}"
        if self.name:
            url += f"/{self.name}"
        return SecretStr(url)

    @classmethod
    def by_schema(
        cls,
        scheme: Schemas,
        host: str | None = None,
        port: int | None = None,
        name: str | None = None,
        path: str | None = None,
        username: str | None = None,
    ) -> Self:
        """Create a DatabaseConfig with default values for the given scheme."""
        defaults: DBConfig = get_defaults(scheme)
        return cls(
            scheme=scheme,
            host=host or defaults.host,
            port=port or defaults.port,
            name=path or name or defaults.name,
            username=username or defaults.username,
        )


__all__ = ["DatabaseConfig", "Schemas"]
