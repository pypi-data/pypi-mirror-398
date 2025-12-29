"""A set of general-purpose Pydantic models and utilities."""

from typing import Any, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SecretStr,
    SerializerFunctionWrapHandler,
    field_serializer,
    field_validator,
)


class ExtraIgnoreModel(BaseModel):
    """A Pydantic model that ignores extra fields."""

    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)


def extract_field_attrs[T](model: type[BaseModel], expected_type: type[T], attr: str = "default") -> dict[str, T]:
    """Extract specified attribute from model fields if of expected type.

    Args:
        model: Pydantic model class
        expected_type: Expected type of the attribute value
        attr: Attribute name to extract (default: "default")

    Returns:
        Dictionary of field names to attribute values
    """
    from pydantic.fields import FieldInfo

    extracted: dict[str, T] = {}
    for field_name, field in model.model_fields.items():
        if isinstance(field, FieldInfo) and hasattr(field, "annotation"):
            attr_value: Any | None = getattr(field, attr, None)
            if isinstance(attr_value, expected_type):
                extracted[field_name] = attr_value
    return extracted


class SecretModel(RootModel[SecretStr | None]):
    """A model to securely handle secrets that can be reused."""

    model_config = ConfigDict(frozen=True, validate_by_name=True)
    root: SecretStr | None = Field(default=None, alias="secret")

    @field_validator("root", mode="before")
    @classmethod
    def convert_secret(cls, v: Any) -> SecretStr | None:
        """Convert a string to SecretStr."""
        if isinstance(v, str):
            if v.lower() in {"null", "none", "****", ""}:
                return None
            return SecretStr(v)
        return v

    @field_serializer("root", mode="wrap")
    def serialize_path(self, value: Any, nxt: SerializerFunctionWrapHandler) -> str:
        """Serialize the secret to a string."""
        secret_value: SecretStr | None = nxt(value)
        if secret_value is None:
            return "null"
        return "****"

    def get_secret_value(self) -> str:
        """Get the secret value as a string."""
        if self.root is None:
            raise ValueError("Secret is not set")
        return self.root.get_secret_value()

    def is_null(self) -> bool:
        """Check if the secret is None."""
        return self.root is None

    def __str__(self) -> str:
        return str(self.root)

    def __repr__(self) -> str:
        return repr(self.root)

    @classmethod
    def load(cls, secret: str | SecretStr | None = None) -> Self:
        """Create a Secret from a string."""
        return cls.model_construct(root=cls.convert_secret(secret))


class Password(SecretModel):
    """A model to securely handle passwords."""

    root: SecretStr | None = Field(default=None, alias="password")


# ruff: noqa: PLC0415
