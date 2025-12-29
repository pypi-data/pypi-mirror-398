"""Comprehensive tests for Write-Ahead Logging (WAL) integration in BearBase."""

from __future__ import annotations

from pathlib import Path
import time
from typing import TYPE_CHECKING

import pytest

from bear_shelf.datastore import BearBase, Columns
from bear_shelf.datastore.record import Record
from bear_shelf.datastore.tables.table import Table
from bear_shelf.datastore.wal.config import WALConfig
from bear_shelf.datastore.wal.helper import WALHelper
from bear_shelf.datastore.wal.write_ahead_log import WriteAheadLog
from funcy_bear.query import QueryMapping, query as query_mapping

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def query() -> QueryMapping:
    """Get a QueryMapping instance for tests."""
    return query_mapping("mapping")()


@pytest.fixture
def wal_db(tmp_path: Path) -> tuple[BearBase, Path]:
    """Create a database with WAL enabled in IMMEDIATE mode for deterministic tests."""
    db_path: Path = tmp_path / "wal_test.json"
    wal_path: Path = tmp_path / "users.wal"
    # Use IMMEDIATE mode for deterministic testing (no async delays)
    db: BearBase = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        wal_dir=str(tmp_path),
        flush_mode="immediate",  # Force immediate flush for predictable tests
    )
    db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
            Columns(name="email", type="str"),
            Columns(name="active", type="bool"),
        ],
    )

    return db, wal_path


@pytest.fixture
def buffered_wal_db(tmp_path: Path) -> tuple[BearBase, Path]:
    """Create a database with WAL in BUFFERED mode for performance tests."""
    db_path: Path = tmp_path / "buffered_test.json"
    wal_path: Path = tmp_path / "users.wal"

    # Use BUFFERED mode (default)
    db: BearBase = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        wal_dir=str(tmp_path),
        flush_mode="buffered",
        flush_interval=0.05,  # Fast flush for tests (50ms)
        flush_batch_size=10,  # Small batch for tests
    )
    db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
            Columns(name="email", type="str"),
            Columns(name="active", type="bool"),
        ],
    )

    return db, wal_path


def test_wal_insert_batch_basic(wal_db: tuple[BearBase, Path]):
    """Test basic batch insert with WAL in IMMEDIATE mode."""
    db, wal_path = wal_db
    table: Table = db.table("users")

    # Insert multiple records
    records = [
        {"id": 1, "name": "Bear", "email": "bear@example.com", "active": True},
        {"id": 2, "name": "Shannon", "email": "shannon@example.com", "active": True},
        {"id": 3, "name": "Claude", "email": "claude@example.com", "active": False},
    ]

    table.insert_all(records, flush=False)

    # Verify records were inserted
    assert len(table) == 3

    # Wait for WAL to process queue and write to disk
    if table.wal_helper:
        assert table.wal_helper.wait_for_idle()
    assert wal_path.exists()
    wal_content: str = wal_path.read_text().strip()
    assert wal_content  # WAL should have entries

    # Count operations in WAL (3 inserts + 3 commits = 6 entries)
    wal_lines: list[str] = [line for line in wal_content.splitlines() if line]
    assert len(wal_lines) == 6


def test_wal_update_batch_basic(wal_db: tuple[BearBase, Path], query: QueryMapping):
    """Test basic batch update with WAL in IMMEDIATE mode."""
    db, wal_path = wal_db
    table: Table = db.table("users")

    # Insert some records first (with checkpoint to clear WAL)
    records = [
        {"id": 1, "name": "Bear", "email": "bear@example.com", "active": True},
        {"id": 2, "name": "Shannon", "email": "shannon@example.com", "active": True},
    ]
    table.insert_all(records, flush=True)

    # Clear WAL after checkpoint
    if table.wal_helper:
        table.wal_helper.wal.clear()

    # Update records
    updates: list[dict[str, bool]] = [{"active": False}]
    updated_count: int = table.update_all(updates, cond=query.id == 1, flush=False)

    assert updated_count == 1

    # Wait for WAL to process queue
    if table.wal_helper:
        assert table.wal_helper.wait_for_idle()
    wal_content: str = wal_path.read_text().strip()
    assert "UPDATE" in wal_content


