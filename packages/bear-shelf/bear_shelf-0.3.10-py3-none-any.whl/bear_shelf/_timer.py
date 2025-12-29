"""Timing utilities for profiling Bear Shelf database operations."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Generator
    from logging import Logger

    from bear_epoch_time import TimerData


class TimerManager:
    """Manages timing for database operations with hierarchical tracking."""

    def __init__(self, name: str, logger: Logger | None = None) -> None:
        """Initialize timer manager.

        Args:
            name: Name for this timer
            logger: Optional logger for output (uses logger.debug)
        """
        self.name: str = name
        self.logger: Logger | None = logger
        self._nested_timers: dict[str, TimerData] = {}
        self._timer: TimerData = self._create_timer(name, logger=logger)

    def _create_timer(self, label: str, logger: Logger | None = None, nested: bool = False) -> TimerData:
        """Create a nested timer with the given label.

        Args:
            label: Label for the nested timer
            logger: Optional logger for output
            nested: Whether this timer is nested (default: False)

        Returns:
            TimerData instance for the nested timer
        """
        from bear_epoch_time import TimerData

        timer: TimerData = TimerData(
            name=f"{self.name}.{label}",
            console=logger.debug if logger else None,
            time_type="ms",
        )
        if nested:
            self._nested_timers[label] = timer
        return timer

    def start(self, label: str | None = None) -> None:
        """Start timing an operation.

        Args:
            label: Optional label for nested timing
        """
        if label:
            if label not in self._nested_timers:
                self._create_timer(label, logger=self.logger, nested=True)
            self._nested_timers[label].start()
        else:
            self._timer.start()

    def stop(self, label: str | None = None) -> float:
        """Stop timing and return elapsed time in milliseconds.

        Args:
            label: Optional label for nested timing

        Returns:
            Elapsed time in milliseconds
        """
        if label and label in self._nested_timers:
            self._nested_timers[label].stop()
            return self._nested_timers[label].value
        self._timer.stop()
        return self._timer.value

    @contextmanager
    def measure(self, operation: str) -> Generator[None]:
        """Context manager for timing an operation.

        Usage:
            with timer.measure("query_execution"):
                # ... do work ...

        Args:
            operation: Name of the operation being timed
        """
        self.start(operation)
        try:
            yield
        finally:
            elapsed: float = self.stop(operation)
            if self.logger:
                self.logger.debug(f"{operation}: {elapsed:.2f}ms")

    def get_stats(self) -> dict[str, float]:
        """Get timing statistics for all operations.

        Returns:
            Dictionary mapping operation names to elapsed times in ms
        """
        stats: dict[str, float] = {self.name: self._timer.value}
        for label, timer in self._nested_timers.items():
            stats[f"{self.name}.{label}"] = timer.value
        return stats

    def reset(self) -> None:
        """Reset all timers."""
        self._timer.reset()
        for timer in self._nested_timers.values():
            timer.reset()


class DummyTimer:
    """No-op timer for when debug mode is disabled."""

    def __getattr__(self, name: str) -> Any:
        """Return a no-op function or context manager for any attribute."""
        return self._no_op

    def _no_op(self, *args: Any, **kwargs: Any) -> Any:
        """No-op function that accepts any arguments."""
        return 0.0

    @contextmanager
    def measure(self, *args: Any, **kwargs: Any) -> Generator[None]:
        """No-op context manager."""
        yield


def timing_enabled() -> bool:
    """Check if timing is enabled via debug mode."""
    from os import getenv

    return getenv("BEAR_SHELF_DEBUG", "false").lower() in {"1", "true", "yes", "on"}


def get_timer(name: str, logger: Logger | None = None) -> TimerManager:
    """Get a timer instance (real or dummy based on debug mode).

    Args:
        name: Name for the timer
        logger: Optional logger for output

    Returns:
        TimerManager if debug enabled, DummyTimer otherwise
    """
    if timing_enabled():
        return TimerManager(name, logger=logger)
    return cast("TimerManager", DummyTimer())


# ruff: noqa: PLC0415 ARG002
