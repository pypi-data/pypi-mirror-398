"""XML storage backend for the datastore.

Provides self-describing XML file storage with type annotations and validation metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from lazy_bear import lazy
from pydantic import ValidationError

from ._common import Storage

if TYPE_CHECKING:
    from logging import Logger
    from pathlib import Path

    from bear_shelf._logger import get_logger
    from bear_shelf.datastore.adapter.xml import XMLDeserializer, XMLSerializer
    from bear_shelf.datastore.unified_data import UnifiedDataFormat
    from codec_cub.general.helpers import touch
    from codec_cub.xmls import Tree, XMLFileHandler
else:
    Tree, XMLFileHandler = lazy("codec_cub.xmls", "Tree", "XMLFileHandler")
    XMLDeserializer, XMLSerializer = lazy("bear_shelf.datastore.adapter.xml", "XMLDeserializer", "XMLSerializer")
    touch = lazy("codec_cub.general.helpers", "touch")
    get_logger = lazy("bear_shelf._logger", "get_logger")
    UnifiedDataFormat = lazy("bear_shelf.datastore.unified_data", "UnifiedDataFormat")


class XMLStorage(Storage):
    """An XML file storage backend using self-describing XML format.

    This implementation produces highly self-documenting XML with explicit type
    annotations, counts for validation, and metadata attributes referencing the
    Pydantic models. This enables robust parsing and validation without external
    schema knowledge.
    """

    def __init__(self, file: str | Path, file_mode: str = "r+", encoding: str = "utf-8") -> None:
        """Initialize XML storage.

        Args:
            file: Path to the XML file
            file_mode: File mode for opening (default: "r+" for read/write)
            encoding: Text encoding to use (default: "utf-8")
        """
        self.logger: Logger = get_logger("XMLStorage")
        super().__init__()
        self.file: Path = touch(path=file, mkdir=True, create_file=True)
        self.handler: XMLFileHandler = XMLFileHandler(self.file, mode=file_mode, encoding=encoding)
        self.logger.debug(f"XMLStorage initialized with file: {self.file}")

    def read(self) -> UnifiedDataFormat | None:
        """Read data from XML file.

        Returns:
            UnifiedDataFormat instance populated from the XML file.
        """
        try:
            xml_data: Tree | None = self.handler.read()
            if xml_data is None:
                return UnifiedDataFormat()
            with XMLDeserializer(xml_data.getroot()) as deserializer:
                data: UnifiedDataFormat = deserializer.to_data()
                self.logger.debug(f"Read data from XML storage at {self.file}: {data}")
                return data
        except (ValueError, OSError, ValidationError) as e:
            self.logger.error(f"Error reading XML storage from {self.file}: {e}")
            return None

    def write(self, data: UnifiedDataFormat, pretty: bool = True) -> None:
        """Write data to XML file in idiomatic XML format.

        Args:
            data: UnifiedDataFormat instance to write.
            pretty: Whether to pretty-print the XML (default: True)
        """
        with XMLSerializer(data) as serializer:
            output = serializer.to_tree()
            self.logger.debug(f"Writing data to XML storage at {self.file}: {data}")
            self.handler.write(output, pretty=pretty)

    def close(self) -> None:
        """Close the file handle."""
        self.logger.debug(f"Closing XMLStorage for file: {self.file} {self.closed=}")
        if self.closed:
            return
        self.handler.close()

    @property
    def closed(self) -> bool:
        """Check if the storage is closed."""
        return self.handler.closed
