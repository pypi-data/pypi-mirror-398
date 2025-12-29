# Storage Backend Architecture Sketch

## Overview
Generalize the storage layer so the dialect can work with JSONL, JSON, TOML, or in-memory storage without changing the core logic.

## ✅ IMPLEMENTATION STATUS (2025-01-10)

**COMPLETED:**
- ✅ `JSONLFilehandler` moved to bear-dereth at `src/bear_dereth/files/file_handlers/jsonl_file_handler.py`
- ✅ `JSONLStorage` created in bear-dereth at `src/bear_dereth/datastore/storage/jsonl.py`
- ✅ Exported from bear-dereth datastore module
- ✅ Follows same interface as `JsonStorage` and `TomlStorage`

**NEXT STEPS:**
1. Release bear-dereth with JSONLStorage
2. Update bear-shelf to import from bear-dereth
3. Remove bear-shelf's local jsonl_handler.py
4. Define clear data format standards across layers

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              SQLAlchemy Dialect                     │
│  (Handles SQL compilation, execution, transactions) │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                  DataStore                          │
│  (In-memory dict, search/insert/update/delete)      │
│  - Uses QueryMapping for WHERE clauses              │
│  - Table-agnostic record management                 │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│            StorageBackend (Protocol)                │
│  - load() -> dict[table_name, records]              │
│  - save(data) -> None                               │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬─────────────┐
        ▼              ▼              ▼             ▼
    ┌───────┐    ┌──────────┐   ┌────────┐   ┌─────────┐
    │ JSONL │    │   JSON   │   │  TOML  │   │ Memory  │
    └───────┘    └──────────┘   └────────┘   └─────────┘
```

## Protocol Definition

```python
from typing import Protocol, Any
from pathlib import Path

