"""Configuration model for Write-Ahead Logging (WAL) behavior."""

from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

MEGABYTES = 1024 * 1024


class WALFlushMode(StrEnum):
    """WAL flush strategies."""

    IMMEDIATE = "immediate"
    BUFFERED = "buffered"


class WALConfig(BaseModel):
    """Configuration for Write-Ahead Logging behavior.

    This controls the trade-off between safety and performance:
    - IMMEDIATE mode: Maximum safety, slower (good for low volume)
    - BUFFERED mode: Better performance, small crash window (good for high volume)
    """

    flush_mode: WALFlushMode = Field(default=WALFlushMode.BUFFERED, description="When to flush WAL writes to disk")
    auto_checkpoint: bool = Field(default=True, description="Automatically checkpoint when WAL reaches threshold")
    checkpoint_threshold: int = Field(default=1000, ge=1, description="Number of WAL operations before auto-checkpoint")
    flush_interval: float = Field(
        default=5,
        ge=0.05,
        le=60.0,
        description="Seconds between automatic flushes in BUFFERED mode",
    )
    flush_batch_size: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Number of operations before forcing flush in BUFFERED mode",
    )
    on_flush_error: Callable[[Exception], None] | None = Field(
        default=None,
        description="Optional callback for flush errors in background thread",
    )
    max_buffer_bytes: int = Field(
        default=MEGABYTES * 5,
        ge=MEGABYTES * 1,
        le=MEGABYTES * 100,
        description="Maximum memory buffer size for WAL in BUFFERED mode",
    )
    get_timeout: float = Field(default=0.05, ge=0.01, description="Timeout in seconds for read operations from WAL")
    timeout: float = Field(default=5.0, ge=0.1, description="Timeout in seconds for WAL operations")

    @field_validator("flush_mode", mode="before")
    @classmethod
    def validate_flush_mode(cls, v: str | WALFlushMode) -> WALFlushMode:
        """Validate and convert flush mode."""
        if isinstance(v, str):
            return WALFlushMode(v.lower())
        return v

    @field_validator("flush_interval", mode="before")
    @classmethod
    def validate_flush_interval(cls, v: float) -> float:
        """Validate flush interval."""
        min_interval: float = 0.05
        max_interval: float = 60.0
        if not (min_interval <= v <= max_interval):
            raise ValueError("flush_interval must be between 0.05 and 60.0 seconds")
        return v

    @field_validator("checkpoint_threshold", mode="before")
    @classmethod
    def validate_checkpoint_threshold(cls, v: int) -> int:
        """Validate checkpoint threshold."""
        min_threshold: int = 1
        max_threshold: int = 1000000
        if not (min_threshold <= v <= max_threshold):
            raise ValueError("checkpoint_threshold must be between 1 and 1000000")
        return v

    @field_validator("flush_batch_size", mode="before")
    @classmethod
    def validate_flush_batch_size(cls, v: int) -> int:
        """Validate flush batch size."""
        min_size: int = 1
        max_size: int = 10000
        if not (min_size <= v <= max_size):
            raise ValueError("flush_batch_size must be between 1 and 10000")
        return v

    @classmethod
    def immediate(cls) -> WALConfig:
        """Preset for maximum safety (low volume workloads).

        Every write is immediately flushed to disk with fsync.
        Best for: Critical data, low volume, need maximum crash protection.
        """
        return cls(flush_mode=WALFlushMode.IMMEDIATE)

    @classmethod
    def buffered(
        cls,
        flush_interval: float = 0.1,
        flush_batch_size: int = 100,
    ) -> WALConfig:
        """Preset for balanced performance (high volume workloads).

        Batches writes in memory and flushes periodically.
        Best for: Bulk inserts, high volume, acceptable small crash window.

        Args:
            flush_interval: Seconds between flushes (default: 0.1 = 100ms)
            flush_batch_size: Operations before flush (default: 100)
        """
        return cls(
            flush_mode=WALFlushMode.BUFFERED,
            flush_interval=flush_interval,
            flush_batch_size=flush_batch_size,
        )

    @classmethod
    def high_throughput(cls) -> WALConfig:
        """Preset for maximum throughput (bulk operations).

        Aggressive batching for fastest writes.
        Best for: Data imports, batch processing, can tolerate crash window.
        """
        return cls(
            flush_mode=WALFlushMode.BUFFERED,
            flush_interval=1.0,  # Flush every second
            flush_batch_size=1000,  # Or every 1000 ops
        )

    def on_error(self, e: Exception) -> None:
        """Invoke the error callback if set.

        Args:
            e: The exception that occurred
        """
        if self.on_flush_error and callable(self.on_flush_error) and isinstance(e, Exception):
            self.on_flush_error(e)

    model_config = ConfigDict(frozen=True)
