"""Real-world WAL usage test - User management system simulation."""

from __future__ import annotations

from pathlib import Path
import time
from typing import TYPE_CHECKING

from bear_shelf.datastore import Columns
from bear_shelf.datastore.database import JSONBase
from bear_shelf.datastore.record import NullRecords, Record, Records
from bear_shelf.datastore.tables.table import Table
from funcy_bear.query import where_map

if TYPE_CHECKING:
    from pathlib import Path


def test_wal_user_management_simulation(tmp_path: Path) -> None:
    """Simulate a realistic user management system with WAL crash recovery.

    This test demonstrates WAL in action with:
    - Buffered writes with batching
    - Multiple inserts, updates, and deletes
    - Crash simulation and recovery
    - Data integrity verification after recovery
    """
    db_path: Path = tmp_path / "users.json"
    wal_dir: Path = tmp_path

    # Phase 1: Create database and perform operations
    db = JSONBase(
        file=db_path,
        enable_wal=True,
        wal_dir=str(wal_dir),
        flush_mode="buffered",
        flush_batch_size=5,
        flush_interval=2.0,
    )

    db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="username", type="str"),
            Columns(name="email", type="str"),
            Columns(name="created_at", type="float"),
            Columns(name="active", type="bool"),
        ],
    )

    users: Table = db.table("users")

    # Insert 7 users
    for i in range(1, 8):
        users.insert(
            {
                "id": i,
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "created_at": time.time(),
                "active": True,
            }
        )

    assert len(users) == 7

    # Wait for WAL flush
    users.wal_helper.wait_for_idle()

    # Query active users
    active_users: Records = users.search(where_map("active") == True)  # noqa: E712
    assert len(active_users) == 7

    # Find specific user
    user3: Records = users.get(id=3)
    assert user3.first()["username"] == "user3"

    # Update operations
    users.update({"active": False}, where_map("id") == 2)
    users.update({"email": "newemail@example.com"}, where_map("id") == 5)

    # Delete operation
    users.delete(where_map("id") == 7)

    # Wait for final flush
    users.wal_helper.wait_for_idle()

    assert len(users) == 6

    # Verify pre-recovery state
    user2_before: Record = users.get(id=2).first()
    assert user2_before["active"] is False

    user5_before: Record = users.get(id=5).first()
    assert user5_before["email"] == "newemail@example.com"

    db.close(clear=False, delete=False)  # pyright: ignore[reportCallIssue] # Do not clear WAL for recovery

    # Phase 2: Simulate crash and recovery
    db2 = JSONBase(  # type: ignore[call-arg]
        file=db_path,  # type: ignore[arg-type]
        enable_wal=True,  # type: ignore[call-arg]
        wal_dir=str(wal_dir),  # type: ignore[call-arg]
        flush_mode="buffered",  # type: ignore[call-arg]
        flush_batch_size=5,  # type: ignore[call-arg]
        flush_interval=2.0,  # type: ignore[call-arg]
    )

    users2: Table = db2.table("users")
    users2.wal_helper.recover_from_wal(users2)

    # Verify data integrity after recovery
    assert len(users2) == 6

    # Check user2 deactivation persisted
    user2_after: Record = users2.get(id=2).first()
    assert user2_after["active"] is False
    assert user2_after["email"] == "user2@example.com"

    # Check user5 email update persisted
    user5_after: Record = users2.get(id=5).first()
    assert user5_after["email"] == "newemail@example.com"
    assert user5_after["active"] is True

    # Check user7 deletion persisted
    user7_after: Records = users2.get(id=7, default=NullRecords)
    assert user7_after is NullRecords

    # Check unmodified users remain intact
    user1_after: Record = users2.get(id=1).first()
    assert user1_after["email"] == "user1@example.com"
    assert user1_after["active"] is True

    user3_after: Record = users2.get(id=3).first()
    assert user3_after["email"] == "user3@example.com"
    assert user3_after["active"] is True

    db2.close()