class StorageBackend(Protocol):
    """Protocol for storage backends."""
    
    @property
    def path(self) -> Path | None:
        """Path to storage file (None for in-memory)."""
        ...
    
    def load(self) -> dict[str, list[dict[str, Any]]]:
        """Load all tables and their records.
        
        Returns:
            dict mapping table names to lists of record dicts
            Example: {
                "users": [
                    {"id": 1, "name": "Bear", "age": 30},
                    {"id": 2, "name": "Claire", "age": 21}
                ],
                "posts": [...]
            }
        """
        ...
    
    def save(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Save all tables and their records.
        
        Args:
            data: dict mapping table names to lists of record dicts
        """
        ...
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in storage."""
        ...
    
    def drop_table(self, table_name: str) -> None:
        """Remove a table from storage."""
        ...
```

## Backend Implementations

### 1. JSONLBackend (Current Format)

```python
class JSONLBackend:
    """Storage backend using JSONL format (one record per line)."""
    
    def __init__(self, path: Path):
        self._path = path
    
    @property
    def path(self) -> Path:
        return self._path
    
    def load(self) -> dict[str, list[dict[str, Any]]]:
        """Load from JSONL format:
        {"_table": "users"}
        {"id": 1, "name": "Bear", "age": 30}
        {"id": 2, "name": "Claire", "age": 21}
        {"_table": "posts"}
        {"id": 1, "title": "Hello"}
        """
        if not self._path.exists():
            return {}
        
        # Use existing JSONLFilehandler and Lines parser
        from bear_shelf.jsonl_handler import JSONLFilehandler
        from bear_shelf.db_schema.jsonl_structure import Lines
        
        with JSONLFilehandler(self._path, mode="r") as handler:
            content = handler.splitlines(load=True)
        
        parsed = Lines.from_lines(content)
        return {
            table_name: [record.data for record in parsed.records_for_table(table_name)]
            for table_name in parsed.tables
        }
    
    def save(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Save to JSONL format."""
        from bear_shelf.db_schema.jsonl_structure import LineStructure
        from bear_shelf.jsonl_handler import JSONLFilehandler
        
        structure = LineStructure()
        for table_name, records in data.items():
            # Need table definition - get from TableManager
            # This is where we'd need to refactor slightly
            structure.create_table_simple(table_name)
            for record in records:
                structure.add(table_name, record)
        
        with JSONLFilehandler(self._path, mode="w") as handler:
            handler.write(structure.render())
```

### 2. JSONBackend (Plain JSON)

```python
class JSONBackend:
    """Storage backend using plain JSON format."""
    
    def __init__(self, path: Path, indent: int = 2):
        self._path = path
        self._indent = indent
    
    @property
    def path(self) -> Path:
        return self._path
    
    def load(self) -> dict[str, list[dict[str, Any]]]:
        """Load from JSON format:
        {
            "users": [
                {"id": 1, "name": "Bear", "age": 30},
                {"id": 2, "name": "Claire", "age": 21}
            ],
            "posts": [
                {"id": 1, "title": "Hello"}
            ]
        }
        """
        if not self._path.exists():
            return {}
        
        import json
        with open(self._path) as f:
            return json.load(f)
    
    def save(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Save to JSON format."""
        import json
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, 'w') as f:
            json.dump(data, f, indent=self._indent)
    
    def table_exists(self, table_name: str) -> bool:
        data = self.load()
        return table_name in data
    
    def drop_table(self, table_name: str) -> None:
        data = self.load()
        if table_name in data:
            del data[table_name]
            self.commit(data)
```

### 3. TOMLBackend

```python
class TOMLBackend:
    """Storage backend using TOML format."""
    
    def __init__(self, path: Path):
        self._path = path
    
    @property
    def path(self) -> Path:
        return self._path
    
    def load(self) -> dict[str, list[dict[str, Any]]]:
        """Load from TOML format:
        [[users]]
        id = 1
        name = "Bear"
        age = 30
        
        [[users]]
        id = 2
        name = "Claire"
        age = 21
        
        [[posts]]
        id = 1
        title = "Hello"
        """
        if not self._path.exists():
            return {}
        
        import tomllib  # Python 3.11+
        with open(self._path, 'rb') as f:
            return tomllib.load(f)
    
    def save(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Save to TOML format."""
        import tomli_w  # For writing TOML
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, 'wb') as f:
            tomli_w.dump(data, f)
```

### 4. MemoryBackend (No File)

```python
class MemoryBackend:
    """In-memory storage backend (no file persistence)."""
    
    def __init__(self):
        self._data: dict[str, list[dict[str, Any]]] = {}
    
    @property
    def path(self) -> None:
        return None
    
    def load(self) -> dict[str, list[dict[str, Any]]]:
        """Return in-memory data."""
        return self._data.copy()
    
    def save(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Update in-memory data."""
        self._data = data.copy()
    
    def table_exists(self, table_name: str) -> bool:
        return table_name in self._data
    
    def drop_table(self, table_name: str) -> None:
        self._data.pop(table_name, None)
```

## DataStore Refactor

```python
class DataStore:
    """In-memory data store with pluggable storage backend."""
    
    def __init__(self, backend: StorageBackend):
        self.backend = backend
        self._data: dict[str, list[dict[str, Any]]] = {}
        self._loaded = False
    
    def load_from_backend(self) -> None:
        """Load data from the storage backend."""
        if not self._loaded:
            self._data = self.backend.load()
            self._loaded = True
    
    def write_to_backend(self) -> None:
        """Write data to the storage backend."""
        self.backend.commit(self._data)
    
    # All the existing methods stay the same!
    def search(self, table_name: str, condition: QueryProtocol | None) -> list[dict]:
        """Search implementation doesn't change."""
        ...
    
    def insert_record(self, table_name: str, record: dict) -> None:
        """Insert implementation doesn't change."""
        ...
    
    # etc.
```

## Dialect Connection String

Make the backend configurable via the connection string:

```python
# JSONL (default)
create_engine("bearshelf:///path/to/database.jsonl")

# JSON
create_engine("bearshelf:///path/to/database.json?backend=json")

# TOML
create_engine("bearshelf:///path/to/database.toml?backend=toml")

# Memory (for testing)
create_engine("bearshelf:///:memory:")
```

## Separation of Concerns: Data Layers 🎯

### Layer 1: Storage Format (Disk)
What's actually written to disk - format-specific:
- **JSON**: Single JSON object or array
- **JSONL**: One JSON object per line
- **TOML**: TOML sections and key-value pairs

### Layer 2: Storage Interface (Storage ABC)
Generic dict-like data - format-agnostic:
- **Type**: `dict[str, Any]` - completely flexible
- **Storage backends are DUMB**: Just serialize/deserialize
- **No schema enforcement**: Storage doesn't care about structure
- **No transformation**: Pass through whatever dict you give them

### Layer 3: Table/Document Layer
Generic record management:
- **Type**: Works with `Document` (generic dict with doc_id)
- **Operations**: search, insert, update, delete
- **No type validation**: Just manages collections of records

### Layer 4: Application Layer  
Typed, validated business logic:
- **Type**: `SettingsRecord`, custom Pydantic models
- **Type safety**: Automatic type detection and validation
- **Business rules**: Application-specific logic
- **Examples**: SettingsManager (key/value pairs), ORM models (tables)

## Architecture Diagram

```
┌─────────────────────────────────────┐
│   Application (SettingsManager)     │  ← Layer 4: Typed models
│   - Uses SettingsRecord             │     (SettingsRecord, Pydantic)
│   - Validates types                 │
│   - Business logic                  │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│    Table (JsonFileStorage)          │  ← Layer 3: Document management
│    - search, upsert, contains       │     (Document, generic records)
│    - manages record collections     │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  Storage (JsonStorage, JSONLStorage) │  ← Layer 2: Raw data I/O
│  - read() → dict[str, Any]          │     (No type assumptions)
│  - write(data: dict[str, Any])      │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│        Disk (JSON/JSONL/TOML)       │  ← Layer 1: Bytes on disk
└─────────────────────────────────────┘
```

## Data Format Standards

### For bear-shelf (Multi-table database):
```python
# Structure: {table_name: [record1, record2, ...]}
{
    "users": [
        {"id": 1, "name": "Bear", "age": 30},
        {"id": 2, "name": "Claire", "age": 21}
    ],
    "posts": [
        {"id": 1, "title": "Hello", "user_id": 1}
    ]
}
```

### For SettingsManager (Key-value store):
```python
# Structure: {table_name: [record1, record2, ...]}
{
    "settings": [
        {"key": "theme", "value": "dark", "type": "string"},
        {"key": "max_connections", "value": 100, "type": "number"}
    ]
}
```

### JSONL On-Disk Format:
```jsonl
{"_table": "users", "id": 1, "name": "Bear", "age": 30}
{"_table": "users", "id": 2, "name": "Claire", "age": 21}
{"_table": "posts", "id": 1, "title": "Hello", "user_id": 1}
```

## Benefits

1. **Easy Testing** - Use MemoryBackend for fast tests
2. **Flexible Storage** - Users choose format based on needs
3. **Clean Separation** - Backend logic completely decoupled from DataStore
4. **Bear-dereth Integration** - Same backends work across all projects!
5. **Future Expansion** - Easy to add SQLite backend, Redis backend, etc.
6. **Type Safety at Application Layer** - Not at storage layer
7. **No Format Lock-in** - Storage is format-agnostic

## Migration Path

1. ✅ Create StorageBackend protocol
2. ✅ Implement JSONLBackend (wraps existing code)
3. ✅ Update DataStore to use backend
4. ✅ Implement JSONBackend, MemoryBackend
5. ✅ Update Dialect's `create_connect_args` to parse backend from URL
6. ✅ Implement TOMLBackend (optional)
7. ✅ Port to bear-dereth!
