"""Headless (offscreen) checks for EntryDialog — catches Qt-layer bugs that
pure service/repository tests can't see (e.g. StrEnum values losing their type
through QVariant when read back from a QComboBox)."""
from __future__ import annotations

import datetime as dt
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.dialogs.entry_dialog import EntryDialog, guess_title_from_url
from core.enums import EntryType, Status
from core.schemas import EntryRead
from providers.base import ProviderResult


@pytest.fixture(scope="module", autouse=True)
def qapp() -> QApplication:
    app = QApplication.instance()
    return app if isinstance(app, QApplication) else QApplication([])


def _existing_entry() -> EntryRead:
    now = dt.datetime.now(dt.UTC)
    return EntryRead(
        id=1, uuid="11111111-1111-1111-1111-111111111111",
        type=EntryType.SERIES, title="Breaking Bad", original_title=None,
        status=Status.WATCHING, rating=9, rating_other=None, year=2008, url=None,
        open_count=3, description=None, comment=None, is_favorite=True, season=2, episode=5,
        last_watched_at=None, created_at=now, updated_at=now, deleted_at=None,
    )


def test_guess_title_from_url() -> None:
    url = "https://kinogo.ec/125434-mandalorec-i-grogu.html#125434"
    assert guess_title_from_url(url) == "Mandalorec I Grogu"


def test_add_dialog_type_switch_toggles_episodic_fields() -> None:
    dialog = EntryDialog()
    dialog._type.setCurrentIndex(dialog._type.findData(EntryType.SERIES))
    assert dialog._season.isEnabled()
    assert dialog._episode.isEnabled()
    dialog._type.setCurrentIndex(dialog._type.findData(EntryType.MOVIE))
    assert not dialog._season.isEnabled()
    assert not dialog._episode.isEnabled()


def test_prefill_from_url_sets_url_and_guessed_title() -> None:
    dialog = EntryDialog()
    url = "https://kinogo.ec/125434-mandalorec-i-grogu.html#125434"
    dialog.prefill_from_url(url)
    data = dialog.to_create()
    assert data.url == url
    assert data.title == "Mandalorec I Grogu"
    assert data.type == EntryType.MOVIE


def test_prefill_from_url_uses_provider_result_over_guess() -> None:
    dialog = EntryDialog()
    url = "https://kinogo.ec/125434-mandalorec-i-grogu.html#125434"
    result = ProviderResult(
        title="The Mandalorian and Grogu",
        original_title="The Mandalorian & Grogu",
        description="A bounty hunter and a child.",
    )
    dialog.prefill_from_url(url, result)
    data = dialog.to_create()
    assert data.url == url
    assert data.title == "The Mandalorian and Grogu"
    assert data.original_title == "The Mandalorian & Grogu"
    assert data.description == "A bounty hunter and a child."


def test_prefill_from_url_falls_back_to_guess_when_provider_finds_nothing() -> None:
    dialog = EntryDialog()
    url = "https://kinogo.ec/125434-mandalorec-i-grogu.html#125434"
    dialog.prefill_from_url(url, ProviderResult())
    data = dialog.to_create()
    assert data.title == "Mandalorec I Grogu"


def test_edit_dialog_prefill_roundtrip() -> None:
    dialog = EntryDialog(entry=_existing_entry())
    assert dialog._current_type() == EntryType.SERIES
    assert dialog._current_status() == Status.WATCHING
    assert dialog._season.isEnabled()
    update = dialog.to_update()
    assert update.season == 2
    assert update.episode == 5
    assert update.rating == 9
