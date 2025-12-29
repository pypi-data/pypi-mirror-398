"""Bear's datastore - A clean, simple, and powerful document storage system.

This module provides a lightweight alternative to traditional databases.
Supports multiple storage backends (JSON, JSONL, TOML, in-memory) and advanced querying.
"""

from typing import TYPE_CHECKING

from lazy_bear import lazy

if TYPE_CHECKING:
    from bear_shelf.datastore.columns import Columns
    from bear_shelf.datastore.database import BearBase
    from bear_shelf.datastore.header_data import HeaderData
    from bear_shelf.datastore.record import Record
    from bear_shelf.datastore.tables.data import TableData
    from bear_shelf.datastore.tables.handler import TableHandler
    from bear_shelf.datastore.tables.table import Table
    from bear_shelf.datastore.unified_data import UnifiedDataFormat
else:
    BearBase = lazy("bear_shelf.datastore.database", "BearBase")
    Columns = lazy("bear_shelf.datastore.columns", "Columns")
    HeaderData = lazy("bear_shelf.datastore.header_data", "HeaderData")
    Record = lazy("bear_shelf.datastore.record", "Record")
    TableData = lazy("bear_shelf.datastore.tables.data", "TableData")
    TableHandler = lazy("bear_shelf.datastore.tables.handler", "TableHandler")
    Table = lazy("bear_shelf.datastore.tables.table", "Table")
    UnifiedDataFormat = lazy("bear_shelf.datastore.unified_data", "UnifiedDataFormat")


__all__ = [
    "BearBase",
    "Columns",
    "HeaderData",
    "Record",
    "Table",
    "TableData",
    "TableHandler",
    "UnifiedDataFormat",
]
