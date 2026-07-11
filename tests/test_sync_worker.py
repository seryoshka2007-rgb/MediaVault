"""Headless (offscreen) checks for SyncWorker - same rationale as
test_main_window.py: a QThread's signal wiring can't be seen from a pure
service test. run() is called directly (not start()) so the emission
happens synchronously in the test thread, no event loop needed."""
from __future__ import annotations

import datetime as dt
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.workers.sync_worker import SyncWorker
from core.schemas import SyncResult
from core.services.sync_service import SyncError, SyncService


@pytest.fixture(scope="module", autouse=True)
def qapp() -> QApplication:
    app = QApplication.instance()
    return app if isinstance(app, QApplication) else QApplication([])


def test_worker_emits_succeeded_on_success(
    sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = SyncResult(pushed=2, pulled=1, synced_at=dt.datetime.now(dt.UTC))
    monkeypatch.setattr(sync_service, "sync_now", lambda *a, **kw: expected)  # noqa: ANN401

    worker = SyncWorker(sync_service, "http://server", "tok", "admin", None)
    received: list[SyncResult] = []
    failures: list[str] = []
    worker.succeeded.connect(received.append)
    worker.failed.connect(failures.append)

    worker.run()

    assert received == [expected]
    assert failures == []


def test_worker_emits_failed_on_sync_error(
    sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(*a: object, **kw: object) -> SyncResult:
        raise SyncError("сервер недоступен")

    monkeypatch.setattr(sync_service, "sync_now", _raise)

    worker = SyncWorker(sync_service, "http://server", "tok", "admin", None)
    received: list[SyncResult] = []
    failures: list[str] = []
    worker.succeeded.connect(received.append)
    worker.failed.connect(failures.append)

    worker.run()

    assert received == []
    assert failures == ["сервер недоступен"]
