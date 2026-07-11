"""Headless (offscreen) checks for BackupsDialog — same rationale as
test_participants_dialog.py: pure service tests can't see Qt-layer wiring."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from app.dialogs.backups_dialog import BackupsDialog
from core.services.backup_service import BackupService


@pytest.fixture(scope="module", autouse=True)
def qapp() -> QApplication:
    app = QApplication.instance()
    return app if isinstance(app, QApplication) else QApplication([])


def _service(tmp_path: Path) -> BackupService:
    db_path = tmp_path / "db.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.commit()
    conn.close()
    return BackupService(db_path, tmp_path / "backups")


def test_dialog_lists_existing_backups(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.create(reason="one")

    dialog = BackupsDialog(None, service)

    assert dialog._list.count() == 1


def test_create_button_adds_a_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    dialog = BackupsDialog(None, service)
    assert dialog._list.count() == 0
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **kw: None)

    dialog._on_create()

    assert dialog._list.count() == 1


def test_restore_without_selection_shows_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    dialog = BackupsDialog(None, service)
    shown = []
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **kw: shown.append(1))

    dialog._on_restore()

    assert shown == [1]


def test_restore_confirmed_calls_service_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    service.create(reason="one")
    dialog = BackupsDialog(None, service)
    dialog._list.setCurrentRow(0)

    monkeypatch.setattr(
        QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.Yes
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **kw: None)
    restored: list[Path] = []
    monkeypatch.setattr(service, "restore", restored.append)

    dialog._on_restore()

    assert len(restored) == 1