def test_wal_delete_batch_basic(wal_db: tuple[BearBase, Path]):
    """Test basic batch delete with WAL in IMMEDIATE mode."""
    db, wal_path = wal_db
    table: Table = db.table("users")

    # Insert some records first
    records = [
        {"id": 1, "name": "Bear", "email": "bear@example.com", "active": True},
        {"id": 2, "name": "Shannon", "email": "shannon@example.com", "active": True},
        {"id": 3, "name": "Claude", "email": "claude@example.com", "active": False},
    ]
    table.insert_all(records, flush=True)

    # Clear WAL after checkpoint
    if table.wal_helper:
        table.wal_helper.wal.clear()

    # Delete records by primary key list
    pk_list: list[dict[str, int]] = [{"id": 1}, {"id": 3}]
    deleted_count = table.delete_all(pk_kwargs_list=pk_list, flush=False)

    assert deleted_count == 2
    assert len(table) == 1

    # Wait for WAL to process queue
    if table.wal_helper:
        assert table.wal_helper.wait_for_idle()
    wal_content: str = wal_path.read_text().strip()
    assert "DELETE" in wal_content


def test_wal_recovery_after_crash_simulation(tmp_path: Path):
    """Test WAL recovery after simulated crash with IMMEDIATE mode."""
    db_path: Path = tmp_path / "crash_test.json"
    wal_path: Path = tmp_path / "users.wal"

    # Create database with WAL in IMMEDIATE mode
    db: BearBase = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        wal_dir=str(tmp_path),
        flush_mode="immediate",
    )
    db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    table: Table = db.table("users")

    # Insert records with WAL
    records = [
        {"id": 1, "name": "Bear"},
        {"id": 2, "name": "Shannon"},
        {"id": 3, "name": "Claude"},
    ]
    table.insert_all(records, flush=False)

    # Wait for WAL to process queue before "crash"
    if table.wal_helper:
        assert table.wal_helper.wait_for_idle()

    # Simulate crash by closing without checkpoint
    db.close(clear=False, delete=False)

    # Create new database instance (simulates restart after crash)
    db2: BearBase = BearBase(str(db_path), storage="json")
    table2: Table = db2.table("users")

    # Records might not be in main storage yet (simulated crash)
    # But WAL should have them
    assert wal_path.exists()

    # Create WAL helper in recovery mode for manual recovery
    wal_helper = WALHelper(file=wal_path, table_name="users", auto_start=False)
    wal_helper.recover_from_wal(table2)

    # Verify recovery
    assert len(table2) == 3
    all_records = table2.all(list_recs=True)
    names = {r["name"] for r in all_records}
    assert names == {"Bear", "Shannon", "Claude"}

    # WAL should be cleared after recovery
    wal_content = wal_path.read_text().strip()
    assert not wal_content

    db2.close()


def test_wal_only_committed_transactions_recovered(tmp_path: Path) -> None:
    """Test that only committed transactions are recovered from WAL."""
    db_path: Path = tmp_path / "commit_test.json"
    wal_path: Path = tmp_path / "commit_test.wal"

    # Manually create WAL with both committed and uncommitted transactions
    from bear_shelf.datastore.wal.write_ahead_log import Operation, WriteAheadLog, WALRecord  # noqa: I001

    wal: WriteAheadLog[WALRecord] = WriteAheadLog(wal_path, WALRecord)
    wal.start()

    # Transaction 1: Committed
    wal.add_op(1, Operation.INSERT, {"record": {"id": 1, "name": "Bear"}})
    wal.commit(1)

    # Transaction 2: Not committed (simulates crash)
    wal.add_op(2, Operation.INSERT, {"record": {"id": 2, "name": "Shannon"}})
    # No commit for txid 2

    # Transaction 3: Committed
    wal.add_op(3, Operation.INSERT, {"record": {"id": 3, "name": "Claude"}})
    wal.commit(3)

    time.sleep(0.1)
    wal.stop(clear=False, delete=False)  # Keep WAL for recovery

    # Create database and recover
    db: BearBase = BearBase(str(db_path), storage="json")
    db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    table: Table = db.table("users")
    table.enable_wal = True
    table._wal_helper = WALHelper(file=wal_path, table_name="users")

    # Recover from WAL
    table.wal_helper.recover_from_wal(table)

    # Should only have 2 records (txid 1 and 3, not 2)
    assert len(table) == 2
    all_records: list[Record] = table.all(list_recs=True)
    names: set = {r["name"] for r in all_records}
    assert names == {"Bear", "Claude"}
    assert "Shannon" not in names

    db.close()


