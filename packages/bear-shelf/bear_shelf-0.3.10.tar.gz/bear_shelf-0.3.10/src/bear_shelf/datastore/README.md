# bear_shelf.datastore

Lightweight document storage with pluggable backends, schema-aware tables, and
TinyDB-style querying. This package powers persistent settings, logging buffers,
and other structured data inside Bear Dereth.

## Key Pieces
- `BearBase`: Main entry point that manages tables, storage, and query caching.
- `Columns`: Schema objects describing table fields (type, defaults, PK flags).
- `Table`: Record container returned by `BearBase.table(...)`.
- `Record` / `Records`: Dict-like rows with helpers for iteration and result
  handling.
- `StorageChoices` & `get_storage`: Select between JSON, JSONL, TOML, YAML,
  XML, MessagePack, or in-memory storage.
- `TableHandler`, `UnifiedDataFormat`: Internal plumbing for loading/saving
  tables; exposed for advanced scenarios.


---

## Quick Start

```python
from bear_shelf.datastore import BearBase, Columns, Record
from bear_shelf.query import where_map as where

# Initialize with JSONL storage (default) or pick another StorageChoices value
db = BearBase(file="settings.jsonl", storage="jsonl")

# Define and register a table schema
columns = [
    Columns(name="key", type="str", primary_key=True),
    Columns(name="value", type="str"),
]
table = db.create_table("settings", columns=columns)

# Insert data
table.insert({"key": "theme", "value": "midnight"})
db.insert(key="volume", value="11")  # uses current table

# Query with the unified query API
Q = where("key")
matches = table.search(Q == "theme")
assert matches.first()["value"] == "midnight"

db.close()
```

Notes:
- Passing `":memory:"` as the first argument forces in-memory storage
  (`storage="memory"`).
- `BearBase` acts as the facade; attribute access falls back to the current
  table so `db.all()` is equivalent to `table.all()` once a table is selected.
- Use `with BearBase(file="...") as db:` to ensure the storage handle is closed.

---

## Tables & Schema

`Columns` instances describe table fields:

- `name`: Column name.
- `type`: Stored as a string (e.g., `"int"`, `"str"`). Automatically coerces
  from Python types supplied in `Columns[int]`.
- `default`, `nullable`, `primary_key`, `autoincrement`: Optional metadata used
  when enforcing schema or generating defaults.

Creating tables:

```python
columns = [
    Columns(name="id", type="int", primary_key=True, autoincrement=True),
    Columns(name="name", type="str"),
]
table = db.create_table("users", columns)
```

`Table` exposes the core CRUD surface:
- `insert`, `insert_all`
- `all`, `get`, `contains`
- `search` (takes a `QueryProtocol`, e.g., from `bear_shelf.query`)
- `update`, `upsert`, `delete` (via operations from `TableProtocol`)
- `primary_key` property returns the PK column if defined.

`Table.commit()` persists pending changes; it is invoked automatically after
mutations unless WAL support is enabled.

---

## Write-Ahead Logging (WAL) 📝✨

WAL provides crash-safe durability for batch operations by logging changes before
applying them to the database. This prevents data loss in case of crashes or power
failures during bulk updates.

### Enabling WAL

WAL can be enabled globally for all tables or per-table:

**Global WAL (all tables):**
```python
from bear_shelf.datastore import BearBase, Columns

# Enable WAL for all tables in this database
db = BearBase("data.json", storage="json", enable_wal=True)

# Tables created will automatically have WAL enabled
db.create_table("users", columns=[
    Columns(name="id", type="int", primary_key=True),
    Columns(name="name", type="str"),
])

# WAL files auto-generated as {table_name}.wal in the same directory
```

**Per-table WAL:**
```python
# WAL disabled by default, enable only for specific tables
db = BearBase("data.json", storage="json")

# Enable WAL just for this table
db.create_table("users", columns=[...], enable_wal=True)

# Or specify a custom WAL file path
db.create_table("orders", columns=[...], enable_wal=True, wal_file="/custom/path/orders.wal")
```

