"""A set of SQL compilers for the Bear Shelf dialect."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy
from sqlalchemy.sql.compiler import DDLCompiler

if TYPE_CHECKING:
    from bear_shelf.config import APP_CONFIG
else:
    APP_CONFIG = lazy("bear_shelf.config", "APP_CONFIG")


class BearDDLCompiler(DDLCompiler):
    """DDL compiler for Bear Shelf dialect."""

    def visit_create_table(self, create: Any, **_) -> str:
        """Handle CREATE TABLE DDL - emit sentinel comment."""
        return f"{APP_CONFIG.info.ddl_comment_prefix} create {create.element.name} */"

    def visit_drop_table(self, drop: Any, **_) -> str:
        """Handle DROP TABLE DDL - emit sentinel comment."""
        return f"{APP_CONFIG.info.ddl_comment_prefix} drop {drop.element.name} */"
