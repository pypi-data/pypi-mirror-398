"""Test WAL recovery idempotence to catch infinite WAL growth bugs.

The critical test: recovering multiple times should not cause WAL to grow.
This catches bugs where recovery operations are re-logged to the WAL.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from bear_shelf.datastore import BearBase, Columns
from bear_shelf.datastore.record import Record
from bear_shelf.datastore.storage.jsonl import JSONLStorage
from bear_shelf.datastore.tables.table import Table
from funcy_bear.query import where_map

if TYPE_CHECKING:
    from pathlib import Path


def test_wal_recovery_idempotence_prevents_infinite_growth(tmp_path: Path):
    """Test that recovering from WAL multiple times doesn't cause infinite WAL growth.

    This is the critical test that catches bugs where recovery operations
    are re-logged to the WAL instead of being flushed directly to disk.

    Bug scenario:
    1. Perform operations (insert, update, delete) -> logged to WAL
    2. Recover from WAL
    3. If recovery doesn't use flush=True, operations get re-logged!
    4. Recover again -> WAL grows infinitely

    This test ensures recovery is idempotent.
    """
    db_path: Path = tmp_path / "test.json"
    wal_dir: Path = tmp_path
    wal_file: Path = wal_dir / "users.wal"

    # Phase 1: Create database and perform operations
    db: BearBase[JSONLStorage] = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        wal_dir=str(wal_dir),
        flush_mode="immediate",
    )

    db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
            Columns(name="active", type="bool"),
        ],
    )

    users: Table = db.table("users")

    # Perform operations
    users.insert_all(
        [
            {"id": 1, "name": "user1", "active": True},
            {"id": 2, "name": "user2", "active": True},
            {"id": 3, "name": "user3", "active": True},
        ],
        flush=False,
    )

    users.update({"active": False}, where_map("id") == 2)
    users.delete(where_map("id") == 3)

    # Wait for WAL flush
    users.wal_helper.wait_for_idle()

    # Get initial WAL size
    initial_wal_size: int = wal_file.stat().st_size if wal_file.exists() else 0
    assert initial_wal_size > 0, "WAL should have content after operations"

    db.close(clear=False, delete=False)  # Do not clear WAL for recovery

    # Phase 2: First recovery
    db2: BearBase[JSONLStorage] = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        wal_dir=str(wal_dir),
        flush_mode="immediate",
    )

    users2: Table = db2.table("users")
    users2.wal_helper.recover_from_wal(users2)

    # WAL should be cleared after recovery
    wal_size_after_first_recovery: int = wal_file.stat().st_size if wal_file.exists() else 0

    # Verify data is correct
    assert len(users2) == 2
    user1 = users2.get(id=1).first()
    assert user1["active"] is True

    user2 = users2.get(id=2).first()
    assert user2["active"] is False

    db2.close()

    # Phase 3: Second recovery (the critical test!)
    db3: BearBase[JSONLStorage] = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        wal_dir=str(wal_dir),
        flush_mode="immediate",
    )

    users3: Table = db3.table("users")
    users3.wal_helper.recover_from_wal(users3)

    # WAL should still be empty/cleared - NOT GROWING!
    wal_size_after_second_recovery: int = wal_file.stat().st_size if wal_file.exists() else 0

    # This is the critical assertion that catches the infinite growth bug
    assert wal_size_after_second_recovery == wal_size_after_first_recovery, (
        f"WAL grew during second recovery! "
        f"First: {wal_size_after_first_recovery}, "
        f"Second: {wal_size_after_second_recovery}. "
        f"This means recovery operations are being re-logged instead of using flush=True!"
    )

    # Data should still be correct
    assert len(users3) == 2
    user1: Record = users3.get(id=1).first()
    assert user1["active"] is True

    user2: Record = users3.get(id=2).first()
    assert user2["active"] is False

    db3.close()


def test_wal_recovery_with_updates_doesnt_relog(tmp_path: Path):
    """Specific test for UPDATE operations during recovery.

    UPDATE is the most likely to have the re-logging bug because
    it's easy to forget to add flush=True to the update() call.
    """
    db_path: Path = tmp_path / "test.json"
    wal_dir: Path = tmp_path
    wal_file: Path = wal_dir / "data.wal"

    db: BearBase[JSONLStorage] = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        wal_dir=str(wal_dir),
        flush_mode="immediate",
    )

    db.create_table(
        "data",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="value", type="int"),
        ],
    )

    table: Table = db.table("data")

    # Insert and update
    table.insert_all(
        [
            {"id": 1, "value": 10},
            {"id": 2, "value": 20},
        ],
        flush=False,
    )

    table.update({"value": 15}, where_map("id") == 1)
    table.update({"value": 25}, where_map("id") == 2)

    table.wal_helper.wait_for_idle()

    # Count operations in WAL before recovery
    wal_content_before: str = wal_file.read_text() if wal_file.exists() else ""
    operations_before: int = len([line for line in wal_content_before.splitlines() if "UPDATE" in line])

    db.close(clear=False, delete=False)  # Do not clear WAL for recovery

    # First recovery
    db2: BearBase[JSONLStorage] = BearBase(
        str(db_path), storage="json", enable_wal=True, wal_dir=str(wal_dir), flush_mode="immediate"
    )
    table2: Table = db2.table("data")
    table2.wal_helper.recover_from_wal(table2)

    # Verify updates worked
    assert table2.get(id=1).first()["value"] == 15
    assert table2.get(id=2).first()["value"] == 25

    db2.close()

    # Check WAL after recovery - should be cleared, not grown
    wal_content_after: str = wal_file.read_text() if wal_file.exists() else ""
    operations_after: int = len([line for line in wal_content_after.splitlines() if "UPDATE" in line])

    # If operations_after > operations_before, we have the bug!
    assert operations_after == 0, (
        f"UPDATE operations were re-logged during recovery! "
        f"Before: {operations_before}, After: {operations_after}. "
        f"The update() method must use flush=True during recovery."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
