from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from logging import Logger
    from pathlib import Path


FORMAT = "[%(filename)s::%(funcName)s(%(lineno)s)] %(message)s"
DATEFMT = "%I:%M:%S.%f"


class DummyLogger:
    def __getattr__(self, name: str) -> Any:
        def no_op(*args: Any, **kwargs: Any) -> None: ...

        return no_op


class LoggerManager:
    def __init__(
        self,
        level: int | str | None = None,
        *,
        console: bool = False,
        file: bool = False,
        path: str | Path | None = None,
        size: int | None = None,
        backup_count: int = 3,
    ) -> None:
        from logging import DEBUG, getLevelNamesMapping

        self.path: str | Path | None = path
        self.level: int = getLevelNamesMapping().get(level, DEBUG) if isinstance(level, str) else level or DEBUG
        self.console_enabled: bool = console
        self.file_enabled: bool = file
        self.size: int = size if size is not None else 5 * (1024 * 1024)
        self.backup_count: int = backup_count
        self._loggers: dict[str, Logger] = {}

    def configured_logger(self, name: str) -> Logger:
        if not (self.console_enabled and (self.file_enabled and self.path)):
            return cast("Logger", DummyLogger())

        from logging import Formatter, getLogger

        logger: Logger = getLogger(name)
        logger.setLevel(self.level)

        if self.console_enabled:
            from rich.console import Console
            from rich.logging import RichHandler

            fmt = Formatter(FORMAT, datefmt=DATEFMT)
            console = Console()
            console_handler: RichHandler = RichHandler(
                console=console,
                rich_tracebacks=True,
                tracebacks_show_locals=True,
                enable_link_path=False,
                show_path=False,
            )
            console_handler.setLevel(self.level)
            console_handler.setFormatter(fmt)
            logger.addHandler(console_handler)

        if self.file_enabled and self.path:
            from logging.handlers import RotatingFileHandler

            fmt = Formatter(FORMAT, datefmt=DATEFMT)
            file_handler = RotatingFileHandler(
                filename=self.path,
                maxBytes=self.size,
                backupCount=self.backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(self.level)
            file_handler.setFormatter(fmt)
            logger.addHandler(file_handler)
        return logger

    def get_logger(self, name: str) -> Logger:
        if name not in self._loggers:
            self._loggers[name] = self.configured_logger(name)
        return self._loggers[name]


def logging_enabled() -> bool:
    from os import getenv

    return getenv("BEAR_SHELF_DEBUG", "false").lower() in {"1", "true", "yes", "on"}


def get_logger(
    name: str,
    level: int | str | None = None,
    *,
    console: bool = False,
    file: bool = False,
    path: str | Path | None = None,
    size: int | None = None,
    backup_count: int = 3,
) -> Logger:
    if logging_enabled():
        return LoggerManager(
            level=level,
            console=console,
            file=file,
            path=path,
            size=size,
            backup_count=backup_count,
        ).get_logger(name)

    return cast("Logger", DummyLogger())


# ruff: noqa: PLC0415
