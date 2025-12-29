# Bear Shelf - AI Coding Agent Instructions

## Project Identity
This is **Bear Shelf**: a lightweight document storage system with SQLAlchemy dialect support. Refer to the maintainer as **Bear** (never "the user"). Built with Python 3.12+ (3.14 is current), using modern type hints and Pydantic for validation.

## Core Architecture

### Three-Layer Design
1. **SQLAlchemy Dialect Layer** (`src/bear_shelf/dialect/`): Custom dialect translates SQL to storage operations
   - `BearShelfDialect`: Main dialect registered with SQLAlchemy
   - `sql_translator.py`: Converts WHERE clauses to `QueryInstance` objects
   - `executor.py`: Handles statement execution (SELECT, INSERT, UPDATE, DELETE)
   - DDL events (`before_create`, `before_drop`) trigger actual storage operations

2. **Datastore Layer** (`src/bear_shelf/datastore/`): Storage-agnostic database abstraction
   - `BearBase`: Main facade managing tables and storage backends
   - `Table`: CRUD operations on records with TinyDB-style querying
   - Storage backends: JSONL (default), JSON, TOML, YAML, XML, MessagePack, in-memory

3. **Type System Integration**: Leverages `funcy_bear` for advanced type introspection
   - `Columns[T]` uses Pydantic generics with `PrivateAttr` for type caching
   - `ParamWrapper` handles parameterized generics (e.g., `Columns[EpochTimestamp]`)
   - `_type_obj_cache` stores actual type objects to avoid string conversion issues

### Critical Patterns

#### Generic Type Handling
When `Columns[T]` is used with a custom type, the actual type object is cached in `_type_obj_cache`:
```python
# In model_post_init, cache type before converting to string
type_arg = next(iter(metadata["args"]))
self._type_obj_cache = type_arg  # Store actual type object
self.type = type_name(type_arg)   # String for serialization

# In type_obj property, return cached type if available
if self._type_obj_cache is not None:
    return self._type_obj_cache
return str_to_type(self.type)  # Fallback for string types
```

Use `ParamWrapper` to check if types are concrete before `isinstance()` checks:
```python
param = ParamWrapper(Parameter(name=col.name, annotation=col.type_obj))
check_type = col.type_obj if param.is_concrete else param.origin
```

#### SQLAlchemy URL Format
`bearshelf:///path/to/file.ext` - file extension determines storage backend. WAL files are auto-generated as `{table_name}.wal` in same directory unless `wal_dir` specified.

#### ORDER BY Implementation
`Records.order_by(*keys, desc=bool)` uses `sorted()` with `reverse=desc`. The sort key function handles None values specially (always last for asc, first for desc).

## Development Workflow

### Essential Commands
```bash
# Quality checks (run before commits)
nox -s ruff_fix      # Auto-fix linting/formatting
nox -s pyright       # Type checking (strict mode)
nox -s tests         # Run test suite (pytest with random order)

# Alternative: use mask tasks
mask lint            # Equivalent to nox -s ruff_check
mask test            # Equivalent to nox -s tests
mask check           # Run all checks

# CLI testing
bear-shelf version   # Get current version
bear-shelf debug_info # Show environment details
```

### Test Patterns
- Fixtures use `tmp_path` for temporary databases: `create_engine(f"bearshelf:///{tmp_path / 'test.jsonl'}")`
- Tests copy `sample_database.jsonl` to temp files to avoid mutating fixtures
- Use `Session(engine)` context managers for SQLAlchemy ORM tests
- WAL tests need `time.sleep(0.1)` for async thread completion

### Version Management
Git tags drive versioning (`v1.2.3` format). Dynamic versioning via `uv-dynamic-versioning`:
```bash
bear-shelf bump patch  # Auto-bumps, tags, and pushes
# Or manual: git tag v1.2.3 && git push origin v1.2.3
```

## Code Quality Standards

### Comment Philosophy
Comments answer **WHY** or **WATCH OUT**, never WHAT. Code should be self-documenting via clear naming. Only comment for:
- Library quirks/undocumented behavior
- Non-obvious business rules  
- Future warnings ("TODO: Fix before...")
- Explaining necessary weirdness

Before adding a comment, ask: "Could better naming make this unnecessary?"

### Type Hints
- Full type coverage required (pyright standard mode)
- Use modern syntax: `list[T]` not `List[T]`, `dict[K, V]` not `Dict[K, V]`
- Import from `collections.abc` for protocols: `Callable`, `Sequence`, `Mapping`
- Pydantic models use `Field()` for regular fields, `PrivateAttr()` for private (`_field`)

### Import Organization (ruff isort)
```python
from __future__ import annotations  # Always first

from typing import TYPE_CHECKING    # Second if needed

# Then: standard library, third-party, first-party, local
# Within sections: sorted alphabetically with combine-as-imports
```

## Testing & Debugging

### Common Test Failures
1. **WAL async timing**: Add `time.sleep(0.1)` after WAL operations
2. **ORDER BY DESC not working**: Ensure `reverse=desc` passed to `sorted()`
3. **Generic type isinstance errors**: Use `ParamWrapper.is_concrete` check first

### WAL (Write-Ahead Log) Gotchas
- Enable globally: `BearBase(file, enable_wal=True)` or per-table
- Operations with `checkpoint=False` log to WAL, `checkpoint=True` writes immediately
- Background threads need cleanup: `table.close()` or use context managers
- Recovery mode: `WALHelper(file=wal_path, auto_start=False).recover_from_wal(table)`

## Adding Storage Backends

All storage classes inherit from `Storage` base class and live in `src/bear_shelf/datastore/storage/`:
```python
class YourStorage(Storage):
    def read(self) -> UnifiedDataFormat | None: ...
    def write(self, data: UnifiedDataFormat) -> None: ...
    def close(self) -> None: ...
    @property
    def closed(self) -> bool: ...
```

**No manual registration needed** - the system auto-discovers Storage subclasses.

## Dependencies & Ecosystem

### Internal Dependencies (Bear-verse)
- `funcy_bear`: Type introspection (`ParamWrapper`, `TypeHelper`), query utilities
- `bear-epoch-time`: Timestamp handling (`EpochTimestamp`)
- `codec_cub`: Codec utilities

### Key External Libraries
- `sqlalchemy>=2.0`: ORM integration
- `pydantic>=2.12`: Data validation
- `tomlkit`, `pyyaml`, `msgpack`: Format support

## File Locations
- Config: `config/` (ruff.toml, pytest.ini, jsonl_db/*.toml)
- Tests: `tests/` with `conftest.py` setting `BEAR_SHELF_ENV=test`
- Generated version: `src/bear_shelf/_internal/_version.py` (git-based, auto-generated)
- Docs: `mkdocs.yml` + `docs/` using Material theme with mkdocstrings

## Quick Reference

**URL formats**: `bearshelf:///file.{jsonl,json,toml,yaml,xml}` or `bearshelf:///:memory:`  
**Environment var**: `BEAR_SHELF_ENV` (prod/test)  
**Dialect name**: `bearshelf` (registered in `project.entry-points."sqlalchemy.dialects"`)  
**Min Python**: 3.12 (3.14 is released and current)  
**License**: Not specified in project files
