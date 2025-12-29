"""Bear-Shelf: A lightweight document storage system with SQLAlchemy dialect support.

The shelf that replaces shelve - where your data hibernates.
"""

from bear_shelf._internal._info import METADATA
from bear_shelf._internal.cli import main

__version__: str = METADATA.version

__all__: list[str] = ["METADATA", "__version__", "main"]
