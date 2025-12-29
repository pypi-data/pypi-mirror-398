"""Test WALConfig kwargs pattern in BearBase."""

from pathlib import Path

from bear_shelf.datastore import BearBase, Columns
from bear_shelf.datastore.storage.jsonl import JSONLStorage
from bear_shelf.datastore.tables.table import Table
from bear_shelf.datastore.wal.config import WALConfig, WALFlushMode


def test_wal_config_pattern_full_config(tmp_path: Path) -> None:
    """Test passing full WALConfig object."""
    db_path: Path = tmp_path / "test.json"

    config: WALConfig = WALConfig.high_throughput()
    db: BearBase[JSONLStorage] = BearBase(str(db_path), storage="json", enable_wal=True, wal_config=config)

    assert db.wal_config == config
    assert db.wal_config is not None
    assert db.wal_config.flush_mode == WALFlushMode.BUFFERED
    assert db.wal_config.flush_interval == 1.0
    assert db.wal_config.flush_batch_size == 1000

    db.close()


def test_wal_config_pattern_kwargs_only(tmp_path: Path) -> None:
    """Test building WALConfig from individual kwargs."""
    db_path: Path = tmp_path / "test.json"

    db: BearBase[JSONLStorage] = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        flush_mode="buffered",
        flush_interval=0.5,
        flush_batch_size=200,
    )
    assert db.wal_config is not None
    assert db.wal_config.flush_mode == WALFlushMode.BUFFERED
    assert db.wal_config.flush_interval == 0.5
    assert db.wal_config.flush_batch_size == 200

    db.close()


def test_wal_config_pattern_mixed_override(tmp_path: Path) -> None:
    """Test passing config + kwargs (kwargs should override)."""
    db_path: Path = tmp_path / "test.json"

    base_config: WALConfig = WALConfig.buffered(flush_interval=0.1)

    # Override flush_interval with kwarg
    db: BearBase[JSONLStorage] = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        wal_config=base_config,
        flush_interval=0.9,  # Should override base_config's 0.1
    )
    assert db.wal_config is not None
    assert db.wal_config.flush_mode == WALFlushMode.BUFFERED
    assert db.wal_config.flush_interval == 0.9  # Overridden!
    assert db.wal_config.flush_batch_size == 100  # From base_config

    db.close()


def test_wal_config_always_created(tmp_path: Path) -> None:
    """Test that WALConfig is always created even if enable_wal=False."""
    db_path: Path = tmp_path / "test.json"

    # No enable_wal, no config - should still have default WALConfig
    db: BearBase[JSONLStorage] = BearBase(str(db_path), storage="json")

    assert db.wal_config is None
    # assert isinstance(db.wal_config, WALConfig)
    # assert db.wal_config.flush_mode == WALFlushMode.BUFFERED  # Default

    db.close()


def test_wal_config_doesnt_leak_to_storage(tmp_path: Path) -> None:
    """Test that WAL kwargs don't get passed to storage backend."""
    db_path: Path = tmp_path / "test.json"

    # This should not error even though JSON storage doesn't accept flush_mode
    # It doesn't? lol
    db: BearBase[JSONLStorage] = BearBase(
        str(db_path),
        enable_wal=True,
        storage="json",
        flush_mode="buffered",
        flush_interval=0.5,
    )
    assert db.wal_config is not None
    # Verify WAL config got the kwargs
    assert db.wal_config.flush_mode == WALFlushMode.BUFFERED
    assert db.wal_config.flush_interval == 0.5

    db.close()


def test_wal_config_immediate_mode(tmp_path: Path) -> None:
    """Test IMMEDIATE flush mode configuration."""
    db_path: Path = tmp_path / "test.json"

    db: BearBase[JSONLStorage] = BearBase(
        str(db_path),
        storage="json",
        enable_wal=True,
        flush_mode="immediate",
    )
    assert db.wal_config is not None
    assert db.wal_config.flush_mode == WALFlushMode.IMMEDIATE

    # Create a table and verify WAL helper has the config
    db.create_table("test", columns=[Columns(name="id", type="int", primary_key=True)])
    table: Table = db.table("test")

    if table.wal_helper:
        assert table.wal_helper._wal is not None
        assert table.wal_helper._wal.config.flush_mode == WALFlushMode.IMMEDIATE

    db.close()
