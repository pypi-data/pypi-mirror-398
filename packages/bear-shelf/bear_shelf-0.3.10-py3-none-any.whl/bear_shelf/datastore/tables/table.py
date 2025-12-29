"""This module implements tables, the central place for accessing and manipulating documents."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Self, overload

from lazy_bear import lazy

from bear_shelf.datastore.record import NullRecords, Record, Records
from bear_shelf.datastore.tables.protocol import TableProtocol

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from pathlib import Path

    from frozen_cub.lru_cache import LRUCache

    from bear_shelf.datastore.columns import Columns
    from bear_shelf.datastore.wal.helper import WALHelper, WALHelperDummy
    from funcy_bear.query import QueryProtocol

    from .data import TableData
else:
    LRUCache = lazy("frozen_cub.lru_cache", "LRUCache")
    QueryProtocol = lazy("funcy_bear.query", "QueryProtocol")
    WALHelper, WALHelperDummy = lazy("bear_shelf.datastore.wal.helper", "WALHelper", "WALHelperDummy")


class Table(TableProtocol[Record, Records]):
    """A table in the datastore, managing records and providing query capabilities."""

    default_query_cache_capacity = 10

    def __init__(
        self,
        name: str,
        table_data: TableData,
        commit_callback: Callable[[], None],
        cache_size: int = default_query_cache_capacity,
        enable_wal: bool = False,
        wal_file_path: str | Path | None = None,
        wal_config: Any | None = None,  # WALConfig type, Any to avoid circular import
    ) -> None:
        """Create a table instance.

        Args:
            name: The table name
            table_data: The table's data
            commit_callback: Callback to commit changes to storage
            cache_size: Size of the query cache
            enable_wal: Whether to enable Write-Ahead Logging
            wal_file_path: Path to the WAL file (only used if enable_wal is True)
            wal_config: WAL configuration (uses buffered defaults if None)
        """
        self._name: str = name
        self.enable_wal: bool = enable_wal
        self._query_cache: LRUCache[QueryProtocol, Records] = LRUCache(capacity=cache_size)
        self._table_data: TableData = table_data
        self._commit_callback: Callable[[], None] = commit_callback
        self._wal_helper: WALHelper | None = None

        if enable_wal:
            if wal_file_path is None:
                raise ValueError("wal_file_path is required when enable_wal is True")
            self._wal_helper = WALHelper(file=wal_file_path, table_name=name, config=wal_config)

    @property
    def name(self) -> str:
        """Get the table name."""
        return self._name

    @property
    def table_data(self) -> TableData:
        """Get the current table data, loading from storage if necessary."""
        return self._table_data

    @property
    def primary_key(self) -> str:
        """Get the primary key column name.

        Note: TableData validation (data.py:_validate_exactly_one_primary_key)
        ensures every table has exactly one primary key, so this RuntimeError
        should never occur in normal operation.
        """
        for col in self.table_data.columns:
            if col.primary_key:
                return col.name
        raise RuntimeError("Table has no primary key (should be impossible after validation)")

    @property
    def query_cache(self) -> LRUCache[QueryProtocol, Records]:
        """Get the query cache."""
        return self._query_cache

    @property
    def wal_helper(self) -> WALHelper:
        """Get the WAL helper if WAL is enabled."""
        if not self.enable_wal or self._wal_helper is None:
            self._wal_helper = WALHelperDummy()
        return self._wal_helper

    def commit(self) -> None:
        """Commit the current state of the table to storage."""
        self._commit_callback()
        self.query_cache.clear()

    def _doc_check(self, record: Any, **kwargs) -> Record:
        """Check the record before insertion or update.

        Args:
            record: The record to check
        Returns:
            The record data as a dictionary
        """
        if record is None:
            record = Record(**kwargs)
        elif isinstance(record, dict):
            record = Record(**record)
        return record

    def _with_wal_or_save(
        self,
        wal_log_fn: Callable,
        memory_fn: Callable | None = None,
        flush: bool = False,
        **kwargs,
    ) -> None:
        """Execute operation with WAL logging or immediate save.

        Args:
            wal_log_fn: Function to log operation to WAL
            memory_fn: Function to update in-memory data, optional
            flush: Whether to save after operation, overriding WAL
            **kwargs: Arguments to pass to the functions
        """
        if (self.enable_wal and self.wal_helper) and not flush:
            wal_log_fn(**kwargs)
            memory_fn(**kwargs) if memory_fn is not None else None
            self.query_cache.clear()  # We just updated the memory data, so clear query cache to prevent stale reads
        else:
            memory_fn(**kwargs) if memory_fn is not None else None
            self.commit()

    def get(
        self,
        cond: QueryProtocol | None = None,
        default: Any = NullRecords,
        **pk_kwargs,
    ) -> Records:
        """Get a single record by primary key or query.

        Args:
            cond: Query condition to match
            default: Value to return if no record is found
            **pk_kwargs: Primary key field values as keyword arguments
        """
        if pk_kwargs:
            for rec in self.table_data.records:
                if all(rec.get(k) == v for k, v in pk_kwargs.items()):
                    return Records(record=rec)
            return default
        if cond:
            return self.search(cond)

        raise ValueError("Must provide either primary key kwargs or query condition")

    def set(self, key: str, value: Any) -> None:
        """Set a key-value pair.

        Args:
            key: The key to set in the record.
            value: The value to set for the key.
        """
        records: Records = self.get(key=key)
        if records is not NullRecords and records.count > 0:
            record: Record = records.first()
            record[key] = value
        self.commit()

    def search(self, query: QueryProtocol) -> Records:
        """Search for records matching a query."""
        cached: Records | None = self.query_cache.get(query)
        if cached is not None:
            if cached is NullRecords:
                return NullRecords
            return cached
        results: Records = Records([rec for rec in self.table_data.records if query(rec)])

        if query.is_cacheable:
            self.query_cache[query] = results if results.count > 0 else NullRecords
        return results

    @overload
    def all(self, *, list_recs: Literal[False]) -> Records: ...
    @overload
    def all(self, *, list_recs: Literal[True] = True) -> list[Record]: ...

    def all(self, **kwargs) -> Records | list[Record]:
        """Get all records from the table.

        Args:
            list_recs: Whether to return records as a list (default: False)

        Returns:
            Records: All records in the table.
        """
        records: list[Record] = self.table_data.records
        if kwargs.pop("list_recs", False):
            return records
        return Records(records)

    def insert(self, record: dict | Record | None = None, **kwargs) -> None:
        """Insert a new record into the table.

        Args:
            record: Dictionary or Record instance to insert
            **kwargs: Field values as keyword arguments
        """
        record = self._doc_check(record=record, **kwargs)
        self._with_wal_or_save(
            wal_log_fn=self.wal_helper.insert,
            memory_fn=self.table_data.add_record,
            record=record,
        )

    def insert_all(self, records: Sequence[dict | Record], flush: bool = False) -> None:
        """Insert multiple records into the table.

        Args:
            records: List of dictionaries or Record instances to insert
            flush: Whether to save after insert is complete, overriding
                the usage of wal if enabled
        """
        record_instances: list[Record] = [self._doc_check(record=r) for r in records]
        self._with_wal_or_save(
            wal_log_fn=self.wal_helper.insert_batch,
            memory_fn=self.table_data.add_records,
            records=record_instances,
            flush=flush,
        )

    def update(
        self,
        fields: dict | None = None,
        cond: QueryProtocol | None = None,
        flush: bool = False,
        **kwargs,
    ) -> int:
        """Update records matching a condition.

        Args:
            fields: Dictionary of field updates to apply
            cond: Query condition to match records for update
            flush: Whether to save after update is complete, overriding WAL
            **kwargs: Field updates as keyword arguments (merged with fields dict)

        Returns:
            Number of records updated

        Examples:
            # Update with dict
            table.update({'status': 'active'}, cond=Q.id == 1)

            # Update with kwargs
            table.update(status='active', updated_at=datetime.now())

            # Update specific record by primary key
            table.update({'count': 42}, id=5)
        """
        if fields is None and not kwargs:
            raise ValueError("Must provide fields to update as dict or kwargs")
        if fields is not None and not isinstance(fields, dict):
            raise TypeError(
                f"Update fields must be a dict, not {type(fields).__name__}. "
                "Callable updates are not supported. Apply transformations before calling update()."
            )

        updates: list[tuple[dict[str, Any], dict[str, Any]]] = []

        if fields is None:
            fields = kwargs or {}
        elif kwargs:
            fields = {**fields, **kwargs}

        if self.primary_key in fields:  # Remove primary key from update fields to prevent modification
            fields = {k: v for k, v in fields.items() if k != self.primary_key}

        for record in self.table_data.records:
            if cond is None or cond(record):
                updates.append(({self.primary_key: record.get(self.primary_key)}, fields))
                for k, v in fields.items():
                    record[k] = v
        if updates:
            self._with_wal_or_save(wal_log_fn=self.wal_helper.update_batch, updates=updates, flush=flush)
        return len(updates)

    def update_all(
        self,
        updates: Sequence[dict],
        cond: QueryProtocol | None = None,
        flush: bool = False,
    ) -> int:
        """Update multiple records matching a condition.

        Args:
            updates: Sequence of dict field updates to apply to each matching record
            cond: Query condition to match records for update
            flush: Whether to save after update is complete, overriding WAL

        Returns:
            Number of records updated

        Examples:
            # Apply multiple updates to matching records
            table.update_all(
                [{'status': 'active'}, {'priority': 'high'}],
                cond=Q.category == 'urgent'
            )
        """
        for update in updates:
            if not isinstance(update, dict):
                raise TypeError(
                    f"All updates must be dicts, not {type(update).__name__}. Callable updates are not supported."
                )

        wal_updates: list[tuple[dict[str, Any], dict[str, Any]]] = []
        records_to_update: list[Record] = [rec for rec in self.table_data.records if cond is None or cond(rec)]

        for record in records_to_update:
            for update in updates:
                wal_updates.append(({self.primary_key: record.get(self.primary_key)}, update))
                for k, v in update.items():
                    record[k] = v

        if wal_updates:
            self._with_wal_or_save(wal_log_fn=self.wal_helper.update_batch, updates=wal_updates, flush=flush)
        return len(records_to_update) * len(updates)

    def upsert(
        self,
        record: dict | Record | None = None,
        cond: QueryProtocol | None = None,
        **kwargs,
    ) -> None:
        """Update existing record or insert new one.

        Args:
            record: Record data to upsert
            cond: Query condition to find existing record
            **kwargs: Field values as keyword arguments
        """
        record = self._doc_check(record=record, **kwargs)
        if cond is not None:
            updated: int = self.update(fields=dict(record), cond=cond)
            if updated > 0:
                return
        self.insert(record)

    def delete(self, cond: QueryProtocol | None = None, **pk_kwargs) -> int:
        """Delete records matching a condition or primary key.

        Args:
            cond: Query condition to match records for deletion
            **pk_kwargs: Primary key field values as keyword arguments

        Returns:
            Number of records deleted
        """
        if not cond and not pk_kwargs:
            raise ValueError("Must provide either primary key kwargs or query condition")

        to_delete: list[Record] = []
        if pk_kwargs:
            to_delete = [rec for rec in self.table_data.records if all(rec.get(k) == v for k, v in pk_kwargs.items())]
        elif cond:
            to_delete = [rec for rec in self.table_data.records if cond(rec)]

        pk_values: list[dict[str, Any]] = [{self.primary_key: rec.get(self.primary_key)} for rec in to_delete]

        for rec in to_delete:
            self.table_data.delete(rec)

        if pk_values:
            self._with_wal_or_save(wal_log_fn=self.wal_helper.delete_batch, primary_key_values=pk_values)
        return len(to_delete)

    def delete_all(
        self,
        cond: QueryProtocol | None = None,
        pk_kwargs_list: Sequence[dict] | None = None,
        flush: bool = False,
    ) -> int:
        """Delete multiple records matching a condition or primary keys.

        Args:
            cond: Query condition to match records for deletion
            pk_kwargs_list: Sequence of primary key field values as dictionaries
            flush: Whether to save after deletion is complete, overriding WAL

        Returns:
            Number of records deleted
        """
        if not cond and not pk_kwargs_list:
            raise ValueError("Must provide either primary key kwargs list or query condition")

        to_delete: list[Record] = []
        pk_values: list[dict[str, Any]] = []

        if pk_kwargs_list:
            for pk_kwargs in pk_kwargs_list:
                matching: list[Record] = [
                    rec for rec in self.table_data.records if all(rec.get(k) == v for k, v in pk_kwargs.items())
                ]
                to_delete.extend(matching)
                pk_values.extend(pk_kwargs for _ in matching)
        elif cond:
            for rec in self.table_data.records:
                if cond(rec):
                    to_delete.append(rec)
                    pk_values.append({self.primary_key: rec.get(self.primary_key)})

        for rec in to_delete:
            self.table_data.delete(rec)

        if pk_values:
            self._with_wal_or_save(wal_log_fn=self.wal_helper.delete_batch, primary_key_values=pk_values, flush=flush)

        return len(to_delete)

    def get_columns(self) -> list[Columns]:
        """Get a list of all Columns in the table."""
        return self.table_data.columns

    def contains(self, query: QueryProtocol) -> bool:
        """Check if any record matches the query."""
        return any(query(rec) for rec in self.table_data.records)

    def columns(self) -> list[str]:
        """Get a list of all column names in the table."""
        columns: list[Columns] = self.table_data.columns
        return [col.name for col in columns]

    def records(self) -> Records:
        """Get all records in the table as a Records instance."""
        return self.all(list_recs=False)

    def count(self) -> int:
        """Get the number of records in the table."""
        return len(self.table_data)

    def clear(self) -> None:
        """Clear all records in the table."""
        self.table_data.clear()
        self.query_cache.clear()

    def close(self, clear: bool = True, delete: bool = True) -> None:
        """Close the table, releasing any resources."""
        self.query_cache.clear()
        if self.wal_helper:
            self.wal_helper.close(clear=clear, delete=delete)

    def __call__(self) -> Self:
        """Reload the table data from storage."""
        return self

    def __iter__(self) -> Iterator[Record]:
        """Iterate over the records in the table."""
        return self.table_data.iterate()

    def __len__(self) -> int:
        """Get the number of records in the table."""
        return len(self.table_data)
