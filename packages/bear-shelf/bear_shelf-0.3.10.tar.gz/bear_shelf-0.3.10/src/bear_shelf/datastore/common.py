"""Common types and utilities for the datastore."""

from enum import StrEnum


class FKAction(StrEnum):
    """Foreign key referential actions for DELETE operations.

    Defines behavior when a parent record is deleted:
    - SET_NULL: Set child FK to NULL (requires nullable column)
    - CASCADE: Delete child records recursively
    - RESTRICT: Prevent delete if children exist (default SQL behavior)
    - NO_ACTION: Allow delete without checking (creates orphans)
    """

    SET_NULL = "SET NULL"
    CASCADE = "CASCADE"
    RESTRICT = "RESTRICT"
    NO_ACTION = "NO ACTION"


__all__ = ["FKAction"]
