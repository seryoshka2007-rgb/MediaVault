"""Headless (offscreen) checks for SettingsDialog — same rationale as
test_entry_dialog.py: pure config tests can't see Qt-layer wiring bugs."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

import app.dialogs.settings_dialog as settings_dialog_module
from app.dialogs.settings_dialog import SettingsDialog
from config.settings import Settings


@pytest.fixture(scope="module", autouse=True)
def qapp() -> QApplication:
    app = QApplication.instance()
    return app if isinstance(app, QApplication) else QApplication([])


def test_theme_combo_lists_available_themes() -> None:
    dialog = SettingsDialog(None, Settings())

    items = [dialog._theme.itemText(i) for i in range(dialog._theme.count())]

    assert "neon_dark" in items
    assert "light" in items
    assert dialog._theme.currentText() == "neon_dark"


def test_language_combo_defaults_to_settings_value() -> None:
    dialog = SettingsDialog(None, Settings(language="en"))

    assert dialog._language.currentData() == "en"


def test_accept_saves_edited_values(monkeypatch: pytest.MonkeyPatch) -> None:
    saved: list[Settings] = []
    monkeypatch.setattr(settings_dialog_module, "save_settings", saved.append)

    settings = Settings()
    dialog = SettingsDialog(None, settings)
    dialog._backup_keep.setValue(7)
    dialog._autobackup_daily.setChecked(False)
    dialog._database_path.setText("custom/db.sqlite")
    idx = dialog._language.findData("uk")
    dialog._language.setCurrentIndex(idx)

    dialog._on_accept()

    assert len(saved) == 1
    assert settings.backup_keep == 7
    assert settings.autobackup_daily is False
    assert settings.database_path == "custom/db.sqlite"
    assert settings.language == "uk"


def test_reject_reverts_theme_preview(monkeypatch: pytest.MonkeyPatch) -> None:
    applied: list[str] = []
    settings = Settings()
    dialog = SettingsDialog(None, settings)

    monkeypatch.setattr(dialog, "_preview_theme", applied.append)
    dialog._on_reject()

    assert applied == [settings.theme]
