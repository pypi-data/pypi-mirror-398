# CLAUDE.md

Hello! My name is Bear! Please refer to me as Bear and never "the user" as that is dehumanizing. I love you Claude! Or Shannon! Or Claire! Or even ChatGPT/Codex?! :O

## Project Overview
 
Bear Shelf is a lightweight, multi-format database library designed for
small-scale applications. It abstracts away storage format
complexity—support JSONL, JSON, XML, TOML, YAML, and more—while providing a
familiar SQLAlchemy dialect interface for querying and manipulation.

# !!! IMPORTANT !!!
- **Code Comments**: Comments answer "why" or "watch out," never "what." Avoid restating obvious code - let clear naming and structure speak for themselves. Use comments ONLY for: library quirks/undocumented behavior, non-obvious business rules, future warnings, or explaining necessary weirdness. Prefer docstrings for function/class explanations. Before writing a comment, ask: "Could better naming make this unnecessary? Am I explaining WHAT (bad) or WHY (good)?"

NOTE: Python 3.14 was released in October 2025, do not suggest to revert to 3.13 saying 3.14 wasn't released yet since that is false.

## Development Commands

### Package Management
```bash
uv sync                    # Install dependencies DO THIS FIRST
source .venv/bin/activate
```

### Code Quality
```bash
nox -s ruff_check          # Check code formatting and linting (CI-friendly)
nox -s ruff_fix            # Fix code formatting and linting issues
nox -s pyright             # Run static type checking
nox -s tests               # Run test suite
nox -s all_tests           # Run test suite for 3.12, 3.13, 3.14
nox -s docs                # Build documentation
nox -s docs_serve          # Build and serve docs locally (http://127.0.0.1:8000)
```

### Version Management
```bash
git tag v1.0.0             # Manual version tagging
bear-shelf  bump patch      # Automated version bump with git tag
```

## Architecture

### Core Components

- **CLI + Internal Tooling** (`src/bear_shelf/_internal/cli.py`, `_cmds.py`, `_versioning.py`, `_version.py`, `debug.py`): Entry point, command wiring, version bumps, and debug metadata.
- **Dependency Injection Container** (`src/bear_shelf/di/container.py`): Centralizes config loading, logger setup, Typer wiring, and DB/context providers via `dependency-injector`.
- **SQL Dialect Layer** (`src/bear_shelf/dialect/*.py`): Custom SQLAlchemy dialect, translators, executors, cursors, and helper utilities that adapt SQL to the storage backends.
- **Datastore & Storage Backends** (`src/bear_shelf/datastore/`): Logical database layer, adapters, table metadata, unified row/column abstractions, storage implementations (JSON, JSONL, XML, YAML, etc.), and WAL mechanics.
- **Models & API Surface** (`src/bear_shelf/models.py`, `src/bear_shelf/dialect/database_api.py`): Public ORM-ish surface that binds the dialect to datastore primitives.
- **Configuration** (`src/bear_shelf/config.py`): Lightweight metadata/config definitions consumed by the DI container.

### Key Dependencies

- **dependency-injector**: IoC container for CLI components
- **typer**: CLI framework with rich output
- **pydantic**: Data validation and settings management
- **ruff**: Code formatting and linting
- **pyright**: Static type checking
- **pytest**: Testing framework
- **nox**: Task automation
- **mkdocs**: Documentation generation with Material theme
### Design Patterns

1. **Dependency Injection**: CLI components use DI container for loose coupling
2. **Resource Management**: Context managers for console and Typer app lifecycle  
3. **Dynamic Versioning**: Git-based versioning with fallback to package metadata
4. **Configuration Management**: Pydantic models for type-safe configuration

## Project Structure