**Custom WAL directory:**
```python
# Store all WAL files in a specific directory
db = BearBase("data.json", storage="json", enable_wal=True, wal_dir="/var/wal")
```

### WAL Operations

WAL-enabled tables support batch operations that log changes before writing:

```python
# Batch insert with WAL
records = [
    {"id": 1, "name": "Bear"},
    {"id": 2, "name": "Shannon"},
    {"id": 3, "name": "Claude"},
]
table.insert_all(records, checkpoint=False)  # Logged to WAL, not immediately saved

# Batch update with WAL
from bear_shelf.query import where_map as Q
updates = [{"active": True}]
table.update_all(updates, cond=Q("id") < 3, checkpoint=False)

# Batch delete with WAL
table.delete_all(pk_kwargs_list=[{"id": 2}], checkpoint=False)

# Checkpoint to flush to disk and clear WAL
if table.wal_helper:
    table.wal_helper.checkpoint(table)
```

### Crash Recovery

After a crash, WAL files can be replayed to recover committed transactions:

```python
from bear_shelf.datastore.wal_helper import WALHelper

# After crash/restart, check if WAL file exists
wal_path = Path("users.wal")
if wal_path.exists():
    # Open database (don't auto-start WAL yet)
    db = BearBase("data.json", storage="json")
    table = db.table("users")

    # Create WAL helper in recovery mode (auto_start=False)
    wal_helper = WALHelper(file=wal_path, table_name="users", auto_start=False)

    # Replay committed transactions from WAL
    wal_helper.recover_from_wal(table)

    # WAL is now cleared, can re-enable for future operations
    table.enable_wal = True
```

### How WAL Works

1. **Logging**: Each batch operation logs individual changes to the WAL file with a
   transaction ID
2. **Commit**: After logging, each transaction is marked as committed
3. **Recovery**: Only committed transactions are replayed during recovery
4. **Checkpoint**: Flushes changes to disk and clears the WAL

### WAL vs Immediate Save

- **Without WAL** (`checkpoint=True`): Changes are immediately written to disk
- **With WAL** (`checkpoint=False`): Changes are logged to WAL; disk write is deferred
  until checkpoint

### Performance Considerations

- WAL uses a background thread for async writes
- Large batches may take time to flush (use `time.sleep(0.1)` in tests)
- WAL provides durability at the cost of an extra write pass

### Cleanup

WAL background threads are automatically cleaned up when closing tables or databases:

```python
# Table cleanup stops WAL threads
table.close()

# Or close the entire database (closes all tables)
db.close()

# Context manager handles cleanup automatically
with BearBase("data.json", enable_wal=True) as db:
    table = db.create_table("users", columns=[...])
    # ... work with table ...
# WAL threads automatically stopped on exit
```

---

## Records & Query Integration

Each row is a `Record` (dict-like object) so you can treat it like a standard
dictionary:

```python
record = Record(key="timezone", value="UTC")
table.insert(record)

res = table.get(key="timezone")
if res:
    first = res.first()
    print(first["value"])
```

`Records` collections support:
- `.first()`, `.all()`, `.count`
- Iteration (`for rec in records`)
- Truthiness (`if records:`) and emptiness checks via `NullRecords`

Queries integrate with `bear_shelf.query`:

```python
from bear_shelf.query import where_map as Q

popular = table.search((Q("followers") > 100) & (Q("active") == True))
```

Cache behaviour:
- `BearBase` keeps an LRU cache of query → record lists per table.
- If a query contains non-hashable operations it marks itself `NotCacheable`,
  skipping the cache.

---

## Storage Backends

`StorageChoices` covers available engines:

