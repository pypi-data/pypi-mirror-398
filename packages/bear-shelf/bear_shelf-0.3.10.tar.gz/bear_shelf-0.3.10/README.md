
# 🐻📚 Bear-Shelf

[![pypi version](https://img.shields.io/pypi/v/bear-shelf.svg)](https://pypi.org/project/bear-shelf/)

**The shelf where your data hibernates.** 🐻💤

A lightweight document storage system with SQLAlchemy dialect support. Store your data in JSONL, JSON, TOML, YAML, XML, MessagePack, or in-memory formats with a clean, type-safe interface.

## Features

- 🔌 **SQLAlchemy Integration**: Use familiar SQLAlchemy syntax with file-based storage
- 📦 **Multiple Backends**: JSONL (default), JSON, TOML, YAML, XML, MessagePack, or in-memory storage
- 🔒 **Type-Safe**: Full type hints and Pydantic models throughout
- 🚀 **Lightweight**: No heavy database engine required
- 📝 **Write-Ahead Logging**: Optional WAL support for data durability
- 🛠️ **CLI Tools**: Built-in command-line utilities for debugging and management

## Installation

With [`uv`](https://docs.astral.sh/uv/):

```bash
uv tool install bear-shelf
```

## Quick Start

```python
from sqlalchemy import create_engine, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

# Create engine with bearshelf dialect (file extension determines backend)
engine = create_engine("bearshelf:///path/to/users.jsonl")

class Base(DeclarativeBase): ...

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)

# Use it like any SQLAlchemy database!
Base.metadata.create_all(engine)

with Session(engine) as session:
    user = User(name="Bear", email="bear@shelf.com")
    session.add(user)
    session.commit()
```

## 🎯 Storage Backends

Bear Shelf auto-detects the storage backend from file extension:

- **JSONL** (default): `bearshelf:///path/to/data.jsonl`
- **JSON**: `bearshelf:///path/to/data.json`
- **TOML**: `bearshelf:///path/to/data.toml`
- **YAML**: `bearshelf:///path/to/data.yaml`
- **XML**: `bearshelf:///path/to/data.xml`
- **MessagePack**: `bearshelf:///path/to/data.msgpack`
- **Memory**: `bearshelf:///:memory:`

## 🐻 About

Built with ❤️ by Bear. Part of the Bear-verse ecosystem:
- `funcy_bear`: Lightweight functional programming and type introspection utility
- `bear-epoch-time`: Timestamp handling
- `codec_cub`: Codec utilities
