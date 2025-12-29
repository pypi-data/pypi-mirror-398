"""A module defining the HeaderData model for database header metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy
from pydantic import Field

from bear_shelf.config import APP_CONFIG
from bear_shelf.models import ExtraIgnoreModel

if TYPE_CHECKING:
    from frozen_cub.frozen import FrozenDict, freeze
else:
    FrozenDict, freeze = lazy("frozen_cub.frozen", "FrozenDict", "freeze")


class HeaderData(ExtraIgnoreModel):
    """Database header metadata."""

    version: str = APP_CONFIG.info.unified_data_version
    schema_version: str = "0.0.1"  # Placeholder for future schema versioning
    tables: list[str] = Field(default_factory=list)

    def items(self) -> list[tuple[str, Any]]:
        """Return items for the header."""
        return list(self.model_dump(exclude_none=True).items())

    def add(self, table_name: str) -> None:
        """Add a table name to the header if not already present.

        Args:
            table_name: Name of the table to add.
        """
        if table_name not in self.tables:
            self.tables.append(table_name)

    def remove(self, table_name: str) -> None:
        """Remove a table name from the header if it exists.

        Args:
            table_name: Name of the table to remove.
        """
        if table_name in self.tables:
            self.tables.remove(table_name)

    def frozen_dump(self) -> FrozenDict:
        """Return a frozen representation of the header."""
        return freeze(self.model_dump(exclude_none=True))

    def __hash__(self) -> int:
        """Get the hash of the header based on its version and tables."""
        return hash(f"HeaderData-{self.version}-{self.schema_version}-{hash(tuple(sorted(self.tables)))}")

    def __repr__(self) -> str:
        return f"HeaderData(version={self.version}, schema_version={self.schema_version}, tables={self.tables})"