| Choice    | Backend Class     | Size (sample data) | Notes                                    |
| --------- | ----------------- | ------------------ | ---------------------------------------- |
| `jsonl`   | `JSONLStorage`    | 1.3K               | Default; append-friendly, great for logs |
| `json`    | `JsonStorage`     | 1.8K               | Simple JSON document                     |
| `toml`    | `TomlStorage`     | 1.1K               | Human-readable, typed values             |
| `yaml`    | `YamlStorage`     | 1.1K               | YAML output                              |
| `xml`     | `XMLStorage`      | 1.7K               | XML documents                            |
| `msgpack` | `MsgPackStorage`  | 697 bytes          | Binary format, most space-efficient      |
| `memory`  | `InMemoryStorage` | N/A                | Ephemeral, keeps data in-process         |

You can subclass `BearBase` to set a default storage:

```python
from bear_shelf.datastore import JSONLBase

with JSONLBase(file="demo.jsonl") as db:
    ...
```

`TableHandler`, `TableData`, and `UnifiedDataFormat` underpin the storage
interface—most applications only need them when implementing custom tooling or
migration logic.

---

## Advanced Tips
- `HeaderData` (for file headers) and `Columns.frozen_dump()` are available when
  you need deterministic serialization (e.g., hashing table definitions).
- `TableHandler` can be used to plug additional behaviors into `BearBase`
  (custom save callbacks, WAL experiments, etc.).
- The datastore plays nicely with settings management—see
  `bear_shelf.config.settings_manager` for a high-level wrapper that maps
  columns to models.

---

## Adding a New Storage Backend

Adding a new storage backend is now fully automated! Just create your storage class
and run a single command.

### 1. Create the Storage Class

Create `src/bear_shelf/datastore/storage/your_format.py`:

```python
from bear_shelf.datastore.storage._common import Storage
from bear_shelf.datastore.unified_data import UnifiedDataFormat
from bear_shelf.files.helpers import touch

class YourStorage(Storage):
    def __init__(self, file: str | Path, file_mode: str = "r+") -> None:
        super().__init__()
        self.file: Path = touch(file, mkdir=True, create_file=True)
        self.handler = YourFileHandler(file=self.file, mode=file_mode)

    def read(self) -> UnifiedDataFormat | None:
        """Read and deserialize. Filter records to match schema columns."""
        # Your implementation here
        pass

    def write(self, data: UnifiedDataFormat) -> None:
        """Serialize and write. Filter records to match schema columns."""
        # Your implementation here
        pass

    def close(self) -> None:
        if self.closed:
            return
        self.handler.close()

    @property
    def closed(self) -> bool:
        return self.handler.closed
```

### 2. Auto-Register the Backend

Run the sync command to automatically discover and register your new storage:

```bash
bear-dereth sync-storage
```

This will:
- ✅ Scan the `storage/` directory for Storage subclasses
- ✅ Auto-generate imports in `_dynamic_storage.py`
- ✅ Update the `StorageChoices` Literal type
- ✅ Add your backend to `STORAGE_MAP`
- ✅ Generate type-safe overloads for `get_storage()`
- ✅ Format the generated code with ruff

### 3. Add Tests

Create `tests/bearbase/test_your_storage.py` covering:
- Basic read/write round-trip
- Empty file handling  
- Record validation
- Multiple tables

### 4. Generate Sample Files

Update `tests/bearbase/test_storage_output.py`:

```python
from bear_shelf.datastore.storage.your_format import YourStorage

# Add to parametrize list
@pytest.mark.parametrize(
    ("storage_class", "file_extension"),
    [..., (YourStorage, "your_ext")],
)

# Add to test body
your_path = data_dir / "sample.your_ext"
your_storage = YourStorage(your_path, file_mode="w+")
your_storage.write(get_unified_data)
your_storage.close()
assert your_path.exists()
assert your_path.stat().st_size > 0
```

### 5. Update This README

Add your backend to the "Storage Backends" table with size comparison.

### That's It!

No manual editing of imports, Literals, or overloads needed. The plugin system
automatically discovers and registers any new Storage subclass.

**Example:** See `msgpack.py` for a complete reference. MessagePack achieved 60% 
size reduction (697 bytes vs 1.8K JSON) while maintaining full compatibility.

Store safely, Bear! 🐻📚✨
