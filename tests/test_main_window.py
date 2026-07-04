"""Headless (offscreen) checks for MainWindow wiring — same rationale as
test_entry_dialog.py: pure service tests can't see Qt-layer bugs."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMessageBox

from app.windows.main_window import MainWindow
from core.schemas import EntryCreate
from core.services.entry_service import EntryService


@pytest.fixture(scope="module", autouse=True)
def qapp() -> QApplication:
    app = QApplication.instance()
    return app if isinstance(app, QApplication) else QApplication([])


def test_watch_button_opens_url_and_bumps_count(
    service: EntryService, monkeypatch: pytest.MonkeyPatch
) -> None:
    entry = service.create(EntryCreate(title="Dune", url="https://example.com/dune"))
    opened_urls: list[str] = []
    monkeypatch.setattr(
        QDesktopServices, "openUrl", lambda qurl: opened_urls.append(qurl.toString())
    )

    window = MainWindow(service)
    window._list.setCurrentRow(0)
    window._on_watch()

    assert opened_urls == ["https://example.com/dune"]
    assert service.get(entry.id).open_count == 1  # type: ignore[union-attr]
    assert "▶1" in window._list.item(0).text()


def test_watch_button_without_url_shows_message(
    service: EntryService, monkeypatch: pytest.MonkeyPatch
) -> None:
    service.create(EntryCreate(title="No Link"))
    opened_urls: list[str] = []
    monkeypatch.setattr(
        QDesktopServices, "openUrl", lambda qurl: opened_urls.append(qurl.toString())
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **kw: None)

    window = MainWindow(service)
    window._list.setCurrentRow(0)
    window._on_watch()

    assert opened_urls == []
