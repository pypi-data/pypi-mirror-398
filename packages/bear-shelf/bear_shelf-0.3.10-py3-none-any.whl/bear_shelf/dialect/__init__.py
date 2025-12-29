"""Bear Shelf Dialect.

This module provides a SQLAlchemy dialect for interacting with Bear Shelf,
a lightweight document storage system. The dialect allows SQLAlchemy to
communicate with Bear Shelf databases using standard SQL queries.
"""

from .bear_dialect import BearShelfDialect

__all__ = ["BearShelfDialect"]
