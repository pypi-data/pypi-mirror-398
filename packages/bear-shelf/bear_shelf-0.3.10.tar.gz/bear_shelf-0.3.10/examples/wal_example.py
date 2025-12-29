"""WAL (Write-Ahead Logging) Usage Examples.

This module demonstrates practical WAL usage patterns for BearBase,
showing how to achieve high-throughput bulk operations while maintaining
crash safety.

The Problem WAL Solves:
-----------------------
Without WAL, BearBase writes the entire database atomically on each insert.
For 1000 records, this can take ~30 seconds due to repeated full-file writes.

With WAL in BUFFERED mode:
- Inserts append to WAL file (~1 second for 1000 records)
- Background thread periodically checkpoints to main DB
- Crash recovery replays committed WAL operations

Performance Comparison:
-----------------------
Without WAL (1000 records):  ~30 seconds
With WAL BUFFERED mode:      ~1 second
With WAL IMMEDIATE mode:     ~5 seconds (fsync each operation)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from bear_shelf.datastore import BearBase, Columns
from bear_shelf.datastore.wal.config import WALConfig

if TYPE_CHECKING:
    from bear_shelf.datastore.storage.jsonl import JSONLStorage
    from bear_shelf.datastore.tables.table import Table


def example_basic_wal_usage(db_path: str | Path = "example_data.json") -> None:
    """Basic WAL usage - just enable it and go!

    WAL defaults to BUFFERED mode for best performance.
    """
    # Enable WAL with defaults (BUFFERED mode)
    db: BearBase[JSONLStorage] = BearBase(db_path, storage="json", enable_wal=True)

    db.create_table(
        "users",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="name", type="str"),
            Columns(name="email", type="str"),
        ],
    )

    table: Table = db.table("users")

    # Insert 1000 records - fast append to WAL!
    records: list[dict[str, Any]] = [
        {"id": i, "name": f"User{i}", "email": f"user{i}@example.com"} for i in range(1000)
    ]

    table.insert_all(records)  # ~1 second instead of ~30 seconds!

    print(f"Inserted {len(table)} records using WAL")
    db.close()


def example_high_throughput_config(db_path: str | Path = "high_throughput.json") -> None:
    """High-throughput configuration for bulk operations.

    Best for scenarios where:
    - You're inserting thousands of records
    - Small crash window (few seconds) is acceptable
    - Speed is more important than immediate durability
    """
    db: BearBase[JSONLStorage] = BearBase(
        db_path,
        storage="json",
        enable_wal=True,
        wal_config=WALConfig.high_throughput(),  # Preset configuration
    )

    db.create_table(
        "events",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="timestamp", type="int"),
            Columns(name="event_type", type="str"),
            Columns(name="data", type="str"),
        ],
    )

    table: Table = db.table("events")

    # Simulate logging 5000 events
    events: list[dict[str, Any]] = [
        {"id": i, "timestamp": i * 1000, "event_type": "click", "data": f"event_{i}"} for i in range(5000)
    ]

    table.insert_all(events)

    print(f"Logged {len(table)} events with high-throughput WAL")
    db.close()


def example_maximum_safety(db_path: str | Path = "critical_data.json") -> None:
    """Maximum safety configuration for critical data.

    Best for scenarios where:
    - Data loss is unacceptable (financial transactions, etc.)
    - You can accept slower performance for guaranteed durability
    - Each operation must be fsynced to disk immediately
    """
    db: BearBase[JSONLStorage] = BearBase(
        db_path,
        storage="json",
        enable_wal=True,
        wal_config=WALConfig.immediate(),  # Maximum safety preset
    )

    db.create_table(
        "transactions",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="amount", type="float"),
            Columns(name="account", type="str"),
        ],
    )

    table: Table = db.table("transactions")

    # Critical financial transactions - each one is fsynced
    transactions: list[dict[str, Any]] = [
        {"id": 1, "amount": 1500.50, "account": "ACC001"},
        {"id": 2, "amount": 2300.75, "account": "ACC002"},
        {"id": 3, "amount": 500.00, "account": "ACC003"},
    ]

    table.insert_all(transactions)

    print(f"Recorded {len(table)} critical transactions with immediate fsync")
    db.close()


def example_custom_wal_config(db_path: str | Path = "custom_config.json") -> None:
    """Custom WAL configuration with individual parameters.

    Fine-tune WAL behavior for your specific use case.
    """
    db: BearBase[JSONLStorage] = BearBase(
        db_path,
        storage="json",
        enable_wal=True,
        flush_mode="buffered",  # Batch writes
        flush_interval=1.0,  # Flush every 1 second
        flush_batch_size=500,  # Or when 500 operations queued
        auto_checkpoint=True,  # Auto-save to main DB
        checkpoint_threshold=2000,  # Checkpoint every 2000 operations
    )

    db.create_table(
        "logs",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="message", type="str"),
        ],
    )

    table: Table = db.table("logs")

    # Add many log entries
    logs: list[dict[str, Any]] = [{"id": i, "message": f"Log entry {i}"} for i in range(1000)]
    table.insert_all(logs)

    print(f"Added {len(table)} log entries with custom WAL config")
    db.close()


def example_manual_checkpoint(db_path: str | Path = "manual_checkpoint.json") -> None:
    """Manual checkpointing for fine-grained control.

    Use this when you want to control exactly when WAL is flushed
    to the main database and cleared.
    """
    db: BearBase[JSONLStorage] = BearBase(
        db_path,
        storage="json",
        enable_wal=True,
        flush_mode="buffered",
        flush_interval=60.0,  # Long interval - we'll checkpoint manually
    )

    db.create_table(
        "batch_data",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="value", type="str"),
        ],
    )

    table: Table = db.table("batch_data")

    # Insert batch 1
    batch1: list[dict[str, Any]] = [{"id": i, "value": f"batch1_{i}"} for i in range(500)]
    table.insert_all(batch1, flush=False)  # Don't flush yet

    # Insert batch 2
    batch2: list[dict[str, Any]] = [{"id": i + 500, "value": f"batch2_{i}"} for i in range(500)]
    table.insert_all(batch2, flush=False)  # Still no flush

    # Now manually checkpoint everything at once
    if table.wal_helper:
        table.wal_helper.checkpoint(table)
        print("Manually checkpointed 1000 records to main database")

    db.close()


def example_crash_recovery(db_path: str | Path = "recovery_example.json") -> None:
    """Demonstrate crash recovery from WAL.

    This shows how WAL can recover data after a simulated crash.
    """
    from bear_shelf.datastore.wal.helper import WALHelper

    wal_path: Path = Path(db_path).parent / "batch_data.wal"

    # Phase 1: Write data with WAL
    db: BearBase[JSONLStorage] = BearBase(db_path, storage="json", enable_wal=True, wal_dir=str(Path(db_path).parent))

    db.create_table(
        "batch_data",
        columns=[
            Columns(name="id", type="int", primary_key=True),
            Columns(name="value", type="str"),
        ],
    )

    table: Table = db.table("batch_data")

    records: list[dict[str, Any]] = [{"id": i, "value": f"data_{i}"} for i in range(100)]
    table.insert_all(records, flush=False)  # Written to WAL, not main DB

    # Simulate crash - close without checkpoint
    if table.wal_helper:
        table.wal_helper.close()
    db.close()

    print("Simulated crash - data in WAL but not in main database")

    # Phase 2: Recovery after "crash"
    db2: BearBase[JSONLStorage] = BearBase(db_path, storage="json")
    table2: Table = db2.table("batch_data")

    print(f"Records in main DB before recovery: {len(table2)}")

    # Recover from WAL
    wal_helper = WALHelper(file=wal_path, table_name="batch_data", auto_start=False)
    wal_helper.recover_from_wal(table2)

    print(f"Records in main DB after recovery: {len(table2)}")
    print("All data recovered from WAL!")

    db2.close()


if __name__ == "__main__":
    from pathlib import Path
    import tempfile

    # Create temp directory for examples
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        print("=" * 60)
        print("WAL Usage Examples")
        print("=" * 60)

        print("\n1. Basic WAL Usage (Default BUFFERED mode)")
        print("-" * 60)
        example_basic_wal_usage(tmp / "basic.json")

        print("\n2. High-Throughput Configuration")
        print("-" * 60)
        example_high_throughput_config(tmp / "high_throughput.json")

        print("\n3. Maximum Safety Configuration (IMMEDIATE mode)")
        print("-" * 60)
        example_maximum_safety(tmp / "critical.json")

        print("\n4. Custom WAL Configuration")
        print("-" * 60)
        example_custom_wal_config(tmp / "custom.json")

        print("\n5. Manual Checkpointing")
        print("-" * 60)
        example_manual_checkpoint(tmp / "manual.json")

        print("\n6. Crash Recovery Demo")
        print("-" * 60)
        example_crash_recovery(tmp / "recovery.json")

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)


# ruff: noqa: PLC0415
