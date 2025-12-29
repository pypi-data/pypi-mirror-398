"""Configuration for the pytest test suite."""

from collections.abc import Generator
from os import environ
from pathlib import Path
from typing import Any

import pytest

from bear_shelf import METADATA

environ[f"{METADATA.env_variable}"] = "test"

environ["BEAR_SHELF_DEBUG"] = "false"


def jsonl_data() -> str:
    return """{"$type":"header","data":{"tables":["categories","posts","users"],"version":"0.1.0"}}
{"$type":"schema","table":"categories","columns":[{"name":"description","type":"str","nullable":true},{"name":"id","type":"int","nullable":false,"primary_key":true},{"name":"name","type":"str","nullable":false}],"count":2}
{"$type":"record","table":"categories","data":{"id":1,"name":"Technology","description":"All things tech and programming"}}
{"$type":"record","table":"categories","data":{"id":2,"name":"Personal","description":null}}
{"$type":"schema","table":"posts","columns":[{"name":"author_id","type":"int","nullable":false},{"name":"content","type":"str","nullable":true},{"name":"id","type":"int","nullable":false,"primary_key":true},{"name":"published","type":"bool","nullable":true},{"name":"title","type":"str","nullable":false}],"count":3}
{"$type":"record","table":"posts","data":{"id":1,"title":"Hello JSONL Database!","content":"This is our first post in the new JSONL database system.","author_id":1,"published":true}}
{"$type":"record","table":"posts","data":{"id":2,"title":"SQLAlchemy Integration","content":"How we integrated SQLAlchemy with JSONL storage.","author_id":1,"published":true}}
{"$type":"record","table":"posts","data":{"id":3,"title":"Draft Post","content":"This is still a work in progress...","author_id":2,"published":false}}
{"$type":"schema","table":"users","columns":[{"name":"age","type":"int","nullable":true},{"name":"email","type":"str","nullable":false},{"name":"id","type":"int","nullable":false,"primary_key":true},{"name":"is_active","type":"bool","nullable":true},{"name":"name","type":"str","nullable":false}],"count":3}
{"$type":"record","table":"users","data":{"id":1,"name":"Bear","email":"bear@example.com","age":30,"is_active":true}}
{"$type":"record","table":"users","data":{"id":2,"name":"Claire","email":"claire@example.com","age":21,"is_active":true}}
{"$type":"record","table":"users","data":{"id":3,"name":"Shannon","email":"shannon@example.com","age":null,"is_active":false}}
"""


@pytest.fixture(scope="session", autouse=True)
def protect_sample_database() -> Generator[None, Any]:
    sample_db = Path("sample_database.jsonl")
    if sample_db.exists():
        sample_db.unlink()
    sample_db.write_text(jsonl_data())
    try:
        yield
    finally:
        if sample_db.exists():
            sample_db.unlink()


@pytest.fixture
def bearshelf_path(tmp_path: Path) -> Generator[str, Any]:
    """Provide a temporary path for a JSONL database file."""
    path: Path = tmp_path / "test_database.jsonl"
    try:
        yield f"bearshelf:///{path}"
    finally:
        if path.exists():
            path.unlink()