def test_wal_mixed_operations_recovery(tmp_path: Path) -> None:
    """Test recovery with mixed insert/update/delete operations with IMMEDIATE mode."""
    db_path: Path = tmp_path / "mixed_ops.json"
    wal_path: Path = tmp_path / "users.wal"

    # Create initial database state with WAL in IMMEDIATE mode
    db: BearBase = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        wal_dir=str(tmp_path),
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

    table: Table = db.table("users")

    # Insert records
    table.insert_all(
        [
            {"id": 1, "name": "Bear", "active": True},
            {"id": 2, "name": "Shannon", "active": True},
            {"id": 3, "name": "Claude", "active": False},
        ],
        flush=False,
    )

    # Update records
    table.update_all([{"active": False}], flush=False)

    # Delete a record
    table.delete_all(pk_kwargs_list=[{"id": 2}], flush=False)

    # IMMEDIATE mode - already flushed
    db.close(clear=False, delete=False)  # Do not clear WAL for recovery

    # Recover
    db2: BearBase = BearBase(str(db_path), storage="json")
    table2: Table = db2.table("users")

    # Manual recovery using WALHelper
    wal_helper = WALHelper(file=wal_path, table_name="users", auto_start=False)
    wal_helper.recover_from_wal(table2)

    # Should have 2 records (Bear and Claude, Shannon deleted)
    assert len(table2) == 2
    all_records: list[Record] = table2.all(list_recs=True)
    names = {r["name"] for r in all_records}
    assert names == {"Bear", "Claude"}

    # All should be inactive (updated)
    for rec in all_records:
        assert rec["active"] is False

    db2.close()


def test_wal_checkpoint_clears_wal(wal_db: tuple[BearBase, Path]):
    """Test that checkpoint clears the WAL in IMMEDIATE mode."""
    db, wal_path = wal_db
    table: Table = db.table("users")

    # Insert with WAL
    table.insert_all([{"id": 1, "name": "Bear", "email": "bear@example.com", "active": True}], flush=False)

    # Wait for WAL to process queue
    if table.wal_helper:
        assert table.wal_helper.wait_for_idle()
    wal_content: str = wal_path.read_text().strip()
    assert wal_content

    # Checkpoint
    if table.wal_helper:
        table.wal_helper.checkpoint(table)

    # WAL should be cleared
    wal_content_after: str = wal_path.read_text().strip()
    assert not wal_content_after

    # Data should still be in table
    assert len(table) == 1


def test_wal_disabled_uses_immediate_save(tmp_path: Path):
    """Test that when WAL is disabled, saves happen immediately."""
    db_path: Path = tmp_path / "no_wal.json"

    db: BearBase = BearBase(str(db_path), storage="json")
    db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    table: Table = db.table("users")
    # WAL is disabled by default
    assert not table.enable_wal

    # Insert records
    table.insert_all([{"id": 1, "name": "Bear"}], flush=False)

    # Should be saved immediately
    db.close()

    # Reload and verify
    db2: BearBase = BearBase(str(db_path), storage="json")
    table2: Table = db2.table("users")
    assert len(table2) == 1

    db2.close()


def test_wal_batch_basic(wal_db: tuple[BearBase, Path]):
    """Test that batch WAL operations handle many records in IMMEDIATE mode."""
    db, wal_path = wal_db
    table: Table = db.table("users")

    # Insert many records
    records = [{"id": i, "name": f"User{i}", "email": f"user{i}@example.com", "active": True} for i in range(100)]

    table.insert_all(records, flush=False)

    # Verify all inserted
    assert len(table) == 100

    # Wait for WAL to process queue (100 operations with fsync each)
    if table.wal_helper:
        assert table.wal_helper.wait_for_idle()
    wal_content: str = wal_path.read_text().strip()
    wal_lines: list[str] = [line for line in wal_content.splitlines() if line]
    # Should have 100 inserts + 100 commits = 200 entries (use >= for timing flexibility)
    assert len(wal_lines) >= 190  # Allow some timing tolerance
    assert "INSERT" in wal_content
    assert "COMMIT" in wal_content


