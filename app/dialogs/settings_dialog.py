"""Settings screen (ROADMAP v0.7): edits config/settings.json instead of
requiring hand-editing. Sync fields (server/token/role) are deliberately
excluded here - they're managed by the dedicated sync setup dialog
(MainWindow._configure_sync), and hand-editing a device token would just
break pairing silently.

database_path/backups_dir/logs_dir only take effect after a restart: the
SQLite engine and session factory are built once at startup (main.py) and
re-pointing them live is a bigger structural change than this screen does.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from app.i18n import LANGUAGE_LABELS, SUPPORTED_LANGUAGES, t
from app.theme.manager import THEMES_DIR, load_theme
from config.settings import Settings, save_settings


class SettingsDialog(QDialog):
    def __init__(self, parent: object, settings: Settings) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._settings = settings
        self._original_theme = settings.theme
        self.setWindowTitle(t("settings"))
        self._build_ui()

    def _build_ui(self) -> None:
        form = QFormLayout()

        self._theme = QComboBox()
        for qss_path in sorted(THEMES_DIR.glob("*.qss")):
            self._theme.addItem(qss_path.stem)
        current_index = self._theme.findText(self._settings.theme)
        self._theme.setCurrentIndex(current_index if current_index >= 0 else 0)
        self._theme.currentTextChanged.connect(self._preview_theme)
        form.addRow(t("theme_field"), self._theme)

        self._language = QComboBox()
        for language in SUPPORTED_LANGUAGES:
            self._language.addItem(LANGUAGE_LABELS[language], language)
        language_index = self._language.findData(self._settings.language)
        self._language.setCurrentIndex(language_index if language_index >= 0 else 0)
        form.addRow(t("language_field"), self._language)

        self._backup_keep = QSpinBox()
        self._backup_keep.setRange(1, 3650)
        self._backup_keep.setValue(self._settings.backup_keep)
        form.addRow(t("backup_keep_field"), self._backup_keep)

        self._autobackup_daily = QCheckBox(t("autobackup_daily_field"))
        self._autobackup_daily.setChecked(self._settings.autobackup_daily)
        form.addRow(self._autobackup_daily)

        self._database_path = QLineEdit(self._settings.database_path)
        form.addRow(t("db_path_field"), self._database_path)

        self._backups_dir = QLineEdit(self._settings.backups_dir)
        form.addRow(t("backups_dir_field"), self._backups_dir)

        self._logs_dir = QLineEdit(self._settings.logs_dir)
        form.addRow(t("logs_dir_field"), self._logs_dir)

        note = QLabel(t("settings_restart_note"))
        note.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self._on_reject)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(note)
        root.addWidget(buttons)

    def _preview_theme(self, name: str) -> None:
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.setStyleSheet(load_theme(name))

    def _on_reject(self) -> None:
        self._preview_theme(self._original_theme)  # undo a live preview
        self.reject()

    def _on_accept(self) -> None:
        self._settings.theme = self._theme.currentText()
        self._settings.language = self._language.currentData()
        self._settings.backup_keep = self._backup_keep.value()
        self._settings.autobackup_daily = self._autobackup_daily.isChecked()
        self._settings.database_path = self._database_path.text().strip() or (
            self._settings.database_path
        )
        self._settings.backups_dir = self._backups_dir.text().strip() or (
            self._settings.backups_dir
        )
        self._settings.logs_dir = self._logs_dir.text().strip() or self._settings.logs_dir
        save_settings(self._settings)
        self.accept()
