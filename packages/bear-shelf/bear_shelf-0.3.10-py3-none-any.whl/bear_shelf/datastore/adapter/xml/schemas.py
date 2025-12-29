"""Module defining XML schema elements for the database."""

from typing import TYPE_CHECKING, Any, ClassVar, Literal, Self, overload

from pydantic import BaseModel, ConfigDict, Field, SerializerFunctionWrapHandler, computed_field, model_serializer

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

XmlTypes = Literal[
    "str",
    "int",
    "float",
    "bool",
    "list",
    "dict",
    "None",
    "Columns",
    "TableData",
    "HeaderData",
    "UnifiedDataFormat",
]


class AbstractElement:
    """Abstract base class for XML elements with a tag attribute."""

    tag: ClassVar[str]

    def to_xml(self) -> Element:
        """Convert the model attributes to an XML element.

        Returns:
            An XML Element representing the model.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class BaseElement[T: AbstractElement](BaseModel, AbstractElement):
    """Base model for XML elements with a tag attribute."""

    model_config = {"arbitrary_types_allowed": True}

    tag: ClassVar[str] = ""
    sub_elements: list[T] = Field(default_factory=list, description="Sub-elements of other XML elements.")

    @model_serializer(mode="wrap")
    def convert_to_strings(self, nxt: SerializerFunctionWrapHandler) -> dict[Any, Any]:
        """Convert common types to strings for XML serialization."""
        data: dict[Any, Any] = nxt(self)

        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, (int | float | bool)):
                data[key] = str(value).lower()
        return data

    def add(self, element: T) -> Self:
        """Add a sub-element to the list of sub-elements."""
        if not isinstance(element, BaseElement):
            raise TypeError(f"Expected an instance of BaseElement, got {type(element)}")
        self.sub_elements.append(element)
        return self

    def has_element(self, element: type[T] | str) -> bool:
        """Check if the element is present in the sub-elements."""
        if isinstance(element, str):
            return any(sub.tag == element for sub in self.sub_elements)
        if isinstance(element, type) and issubclass(element, BaseElement):
            return any(isinstance(sub, element) for sub in self.sub_elements)
        return element in self.sub_elements

    def has_field(self, attr: type | str) -> bool:
        """Check if the class has a specific field or attribute."""
        if isinstance(attr, str):
            return hasattr(self, attr)
        return hasattr(self, attr.__name__)

    @overload
    def get(self, element: str, strict: Literal[True]) -> T: ...

    @overload
    def get(self, element: type[T], strict: Literal[True]) -> T: ...

    @overload
    def get(self, element: type[T], strict: Literal[False] = False) -> T | None: ...

    @overload
    def get(self, element: str, strict: Literal[False] = False) -> T | None: ...

    def get(self, element: type[T] | str, strict: bool = False) -> T | None:
        """Get the sub-element by element type or tag name.

        Args:
            element: The type or tag name of the sub-element to retrieve.
            strict: If True, raise an error if the element is not found. Defaults to False

        Returns:
            The sub-element if found, otherwise None or raises an error if strict is True.
        """
        if isinstance(element, type):
            for sub in self.sub_elements:
                if isinstance(sub, element):
                    return sub
        elif isinstance(element, str):
            for sub in self.sub_elements:
                if sub.tag == element:
                    return sub
        if strict:
            raise ValueError(f"Element '{element}' not found in sub_elements")
        return None

    def get_req(self, element: T | str) -> T:
        """Get the sub-element by element type or tag name, raising an error if not found."""
        return self.get(element, strict=True)

    def to_xml(self, exclude_none: bool = True, exclude: set | None = None, **kwargs) -> Element:
        """Convert the model attributes to an XML element.

        Returns:
            An XML Element representing the model.
        """
        from codec_cub.xmls.helpers import to_elem  # noqa: PLC0415

        if exclude is None:
            exclude_me: set[str] = {"sub_elements"}
        else:
            exclude_me: set[str] = exclude.union({"sub_elements"})
        element: Element = to_elem(
            tag=self.tag,
            **self.model_dump(
                exclude_none=exclude_none,
                exclude=exclude_me,
                **kwargs,
            ),
        )
        if self.sub_elements:
            for sub_element in self.sub_elements:
                sub_element_element: Element = sub_element.to_xml()
                element.append(sub_element_element)
        return element

    def to_string(self) -> str:
        """Convert the model to a string representation."""
        from xml.etree.ElementTree import tostring  # noqa: PLC0415

        return tostring(self.to_xml(), encoding="unicode")


class HelperModel[T: AbstractElement](BaseElement[T]):
    """XML element representing a conversion model."""

    type: XmlTypes = "str"


class VersionElement(HelperModel):
    """XML element representing the version of the database."""

    tag = "version"
    type: XmlTypes = "str"

    version: str


class SimpleTableElement(HelperModel):
    """XML element representing a simple table entry in the header."""

    tag = "table"
    type: XmlTypes = "str"

    name: str


class HeaderTablesElement(HelperModel[SimpleTableElement]):
    """XML element representing the tables list in the header."""

    tag = "tables"
    type: XmlTypes = "list"
    sub_elements: list[SimpleTableElement] = Field(default_factory=list)

    @computed_field
    def count(self) -> int:
        """Get the count of tables in the header."""
        return len(self.sub_elements)


class HeaderElement(HelperModel[VersionElement | HeaderTablesElement]):
    """XML element representing the header section of the database."""

    tag = "header"
    type: XmlTypes = "HeaderData"
    sub_elements: list[VersionElement | HeaderTablesElement] = Field(default_factory=list)


class ColumnElement(BaseElement):
    """XML element representing a single column in a table."""

    tag = "column"
    name: str
    type: str
    nullable: bool = False
    primary_key: bool | None = None


class RecordElement(BaseElement):
    """XML element representing a single record/row in a table.

    Records do not use HelperModel because they contain dynamic fields
    based on the table schema, not a static type annotation.
    """

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    tag: ClassVar[str] = "record"


class ColumnsElement(HelperModel[ColumnElement]):
    """XML element representing the columns section of a table."""

    tag = "columns"
    type: XmlTypes = "list"
    sub_elements: list[ColumnElement] = Field(default_factory=list)
    meta: str = "Columns"

    @computed_field
    def count(self) -> int:
        """Get the count of columns in the table."""
        return len(self.sub_elements)


class RecordsElement(HelperModel[RecordElement]):
    """XML element representing the records section of a table."""

    tag = "records"
    type: XmlTypes = "list"
    sub_elements: list[RecordElement] = Field(default_factory=list)
    meta: str = "Record"

    @computed_field
    def count(self) -> int:
        """Get the count of records in the table."""
        return len(self.sub_elements)


class TableElement(HelperModel[ColumnsElement | RecordsElement]):
    """XML element representing a single table in the database."""

    tag = "table"
    type: XmlTypes = "TableData"
    sub_elements: list[ColumnsElement | RecordsElement] = Field(default_factory=list)

    name: str
    count: int = 2  # Always 2: one for columns, one for records


class TablesElement(HelperModel[TableElement]):
    """XML element representing the tables section of the database."""

    tag = "tables"
    type: XmlTypes = "dict"
    sub_elements: list[TableElement] = Field(default_factory=list)
    meta: str = "TableData"

    @computed_field
    def count(self) -> int:
        """Get the count of tables in the database."""
        return len(self.sub_elements)


class DatabaseElement(BaseElement[HeaderElement | TablesElement]):
    """XML element representing the root database."""

    tag = "database"
    type: XmlTypes = "UnifiedDataFormat"
    sub_elements: list[HeaderElement | TablesElement] = Field(default_factory=list)