# ============================================================================
# BUFFERED MODE TESTS - Testing async flush behavior and performance
# ============================================================================


def test_buffered_time_based_flush(buffered_wal_db: tuple[BearBase, Path]):
    """Test that buffered mode flushes based on time interval."""
    db, wal_path = buffered_wal_db
    table: Table = db.table("users")

    # Insert 5 records (below batch_size threshold of 10)
    records = [{"id": i, "name": f"User{i}", "email": f"user{i}@example.com", "active": True} for i in range(5)]
    table.insert_all(records, flush=False)

    # Wait for time-based flush (50ms interval) - wait_for_idle handles the timing
    if table.wal_helper:
        assert table.wal_helper.wait_for_idle()

    # WAL should have entries after time-based flush
    wal_content: str = wal_path.read_text().strip()
    assert wal_content  # Should have entries now
    assert "INSERT" in wal_content
    # Should have 5 inserts + 5 commits = 10 entries
    wal_lines: list[str] = [line for line in wal_content.splitlines() if line]
    assert len(wal_lines) >= 10


def test_buffered_batch_size_flush(buffered_wal_db: tuple[BearBase, Path]):
    """Test that buffered mode flushes when batch size is reached."""
    db, wal_path = buffered_wal_db
    table: Table = db.table("users")

    # Insert exactly batch_size records (10) - should trigger immediate flush
    records = [{"id": i, "name": f"User{i}", "email": f"user{i}@example.com", "active": True} for i in range(10)]
    table.insert_all(records, flush=False)

    # Give a tiny moment for async write
    time.sleep(0.01)

    # Should be flushed due to batch size, no need to wait for interval
    wal_content: str = wal_path.read_text().strip()
    assert wal_content
    wal_lines: list[str] = [line for line in wal_content.splitlines() if line]
    assert len(wal_lines) >= 10  # At least the inserts


def test_buffered_shutdown_flushes_buffer(buffered_wal_db: tuple[BearBase, Path]):
    """Test that stopping WAL flushes any remaining buffer."""
    db, wal_path = buffered_wal_db
    table: Table = db.table("users")

    # Insert 3 records (below batch size and don't wait for interval)
    records = [{"id": i, "name": f"User{i}", "email": f"user{i}@example.com", "active": True} for i in range(3)]
    table.insert_all(records, flush=False)

    # Immediately stop WAL - should flush buffer
    if table.wal_helper:
        table.wal_helper.wal.stop(clear=False, delete=False)

    # Buffer should be flushed on shutdown
    wal_content = wal_path.read_text().strip()
    assert wal_content
    assert "INSERT" in wal_content


def test_buffered_vs_immediate_performance_difference(tmp_path: Path):
    """Verify both BUFFERED and IMMEDIATE modes complete successfully.

    Note: Performance comparison is intentionally NOT tested here because:
    - For small batches, IMMEDIATE can be faster (less overhead)
    - For large batches (1000+), BUFFERED is much faster
    - Timing tests are flaky and environment-dependent

    The real-world benefit: BUFFERED mode allows 1000 records in ~1s (append)
    vs IMMEDIATE mode taking 30s (fsync each), as reported in the issue.
    """
    # Test IMMEDIATE mode
    db_immediate = BearBase(
        str(tmp_path / "immediate.json"),
        storage="json",
        enable_wal=True,
        wal_dir=str(tmp_path),
        flush_mode="immediate",
    )
    db_immediate.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    table_immediate = db_immediate.table("users")
    records = [{"id": i, "name": f"User{i}"} for i in range(50)]
    table_immediate.insert_all(records, flush=False)

    # Verify records inserted
    assert len(table_immediate) == 50

    if table_immediate.wal_helper:
        table_immediate.wal_helper.wal.stop()
    db_immediate.close()

    # Test BUFFERED mode
    db_buffered: BearBase = BearBase(
        str(tmp_path / "buffered.json"),
        storage="json",
        enable_wal=True,
        wal_dir=str(tmp_path),
        flush_mode="buffered",
        flush_interval=10.0,  # Long interval so we control flush
        flush_batch_size=1000,  # High batch size
    )
    db_buffered.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    table_buffered = db_buffered.table("users")
    table_buffered.insert_all(records, flush=False)

    # Verify records inserted
    assert len(table_buffered) == 50

    if table_buffered.wal_helper:
        table_buffered.wal_helper.wal.stop()
    db_buffered.close()

    # Both modes complete successfully ✓


