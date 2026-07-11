"""BackupService.list_backups/restore, against a real SQLite file on disk
(no mocking - the whole point is exercising the actual SQLite backup API)."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest

from core.services.backup_service import BackupService


def _make_db(path: Path, value: str) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS marker (value TEXT)")
        conn.execute("DELETE FROM marker")
        conn.execute("INSERT INTO marker (value) VALUES (?)", (value,))
        conn.commit()
    finally:
        conn.close()


def _read_marker(path: Path) -> str:
    conn = sqlite3.connect(path)
    try:
        row = conn.execute("SELECT value FROM marker").fetchone()
        assert row is not None
        return str(row[0])
    finally:
        conn.close()


def test_list_backups_empty_when_dir_missing(tmp_path: Path) -> None:
    service = BackupService(tmp_path / "db.sqlite", tmp_path / "backups")
    assert service.list_backups() == []


def test_list_backups_sorted_newest_first(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    _make_db(db_path, "v1")
    service = BackupService(db_path, tmp_path / "backups")

    first = service.create(reason="one")
    time.sleep(0.01)
    second = service.create(reason="two")

    backups = service.list_backups()
    assert list(backups) == [second, first]


def test_restore_brings_back_old_data_and_keeps_a_safety_backup(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    _make_db(db_path, "original")
    service = BackupService(db_path, tmp_path / "backups")
    original_backup = service.create(reason="checkpoint")
    assert original_backup is not None

    _make_db(db_path, "mutated")
    assert _read_marker(db_path) == "mutated"

    service.restore(original_backup)

    assert _read_marker(db_path) == "original"
    reasons = [p.name for p in service.list_backups()]
    assert any("pre_restore" in name for name in reasons)


def test_restore_missing_backup_raises(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite"
    _make_db(db_path, "original")
    service = BackupService(db_path, tmp_path / "backups")

    with pytest.raises(FileNotFoundError):
        service.restore(tmp_path / "backups" / "does-not-exist.db")
