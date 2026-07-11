"""Database backups using SQLite's online backup API (consistent even while in use).

Used both on a schedule (>= once per day) and before dangerous operations.
"""
from __future__ import annotations

import datetime as dt
import logging
import sqlite3
from collections.abc import Sequence
from pathlib import Path

log = logging.getLogger(__name__)


class BackupService:
    def __init__(self, db_path: Path, backups_dir: Path, keep: int = 30) -> None:
        self._db_path = db_path
        self._backups_dir = backups_dir
        self._keep = keep

    def create(self, reason: str = "manual") -> Path | None:
        if not self._db_path.exists():
            return None
        self._backups_dir.mkdir(parents=True, exist_ok=True)
        ts = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dest = self._backups_dir / f"mediavault_{ts}_{reason}.db"

        src = sqlite3.connect(self._db_path)
        try:
            dst = sqlite3.connect(dest)
            try:
                src.backup(dst)  # atomic, consistent snapshot
            finally:
                dst.close()
        finally:
            src.close()

        log.info("Backup created (%s): %s", reason, dest.name)
        self._prune()
        return dest

    def create_daily_if_needed(self) -> Path | None:
        today = dt.date.today().isoformat()
        already = any(
            today in p.name for p in self._backups_dir.glob("mediavault_*.db")
        ) if self._backups_dir.exists() else False
        return None if already else self.create(reason="daily")

    def list_backups(self) -> Sequence[Path]:
        """Newest first, so a browsing UI can show the most recent on top."""
        if not self._backups_dir.exists():
            return []
        return sorted(
            self._backups_dir.glob("mediavault_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    def restore(self, backup_path: Path) -> None:
        """Restore the live database from a snapshot, via SQLite's backup API
        (never a raw file copy - see CLAUDE.md). Takes a safety backup of the
        current state first, since this is a "potentially dangerous
        operation" per CLAUDE.md's rule.

        Takes effect only after the app is restarted: this process's
        already-open SQLAlchemy engine/connections keep referencing
        pre-restore state otherwise.
        """
        if not backup_path.exists():
            raise FileNotFoundError(backup_path)
        self.create(reason="pre_restore")

        source = sqlite3.connect(backup_path)
        try:
            target = sqlite3.connect(self._db_path)
            try:
                source.backup(target)
            finally:
                target.close()
        finally:
            source.close()
        log.info("Restored database from backup: %s", backup_path.name)

    def _prune(self) -> None:
        backups = sorted(
            self._backups_dir.glob("mediavault_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old in backups[self._keep:]:
            old.unlink(missing_ok=True)
            log.info("Pruned old backup: %s", old.name)