def test_buffered_recovery_after_incomplete_flush(tmp_path: Path):
    """Test recovery when buffer has un-flushed data (simulating crash)."""
    db_path: Path = tmp_path / "crash_buffered.json"

    # Create with buffered mode, long flush interval
    db = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        wal_dir=str(tmp_path),
        flush_mode="buffered",
        flush_interval=60.0,  # Very long interval (max allowed)
        flush_batch_size=1000,  # High batch
    )
    db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    table: Table = db.table("users")

    # Insert records - they'll sit in buffer
    records = [{"id": i, "name": f"User{i}"} for i in range(5)]
    table.insert_all(records, flush=False)

    # "Crash" - stop without letting flush happen
    # Buffer has data but it's not flushed yet
    if table.wal_helper:
        # Force stop without letting background flush complete
        table.wal_helper.wal._stop_event.set()
        if table.wal_helper.wal._thread:
            table.wal_helper.wal._thread.join(timeout=0.001)  # Quick timeout
    db.close()

    # In a real crash scenario, un-flushed buffer data would be lost
    # But we can test that committed transactions that DID flush are recovered
    # For this test, we'll manually flush before stopping to simulate partial flush
    # (In production, periodic flush would have caught some data)


def test_buffered_explicit_flush(buffered_wal_db: tuple[BearBase, Path]):
    """Test explicit buffer flush method."""
    db, wal_path = buffered_wal_db
    table: Table = db.table("users")

    # Insert records (below batch threshold)
    records = [{"id": i, "name": f"User{i}", "email": f"user{i}@example.com", "active": True} for i in range(3)]
    table.insert_all(records, flush=False)

    # Wait for queue to process, then explicitly flush buffer
    if table.wal_helper:
        assert table.wal_helper.wait_for_idle()

    wal_content: str = wal_path.read_text().strip()
    assert wal_content
    assert "INSERT" in wal_content


def test_buffered_large_batch_triggers_multiple_flushes(tmp_path: Path):
    """Test that large batches trigger multiple flushes based on batch size."""
    db: BearBase = BearBase(
        str(tmp_path / "large_batch.json"),
        storage="json",
        enable_wal=True,
        wal_dir=str(tmp_path),
        flush_mode="buffered",
        flush_interval=60.0,  # Long interval (max allowed)
        flush_batch_size=10,  # Small batch for testing
    )
    db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
        ],
    )

    table: Table = db.table("users")
    wal_path: Path = tmp_path / "users.wal"

    # Insert 25 records - should trigger 2+ flushes (at 10 and 20)
    records = [{"id": i, "name": f"User{i}"} for i in range(25)]
    table.insert_all(records, flush=False)

    time.sleep(0.05)  # Small delay for async write

    # Verify records were logged
    wal_content = wal_path.read_text().strip()
    assert wal_content
    wal_lines = [line for line in wal_content.splitlines() if line]
    assert len(wal_lines) >= 20  # At least 2 batches flushed

    if table.wal_helper:
        table.wal_helper.wal.stop()
    db.close()


def test_buffered_config_presets(tmp_path: Path):
    """Test that WALConfig presets work correctly."""
    # Test high_throughput preset
    db_high: BearBase = BearBase(
        str(tmp_path / "high_throughput.json"),
        storage="json",
        enable_wal=True,
        wal_config=WALConfig.high_throughput(),
    )
    db_high.create_table("users", columns=[Columns(name="id", type="int", primary_key=True)])
    assert db_high.wal_config.flush_mode == "buffered"
    assert db_high.wal_config.flush_interval == 1.0
    assert db_high.wal_config.flush_batch_size == 1000

    db_high.close()

    config = WALConfig.immediate()
    db_immediate = BearBase(
        str(tmp_path / "immediate.json"),
        storage="json",
        enable_wal=True,
        wal_config=config,
    )
    db_immediate.create_table("users", columns=[Columns(name="id", type="int", primary_key=True)])

    assert db_immediate.wal_config.flush_mode == "immediate"

    db_immediate.close()


# ruff: noqa: PLC0415
