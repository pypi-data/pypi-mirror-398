"""Middleware implementation for Write-Ahead Logging (WAL) operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bear_shelf.datastore.middleware import Middleware

from .helper import WALHelper

if TYPE_CHECKING:
    from pathlib import Path

    from bear_shelf.datastore.storage._common import Storage

    from .config import WALConfig


class WALMiddleware(WALHelper, Middleware):
    """A middleware wrapper around :class:`WALHelper`.

    This class lets the WAL helper participate in the middleware chain so it can
    be configured via BearDB's ``storage`` argument just like any other
    middleware. All helper behaviors (logging insert/update/delete batches,
    recovery, checkpointing, etc.) are preserved while also exposing the
    underlying storage object through :class:`Middleware`.
    """

    def __init__(
        self,
        storage_cls: type[Storage],
        file: str | Path,
        table_name: str,
        *,
        config: WALConfig | None = None,
        auto_start: bool = True,
    ) -> None:
        """Initialize the WAL middleware."""
        Middleware.__init__(self, storage_cls)
        WALHelper.__init__(self, file=file, table_name=table_name, config=config, auto_start=auto_start)

    def close(self, clear: bool = True, delete: bool = True) -> None:
        """Stop WAL threads and close the underlying storage."""
        WALHelper.close(self, clear=clear, delete=delete)
        if self.storage is not None and not self.storage.closed:
            self.storage.close()


__all__ = ["WALMiddleware"]