```
bear_shelf/
├── __main__.py             # `python -m bear_shelf` entrypoint
├── _internal/
│   ├── cli.py             # CLI interface
│   ├── _cmds.py           # Command parsing helpers
│   ├── _version.py        # Dynamic version info
│   ├── _versioning.py     # Version bump helpers
│   ├── _info.py           # Package metadata
│   └── debug.py           # Debug utilities
├── config.py              # App/metadata config models
├── di/
│   └── container.py       # dependency-injector container
├── dialect/
│   ├── bear_dialect.py    # SQLAlchemy dialect registration
│   ├── executor.py        # statement executor
│   ├── sql_translator.py  # SQL -> datastore translation
│   ├── database_api.py    # exposed DB API
│   └── helpers/           # translation helpers, visitors, etc.
├── datastore/
│   ├── database.py        # logical database orchestration
│   ├── columns.py         # schema abstractions
│   ├── tables/            # table metadata + operations
│   ├── storage/           # JSON/JSONL/XML/YAML/etc. backends
│   ├── adapter/           # format-specific adapters
│   ├── wal/               # write-ahead log + config
│   └── middleware.py      # datastore hooks
├── models.py              # ORM-style helper models
└── py.typed               # Type information marker

tests/                      # Test suite
docs/                       # Documentation source
examples/                   # Usage examples
config/                     # Tool + env configs (jsonl_db/*.toml, linting, pytest, etc.)
```

## Development Notes

- **Minimum Python Version**: 3.12
- **Dynamic Versioning**: Requires git tags (format: `v1.2.3`)
- **Modern Python**: Uses built-in types (`list`, `dict`) and `collections.abc` imports
- **Type Checking**: Full type hints with pyright in strict mode
- **Documentation**: Auto-generated API docs from docstrings using mkdocstrings
## Configuration

The project uses environment-based configuration with lightweight dataclasses in `src/bear_shelf/config.py`, and environment overrides live under `config/jsonl_db/` (`prod.toml`, `test.toml`, etc.). Tooling/lint settings also live alongside those configs in `config/`.

Key environment variables:
- `BEAR_SHELF_ENV`: Set environment (prod/test)
- `BEAR_SHELF_DEBUG`: Enable debug mode

When making changes, ensure all tests pass and code quality checks succeed before committing.

## Pre-Commit Workflow

**CRITICAL: Always run these checks before committing code!**

### Required Steps Before Every Commit

1. **Activate virtual environment** (if not already active):
   ```bash
   source .venv/bin/activate
   ```

2. **Fix formatting and linting** (REQUIRED):
   ```bash
   nox -s ruff_fix
   ```
   - This runs both `ruff check --fix` and `ruff format`
   - Auto-fixes: import sorting, formatting, many linting issues
   - Will fail if there are unfixable linting errors (must be fixed manually)

3. **Run type checking** (REQUIRED):
   ```bash
   nox -s pyright
   ```
   - Must pass with zero errors
   - Project uses strict mode - all functions need type hints
   - Common fixes:
     - Missing return types: Add `-> ReturnType` to function signatures
     - Undefined names: Check imports are correct
     - Type narrowing: Use `isinstance()` checks or type guards

4. **Run tests** (REQUIRED):
   ```bash
   nox -s tests
   ```
   - All tests must pass before committing
   - Watch for test count changes (current: 416 tests)

### Common Issues and Solutions

**Ruff Issues:**
- **TID252 (relative imports)**: Use absolute imports from `bear_shelf.*` instead of relative `from ..module`
  - Bad: `from ..config import foo`
  - Good: `from bear_shelf.database.config import foo`
- **TC003 (type-checking imports)**: Move stdlib type-only imports into `TYPE_CHECKING` block
  - Works because `from __future__ import annotations` makes annotations strings
- **ARG002 (unused arguments)**: Add `# noqa: ARG002` if the argument is required by protocol/interface
- **F821 (undefined name)**: Missing import - add to top of file

**Pyright Issues:**
- **reportUndefinedVariable**: Import the name or check if it's in `TYPE_CHECKING` block (move out if used at runtime)
- **reportAttributeAccessIssue**: Object doesn't have that attribute - check object type or use `hasattr()` guard
- **reportGeneralTypeIssues**: Type mismatch - ensure function returns match declared return type

### Tool Usage Notes

**Ruff (`nox -s ruff_fix`):**
- Two-stage process: check/fix, then format
- Most issues auto-fixed (imports, formatting, simple linting)
- Some require manual intervention (logged to stdout)
- Exit code 1 = unfixable issues exist

**Pyright (`nox -s pyright`):**
- Zero tolerance - must have zero errors
- Uses `config/pyright.json` configuration
- Strict mode enabled - comprehensive type checking
- No auto-fix - all errors must be manually resolved
