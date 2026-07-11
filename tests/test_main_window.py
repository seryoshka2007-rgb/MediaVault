"""Headless (offscreen) checks for MainWindow wiring — same rationale as
test_entry_dialog.py: pure service tests can't see Qt-layer bugs."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QInputDialog, QMessageBox

from app.dialogs.entry_dialog import EntryDialog
from app.windows.main_window import MainWindow
from config.settings import Settings
from core.enums import Status
from core.schemas import EntryCreate
from core.services.entry_service import EntryService
from core.services.sync_service import SyncService
from providers.base import ProviderResult
from providers.registry import ProviderRegistry


def _window(
    service: EntryService,
    sync_service: SyncService,
    provider_registry: ProviderRegistry | None = None,
) -> MainWindow:
    return MainWindow(service, sync_service, Settings(), provider_registry)


@pytest.fixture(scope="module", autouse=True)
def qapp() -> QApplication:
    app = QApplication.instance()
    return app if isinstance(app, QApplication) else QApplication([])


def test_watch_button_opens_url_and_bumps_count(
    service: EntryService, sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    entry = service.create(EntryCreate(title="Dune", url="https://example.com/dune"))
    opened_urls: list[str] = []
    monkeypatch.setattr(
        QDesktopServices, "openUrl", lambda qurl: opened_urls.append(qurl.toString())
    )

    window = _window(service, sync_service)
    window._list.setCurrentRow(0)
    window._on_watch()

    assert opened_urls == ["https://example.com/dune"]
    assert service.get(entry.id).open_count == 1  # type: ignore[union-attr]
    assert "▶1" in window._list.item(0).text()


def test_watch_button_without_url_shows_message(
    service: EntryService, sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    service.create(EntryCreate(title="No Link"))
    opened_urls: list[str] = []
    monkeypatch.setattr(
        QDesktopServices, "openUrl", lambda qurl: opened_urls.append(qurl.toString())
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **kw: None)

    window = _window(service, sync_service)
    window._list.setCurrentRow(0)
    window._on_watch()

    assert opened_urls == []


class _FakeRegistry:
    """Duck-types ProviderRegistry.resolve without a real network call."""

    def __init__(self, result: ProviderResult) -> None:
        self._result = result

    def resolve(self, url: str) -> ProviderResult:
        return self._result


def test_add_by_link_prefills_from_provider_result(
    service: EntryService, sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _FakeRegistry(ProviderResult(title="From Provider", description="Synopsis"))
    window = _window(service, sync_service, registry)  # type: ignore[arg-type]

    # Simulate: user picks "По ссылке" (the first button added to the box),
    # types a URL, and accepts the entry dialog as prefilled.
    monkeypatch.setattr(QMessageBox, "exec", lambda self: None)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: self.buttons()[0])
    monkeypatch.setattr(
        QInputDialog, "getText", staticmethod(lambda *a, **kw: ("https://example.com/movie", True))
    )
    monkeypatch.setattr(EntryDialog, "exec", lambda self: EntryDialog.DialogCode.Accepted)

    window._on_add()

    entries = service.list_all()
    assert len(entries) == 1
    assert entries[0].title == "From Provider"
    assert entries[0].description == "Synopsis"


def _select_titles(window: MainWindow, *titles: str) -> None:
    for row in range(window._list.count()):
        item = window._list.item(row)
        if any(item.text().startswith(title) for title in titles):
            item.setSelected(True)


def test_bulk_delete_removes_all_selected_entries(
    service: EntryService, sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    service.create(EntryCreate(title="A"))
    service.create(EntryCreate(title="B"))
    service.create(EntryCreate(title="C"))
    window = _window(service, sync_service)
    _select_titles(window, "A", "B")
    monkeypatch.setattr(
        QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.Yes
    )

    window._on_delete()

    remaining = {e.title for e in service.list_all()}
    assert remaining == {"C"}


def test_bulk_status_change_applies_to_all_selected(
    service: EntryService, sync_service: SyncService
) -> None:
    a = service.create(EntryCreate(title="A"))
    b = service.create(EntryCreate(title="B"))
    service.create(EntryCreate(title="C"))
    window = _window(service, sync_service)
    _select_titles(window, "A", "B")
    idx = window._bulk_status_combo.findData(Status.COMPLETED)
    window._bulk_status_combo.setCurrentIndex(idx)

    window._on_bulk_status()

    assert service.get(a.id).status == Status.COMPLETED  # type: ignore[union-attr]
    assert service.get(b.id).status == Status.COMPLETED  # type: ignore[union-attr]
    c = next(e for e in service.list_all() if e.title == "C")
    assert c.status == Status.PLANNED
