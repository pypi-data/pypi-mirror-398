"""A deserializer to convert XML data to UnifiedDataFormat."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from lazy_bear import lazy

from bear_shelf.config import CUSTOM_TYPE_MAP
from bear_shelf.datastore.columns import Columns
from bear_shelf.datastore.header_data import HeaderData
from bear_shelf.datastore.record import Record
from bear_shelf.datastore.tables.data import TableData
from bear_shelf.datastore.unified_data import UnifiedDataFormat

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

    from codec_cub.xmls.helpers import find_value, get_value
    from funcy_bear.type_stuffs.conversions import coerce_to_type, parse_bool, str_to_type
else:
    coerce_to_type, parse_bool, str_to_type = lazy(
        "funcy_bear.type_stuffs.conversions", "coerce_to_type", "parse_bool", "str_to_type"
    )
    find_value, get_value = lazy("codec_cub.xmls.helpers", "find_value", "get_value")


class XMLDeserializer:
    """Class to handle deserialization of XML data to UnifiedDataFormat."""

    def __init__(self, data: Element) -> None:
        """Initialize the XML deserializer."""
        self.data: Element = data

    def get_root(self, root: Element) -> UnifiedDataFormat:
        """Deserialize root database element to UnifiedDataFormat using schema elements."""
        self.output = UnifiedDataFormat()
        header_elem: Element = find_value(root, "header")
        self.output.header = self.get_header(header_elem)
        tables_elem: Element = find_value(root, "tables")
        self.add_to_tables(tables_elem)
        return self.output

    def get_header(self, header_elem: Element) -> HeaderData:
        """Deserialize header element to HeaderData using schema elements."""
        header = HeaderData()
        header.version = get_value(find_value(header_elem, "version"), "version")
        tables_elem: Element = find_value(header_elem, "tables")
        header.tables = [get_value(t, "name") for t in tables_elem.findall("table")]
        return header

    def add_to_tables(self, tables_elem: Element) -> None:
        """Deserialize tables element to tables dict."""
        for table_elem in tables_elem.findall("table"):
            table_name: str = get_value(table_elem, "name")
            self.output.tables[table_name] = self.get_table_data(table_name, table_elem)

    def get_table_data(self, table_name: str, table_elem: Element) -> TableData:
        """Deserialize table element to TableData using schema elements."""

        def add_to_columns(columns_elem: Element) -> list[Columns]:
            cols: list[Columns] = []
            for col_elem in columns_elem.findall("column"):
                attrs: dict[str, Any] = dict(col_elem.attrib)
                cols.append(Columns.model_validate(attrs))
            return cols

        def add_to_records(records_elem: Element, columns: list[Columns]) -> list[Record]:
            records = []
            col_types: dict[str, str] = {col.name: col.type for col in columns}
            for record_elem in records_elem.findall("record"):
                attrs: dict[str, Any] = dict(record_elem.attrib)
                for field, value in attrs.items():
                    to_type: type = str_to_type(col_types.get(field, "str"), custom_map=CUSTOM_TYPE_MAP)
                    if to_type is bool:
                        attrs[field] = parse_bool(value)
                    else:
                        attrs[field] = coerce_to_type(value, to_type)
                records.append(Record.model_validate(attrs))
            return records

        cols: list[Columns] = add_to_columns(find_value(table_elem, "columns"))
        records: list[Record] = add_to_records(find_value(table_elem, "records"), cols)
        return TableData(name=table_name, columns=cols, records=records)

    def to_data(self) -> UnifiedDataFormat:
        """Deserialize the entire XML Element to a UnifiedDataFormat."""
        return self.get_root(self.data)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        pass
