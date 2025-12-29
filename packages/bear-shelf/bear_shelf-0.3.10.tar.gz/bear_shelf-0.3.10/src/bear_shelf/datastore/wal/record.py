"""Write-Ahead Log Record Model."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from lazy_bear import lazy
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_serializer, field_validator

if TYPE_CHECKING:
    from zlib import crc32

    from bear_epoch_time import EpochTimestamp
else:
    EpochTimestamp = lazy("bear_epoch_time", "EpochTimestamp")
    crc32 = lazy("zlib", "crc32")


def compute_checksum(data: str) -> str:
    """Compute a checksum for the given data string."""
    return str(crc32(data.encode("utf-8")) & 0xFFFFFFFF)


def get_timestamp() -> int:
    """Get the current epoch timestamp as an integer."""
    return int(EpochTimestamp.now())


class Operation(StrEnum):
    """Enumeration of WAL operations."""

    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    COMMIT = "COMMIT"


class WALRecord(BaseModel):
    """A record in the Write-Ahead Log."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    txid: int
    op: Operation
    data: dict[str, Any] | None = Field(default=None)
    timestamp: int = Field(default_factory=get_timestamp)

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, value: Any) -> int:
        """Validate and convert the timestamp field to EpochTimestamp."""
        if isinstance(value, int):
            return value
        if isinstance(value, EpochTimestamp):
            return int(value)
        raise TypeError("timestamp must be an int or EpochTimestamp")

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: EpochTimestamp) -> int:
        """Serialize the timestamp field to an integer."""
        return int(value)

    @computed_field
    def checksum(self) -> str:
        """Compute a checksum for the WALRecord."""
        record_json: str = self.model_dump_json(exclude={"checksum"}, exclude_none=True)
        return compute_checksum(record_json)

    def __str__(self) -> str:
        """String representation of the WALRecord."""
        output: str = f"WALRecord(txid={self.txid}, op={self.op}"
        if self.data is not None:
            output += f", data={self.data}"
        output += f", timestamp={int(self.timestamp)})"
        return output

    def __repr__(self) -> str:
        """Official string representation of the WALRecord."""
        return self.__str__()
