"""Module defining the TableData class for managing table data in a datastore."""

# region: Imports

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, Self

from lazy_bear import lazy
from pydantic import Field, PrivateAttr

from bear_shelf.datastore.columns import Columns, NullColumn
from bear_shelf.datastore.record import Record  # noqa: TC001
from bear_shelf.models import ExtraIgnoreModel

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from inspect import Parameter

    from frozen_cub.frozen import freeze

    from funcy_bear.tools.counter_class import Counter
    from funcy_bear.type_stuffs.introspection import ParamWrapper
else:
    freeze = lazy("frozen_cub.frozen", "freeze")
    Counter = lazy("funcy_bear.tools.counter_class", "Counter")
    ParamWrapper = lazy("funcy_bear.type_stuffs.introspection", "ParamWrapper")
    Parameter = lazy("inspect", "Parameter")

type CacheLookup = dict[str, set[Any]]

# endregion: Imports


class TableData(ExtraIgnoreModel):
    """Complete data for a single table."""

    # region: Private Attributes
    _column_names: set[str] = PrivateAttr(default_factory=set)
    _required_cols: set[str] = PrivateAttr(default_factory=set)
    _unique_cols: set[Columns] = PrivateAttr(default_factory=set)
    _primary_col: Columns = PrivateAttr(default=NullColumn)
    _highest_int_pk: int = PrivateAttr(default=-1)
    _counter: Counter | None = PrivateAttr(default=None)

    # endregion: Private Attributes
    # region: Fields

    name: str = Field(default=..., exclude=True)
    columns: list[Columns] = Field(default_factory=list)
    records: list[Record] = Field(default_factory=list)

    @property
    def count(self) -> int:
        """Get the count of records in the table."""
        return len(self.records)

    @property
    def primary_key(self) -> str:
        """Get the name of the primary key column."""
        return self._primary_col.name

    @property
    def is_auto(self) -> bool:
        """Check if the primary key is auto-incrementing."""
        return self._primary_col.autoincrement is True

    @property
    def is_primary_int(self) -> bool:
        """Check if the primary key column is of type int."""
        return self._primary_col.type_obj is int

    @property
    def is_primary_str(self) -> bool:
        """Check if the primary key column is of type str."""
        return self._primary_col.type_obj is str

    @property
    def prime_default(self) -> Any:
        """Get the default value for the primary key column."""
        return self._primary_col.default

    @prime_default.setter
    def prime_default(self, value: Any) -> None:
        """Set the default value for the primary key column."""
        self._primary_col.default = value

    @property
    def maximum_primary(self) -> int:
        """Get the highest integer primary key value out of all of the records or -1 if none exist."""
        return max(
            (record.get(self.primary_key) for record in self.records if isinstance(record.get(self.primary_key), int)),
            default=-1,
        )

    @property
    def counter(self) -> Counter:
        """Get or create the counter for auto-incrementing primary keys."""
        if self._counter is None:
            start_value: int = self.maximum_primary + 1 if self.records else (self.prime_default or 0)
            self._counter = Counter(start=start_value)
        return self._counter

    # endregion: Fields
    # region: Initialization

    def model_post_init(self, context: Any) -> None:
        """Post-initialization to set up primary column and counter."""
        self.validate_columns()
        if self.columns and self._primary_col == NullColumn:
            self.parse_primary(self.columns)
        if self._counter is None and self.is_auto:
            start_value: int = self.maximum_primary + 1 if self.records else (self.prime_default or 0)
            self._counter = Counter(start=start_value)
        for record in self.records:
            self._ensure_primary_key_first(record)
        return super().model_post_init(context)

    def parse_primary(self, columns: list[Columns]) -> list[Columns]:
        """Parse and set the primary column for the table."""
        primary_key: Columns | None = next((col for col in columns if col.primary_key), None)
        if primary_key is None:
            raise ValueError("At least one column must be designated as primary_key=True.")
        self.set_primary(primary_key)
        if self.is_primary_int and self.prime_default is not None:
            try:
                self.prime_default = int(self.prime_default)
            except Exception:
                self.prime_default = 0
        elif self.is_primary_int and self.prime_default is None:
            self.prime_default = 0
        return columns

    def set_primary(self, column: Columns) -> None:
        """Set the primary column for the table."""
        self._primary_col = column

    # endregion: Initialization
    # region: Table Validation

    def _has_one_column(self) -> None:
        """Check if the table has at least one column."""
        if not self.columns:
            raise ValueError(f"Table '{self.name}' must have at least one column.")

    def _validate_table_name(self) -> None:
        """Validate table name format.

        Raises:
            ValueError: If table name is invalid.
        """
        if not self.name or not self.name.strip():
            raise ValueError("Table name cannot be empty or whitespace.")
        if not self.name[0].isalpha() and self.name[0] != "_":
            raise ValueError(f"Table name must start with a letter or underscore, not '{self.name[0]}'.")
        if " " in self.name:
            raise ValueError("Table name cannot contain spaces. Use underscores instead.")

    def _validate_unique_column_names(self) -> None:
        """Validate that all column names are unique.

        Raises:
            ValueError: If duplicate column names are found.
        """
        column_names: list[str] = [col.name for col in self.columns]
        seen: set[str] = set()
        duplicates: set[str] = set()
        for name in column_names:
            if name in seen:
                duplicates.add(name)
            seen.add(name)
        if duplicates:
            raise ValueError(f"Duplicate column names found in table '{self.name}': {sorted(duplicates)}")
        self._column_names = set(column_names)

    def _validate_exactly_one_primary_key(self) -> None:
        """Validate that exactly one column is designated as primary key.

        Raises:
            ValueError: If zero or multiple primary keys are found.
        """
        primary_keys: list[Columns] = [col for col in self.columns if col.primary_key is True]
        if len(primary_keys) == 0:
            raise ValueError("At least one column must be designated as primary_key=True.")
        if len(primary_keys) > 1:
            pk_names: list[str] = [col.name for col in primary_keys]
            raise ValueError(
                f"Exactly one column must be designated as primary key, found {len(primary_keys)}: {pk_names}"
            )

    def validate_columns(self) -> None:
        """Validate table and column naming and constraints.

        Column/Table Naming Rules:
        - Must start with letter or underscore
        - No spaces (use underscores)
        - Cannot start with 'xml' (case insensitive)
        - Cannot be empty or whitespace-only

        Constraint Rules:
        - Exactly one primary key per table
        - Primary keys cannot be nullable
        - Autoincrement only on integer primary keys

        General:
        - At least one column must be defined
        """
        self._has_one_column()
        self._validate_table_name()
        self._validate_unique_column_names()
        self._validate_exactly_one_primary_key()
        self._required_cols = {col.name for col in self.columns if not col.nullable}
        self._unique_cols = {col for col in self.columns if col.unique or col.primary_key}

    # endregion: Table Validation
    # region: Record Validation

    def _validate_schema(self, record: Record) -> None:
        """Validate record matches column schema.

        Args:
            record: The record to validate.
        """
        record_keys: set[str] = set(record.keys())
        if unknown := record_keys - self._column_names:
            raise ValueError(
                f"Unknown fields: {unknown}. Valid fields: {self._column_names}. Was a new column added? Update the schema accordingly if so!"
            )
        if missing := self._required_cols - record_keys:
            raise ValueError(f"Missing required fields: {missing}")

    def _handle_unique_constraint(
        self,
        record: Record,
        existing: CacheLookup | None = None,
        batch_lookups: CacheLookup | None = None,
    ) -> None:
        """Handle unique constraint for columns marked as unique.

        Args:
            record: The record to validate and potentially modify.
            existing: Pre-built lookup sets for existing records (optimization for batch).
            batch_lookups: Lookup sets for values in current batch (optimization for batch).
        """
        if existing is None:
            existing = {col.name: {rec.get(col.name) for rec in self.records} for col in self._unique_cols}
        if batch_lookups is None:
            batch_lookups = {col.name: set() for col in self._unique_cols}

        for col in self._unique_cols:
            value: Any = record.get(col.name)
            if value in existing[col.name] or value in batch_lookups[col.name]:
                msg: str = "Duplicate primary key" if col.primary_key else "Duplicate unique value"
                raise ValueError(f"{msg} '{value}' for column '{col.name}'.")
            batch_lookups[col.name].add(value)

    def _apply_defaults[T](self, record: Record) -> None:
        """Apply default values for missing fields before validation."""
        cols: list[Columns[T]] = [col for col in self.columns if not record.has(col.name)]

        for col in cols:
            default_value: T | None = col.get_default()
            if default_value is None:
                continue
            record.set(col.name, default_value)

            param = ParamWrapper(
                Parameter(name=col.name, kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=col.type_obj)
            )

            check_type: Any = col.type_obj if param.is_concrete else param.origin
            if check_type is not None and not isinstance(default_value, check_type):
                raise TypeError(
                    f"Default value for column '{col.name}' must be of type '{col.type}', got '{type(default_value).__name__}'."
                )

    def _assign_missing_primary_key(self, setter: Callable) -> None:
        """Assign primary key when missing from record.

        Args:
            setter: Callable to set the primary key value.
        """
        if self.is_auto and self.is_primary_int:
            setter(value=self.counter.tick())
        elif self.prime_default is not None and not self.is_auto:
            setter(value=self.prime_default)
        else:
            raise ValueError(f"Primary key '{self.primary_key}' is required.")

    def _handle_existing_pk(self, p_key: Any) -> None:
        """Handle auto-increment logic for existing integer primary key.

        Args:
            p_key: The current primary key value in the record.
        """
        if p_key < self._highest_int_pk:
            self.counter.set(self._highest_int_pk)
        elif p_key and p_key > self.counter.get():
            self.counter.set(int(p_key))

    def _handle_primary_key(self, record: Record) -> None:
        """Handle primary key assignment and auto-increment.

        Args:
            record: The record to validate and potentially modify.
        """
        p_key: Any = record.get(self.primary_key)

        if self.is_primary_str:
            return

        if not record.has(self.primary_key):
            self._assign_missing_primary_key(partial(record.set, key=self.primary_key))
        elif self.is_auto and self.is_primary_int:
            self._handle_existing_pk(p_key)
        elif self.is_auto and not self.is_primary_int:
            raise ValueError(f"Primary key '{self.primary_key}' must be an integer if autoincrement is enabled.")

    def _ensure_primary_key_first(self, record: Record) -> None:
        """Reorder record so primary key is first."""
        if self.primary_key not in record.root:
            return

        pk_value: Any = record.root.pop(self.primary_key)
        record.root = {self.primary_key: pk_value, **record.root}

        if self.is_primary_int and pk_value > self._highest_int_pk:
            self._highest_int_pk = pk_value

    def validate_record(
        self,
        record: Record,
        existing: CacheLookup | None = None,
        batched: CacheLookup | None = None,
    ) -> Record:
        """Validate record against table schema, adding primary_key if needed.

        Args:
            record: The record to validate.
            existing: Pre-built lookup sets for existing records (batch optimization).
            batched: Lookup sets for values in current batch (batch optimization).

        Returns:
            The validated record with primary key first.
        """
        self._handle_primary_key(record)
        self._apply_defaults(record)
        self._validate_schema(record)
        self._handle_unique_constraint(record, existing, batched)
        self._ensure_primary_key_first(record)
        return record

    def add_record(self, record: Record) -> None:
        """Add a record to a specific table.

        Args:
            record: Dictionary representing the record to add.
        """
        record = self.validate_record(record)
        self.records.append(record)

    def add_records(self, records: list[Record]) -> None:
        """Add multiple records to the table.

        Args:
            records: List of Record instances to add.
        """
        existing: CacheLookup = {col.name: {rec.get(col.name) for rec in self.records} for col in self._unique_cols}
        batched: CacheLookup = {col.name: set() for col in self._unique_cols}
        self.records.extend([self.validate_record(record, existing, batched) for record in records])

    # endregion: Record Validation
    # region: Record Management

    def clear(self, choice: str = "records") -> None:
        """Clear the table data.

        Args:
            choice: What to clear. Options are 'records', 'columns', or 'all'.
                     Default is 'records'.
        """
        if choice.lower() in ("records", "all"):
            self.records.clear()
        match choice.lower():
            case "columns":
                self.columns.clear()
                self._primary_col = NullColumn
                self._counter = None
            case "all":
                self.columns.clear()
                self._primary_col = NullColumn
                self._counter = None

    def insert(self, record: Record) -> None:
        """Insert a record into the table.

        Args:
            record: The record to insert.
        """
        self.records.append(record)

    def delete(self, record: Record) -> None:
        """Delete a record from the table.

        Args:
            record: The record to delete.
        """
        self.records.remove(record)

    def index(self, record: Record) -> int:
        """Get the index of a record in the table.

        Args:
            record: The record to find.

        Returns:
            The index of the record.
        """
        return self.records.index(record)

    def iterate(self) -> Iterator[Record]:
        """Iterate over the records in the table.

        Returns:
            An iterator over the records.
        """
        return iter(self.records)

    # endregion: Record Management
    # region: Class Methods and Dunder Methods

    @classmethod
    def new(cls, name: str, columns: list[Columns]) -> Self:
        """Create a new empty table and add it to the unified data format.

        Args:
            name: Name of the new table.
            columns: Optional list of Columns instances.

        Returns:
            A new TableData instance.
        """
        return cls(name=name, columns=columns)

    def __len__(self) -> int:
        """Get the number of records in the table."""
        return len(self.records)

    def __hash__(self) -> int:
        """Get the hash of the table based on its name."""
        columns: int = hash(freeze(sorted([hash(column) for column in self.columns])))
        records: int = hash(freeze(sorted([hash(record) for record in self.records])))
        return hash(f"{self.name}-{columns}-{records}")

    def __repr__(self) -> str:
        return f"TableData(name={self.name}, columns={self.columns}, records={self.records})"

    # endregion: Class Methods and Dunder Methods


__all__ = ["TableData"]
