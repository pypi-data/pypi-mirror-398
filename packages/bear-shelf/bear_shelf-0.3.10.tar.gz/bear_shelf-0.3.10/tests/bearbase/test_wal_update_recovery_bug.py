"""Test to reproduce and verify fix for WAL update recovery bug.

The issue: During recovery, updates appear to be applied to all records
instead of just the targeted record(s).
"""

from pathlib import Path

import pytest

from bear_shelf.datastore import BearBase, Columns
from bear_shelf.datastore.record import Record
from bear_shelf.datastore.storage.jsonl import JSONLStorage
from bear_shelf.datastore.tables.table import Table
from funcy_bear.query import where_map


def test_wal_update_recovery_single_record(tmp_path: Path):
    """Test that update during recovery only affects the targeted record.

    This reproduces the bug where all users end up with the same email
    and active status after recovery.
    """
    db_path: Path = tmp_path / "update_bug.json"
    wal_dir: Path = tmp_path

    # Phase 1: Create database and perform operations
    db1: BearBase = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        wal_dir=str(wal_dir),
        flush_mode="immediate",
    )

    db1.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="username", type="str"),
            Columns(name="email", type="str"),
            Columns(name="active", type="bool"),
        ],
    )

    users: Table = db1.table("users")

    # Insert 5 distinct users
    users.insert_all(
        [
            {"id": 1, "username": "user1", "email": "user1@example.com", "active": True},
            {"id": 2, "username": "user2", "email": "user2@example.com", "active": True},
            {"id": 3, "username": "user3", "email": "user3@example.com", "active": True},
            {"id": 4, "username": "user4", "email": "user4@example.com", "active": True},
            {"id": 5, "username": "user5", "email": "user5@example.com", "active": True},
        ],
        flush=False,
    )

    # Update ONLY user2's active status
    users.update({"active": False}, where_map("id") == 2)

    # Update ONLY user4's email
    users.update({"email": "newemail@example.com"}, where_map("id") == 4)

    # Wait for WAL flush
    if users.wal_helper:
        users.wal_helper.wait_for_idle()

    # Verify pre-recovery state
    assert len(users) == 5
    user1: Record = users.get(id=1).first()
    user2: Record = users.get(id=2).first()
    user3: Record = users.get(id=3).first()
    user4: Record = users.get(id=4).first()
    user5: Record = users.get(id=5).first()

    assert user1["email"] == "user1@example.com"
    assert user1["active"] is True

    assert user2["email"] == "user2@example.com"
    assert user2["active"] is False  # This was updated

    assert user3["email"] == "user3@example.com"
    assert user3["active"] is True

    assert user4["email"] == "newemail@example.com"  # This was updated
    assert user4["active"] is True

    assert user5["email"] == "user5@example.com"
    assert user5["active"] is True

    db1.close(clear=False, delete=False)  # Do not clear WAL for recovery

    # Phase 2: Reopen and recover
    db2: BearBase[JSONLStorage] = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        wal_dir=str(wal_dir),
        flush_mode="immediate",
    )

    users2 = db2.table("users")

    # Perform recovery
    users2.wal_helper.recover_from_wal(users2)

    # Verify post-recovery state - should match pre-recovery
    assert len(users2) == 5

    # Get all users for debugging
    all_users = users2.all(list_recs=True)

    # Check each user individually
    user1_recovered = users2.get(id=1).first()
    user2_recovered = users2.get(id=2).first()
    user3_recovered = users2.get(id=3).first()
    user4_recovered = users2.get(id=4).first()
    user5_recovered = users2.get(id=5).first()

    # These should NOT have been modified
    assert user1_recovered["email"] == "user1@example.com", f"user1 email wrong: {user1_recovered}"
    assert user1_recovered["active"] is True, f"user1 active wrong: {user1_recovered}"

    # user2 should have active=False
    assert user2_recovered["email"] == "user2@example.com", f"user2 email wrong: {user2_recovered}"
    assert user2_recovered["active"] is False, f"user2 active should be False: {user2_recovered}"

    # user3 should be unchanged
    assert user3_recovered["email"] == "user3@example.com", f"user3 email wrong: {user3_recovered}"
    assert user3_recovered["active"] is True, f"user3 active wrong: {user3_recovered}"

    # user4 should have updated email
    assert user4_recovered["email"] == "newemail@example.com", f"user4 email should be updated: {user4_recovered}"
    assert user4_recovered["active"] is True, f"user4 active wrong: {user4_recovered}"

    # user5 should be unchanged
    assert user5_recovered["email"] == "user5@example.com", f"user5 email wrong: {user5_recovered}"
    assert user5_recovered["active"] is True, f"user5 active wrong: {user5_recovered}"

    db2.close()


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
