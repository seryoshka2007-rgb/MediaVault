"""Headless (offscreen) checks for ParticipantsDialog — same rationale as
test_main_window.py: pure service tests can't see Qt-layer wiring bugs."""
from __future__ import annotations

import datetime as dt
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from app.dialogs.participants_dialog import ParticipantsDialog
from core.schemas import DeviceSummary, ParticipantSummary
from core.services.sync_service import SyncService

_NOW = dt.datetime.now(dt.UTC)


@pytest.fixture(scope="module", autouse=True)
def qapp() -> QApplication:
    app = QApplication.instance()
    return app if isinstance(app, QApplication) else QApplication([])


def _participants() -> list[ParticipantSummary]:
    return [
        ParticipantSummary(
            person_id=1,
            name="Owner",
            role="admin",
            created_at=_NOW,
            devices=[DeviceSummary(device_id=1, label="Desktop", created_at=_NOW)],
        ),
        ParticipantSummary(
            person_id=2,
            name="Alice",
            role="participant",
            created_at=_NOW,
            devices=[DeviceSummary(device_id=2, label="Phone", created_at=_NOW)],
        ),
    ]


def _dialog(sync_service: SyncService, monkeypatch: pytest.MonkeyPatch) -> ParticipantsDialog:
    monkeypatch.setattr(sync_service, "list_participants", lambda *a, **kw: _participants())
    return ParticipantsDialog(None, sync_service, "http://server:8000", "admin-tok")


def test_dialog_lists_participants_and_devices(
    sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    dialog = _dialog(sync_service, monkeypatch)

    texts = [dialog._list.item(i).text() for i in range(dialog._list.count())]

    assert texts == ["Owner  (admin)", "    Desktop", "Alice  (participant)", "    Phone"]


def test_revoke_calls_service_with_selected_device_id(
    sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    dialog = _dialog(sync_service, monkeypatch)
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        sync_service,
        "revoke_device",
        lambda url, token, device_id: captured.update(device_id=device_id),
    )
    monkeypatch.setattr(
        QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.Yes
    )

    dialog._list.setCurrentRow(3)  # "    Phone" under Alice
    dialog._on_revoke()

    assert captured["device_id"] == 2


def test_revoke_without_device_row_selected_shows_message(
    sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    dialog = _dialog(sync_service, monkeypatch)
    revoke_called = False

    def fake_revoke(*a: object, **kw: object) -> None:
        nonlocal revoke_called
        revoke_called = True

    monkeypatch.setattr(sync_service, "revoke_device", fake_revoke)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **kw: None)

    dialog._list.setCurrentRow(0)  # "Owner  (admin)" header row, no device
    dialog._on_revoke()

    assert revoke_called is False
