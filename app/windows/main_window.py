"""Main window. Talks ONLY to services — never to repositories/ORM/SQLite."""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.dialogs.backups_dialog import BackupsDialog
from app.dialogs.entry_dialog import EntryDialog
from app.dialogs.participants_dialog import ParticipantsDialog
from app.dialogs.settings_dialog import SettingsDialog
from app.i18n import entry_type_label, sort_label, status_label, t
from app.workers.sync_worker import SyncWorker
from config.settings import Settings, save_settings
from core.enums import EntryType, SortOption, Status
from core.schemas import EntryRead, EntryUpdate, SyncResult
from core.services.backup_service import BackupService
from core.services.entry_service import EntryService
from core.services.sync_service import SyncError, SyncService
from core.validators.url_validator import is_valid_url
from providers.registry import ProviderRegistry

_ENTRY_ID_ROLE = Qt.ItemDataRole.UserRole

# Subtle per-status tint for list rows - low alpha so it reads as a hint,
# not a solid block, and stays legible on both the light and dark themes.
_STATUS_COLORS: dict[Status, QColor] = {
    Status.PLANNED: QColor(100, 150, 255, 40),
    Status.WATCHING: QColor(255, 200, 60, 40),
    Status.PAUSED: QColor(150, 150, 150, 40),
    Status.COMPLETED: QColor(80, 200, 120, 40),
    Status.DROPPED: QColor(220, 80, 80, 40),
}


class MainWindow(QMainWindow):
    def __init__(
        self,
        entry_service: EntryService,
        sync_service: SyncService,
        settings: Settings,
        provider_registry: ProviderRegistry | None = None,
        backup_service: BackupService | None = None,
    ) -> None:
        super().__init__()
        self._service = entry_service
        self._sync_service = sync_service
        self._settings = settings
        self._providers = provider_registry if provider_registry is not None else ProviderRegistry()
        self._backup_service = backup_service
        self._sync_worker: SyncWorker | None = None
        self.setWindowTitle("MediaVault")
        self.resize(900, 600)
        self._build_ui()
        self._reload()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        top = QHBoxLayout()
        self._search = QLineEdit(placeholderText=t("search_placeholder"))
        self._search.textChanged.connect(self._apply_filters)
        add_btn = QPushButton(t("add"))
        add_btn.clicked.connect(self._on_add)
        watch_btn = QPushButton(t("watch"))
        watch_btn.clicked.connect(self._on_watch)
        edit_btn = QPushButton(t("edit"))
        edit_btn.clicked.connect(self._on_edit)
        delete_btn = QPushButton(t("delete"))
        delete_btn.clicked.connect(self._on_delete)
        self._sync_btn = QPushButton(t("sync"))
        self._sync_btn.clicked.connect(self._on_sync)
        self._participants_btn = QPushButton(t("participants"))
        self._participants_btn.clicked.connect(self._on_participants)
        self._participants_btn.setVisible(self._settings.sync_role == "admin")
        settings_btn = QPushButton(t("settings"))
        settings_btn.clicked.connect(self._on_settings)
        backups_btn = QPushButton(t("backups"))
        backups_btn.clicked.connect(self._on_backups)
        backups_btn.setEnabled(self._backup_service is not None)
        top.addWidget(self._search)
        top.addWidget(add_btn)
        top.addWidget(watch_btn)
        top.addWidget(edit_btn)
        top.addWidget(delete_btn)
        top.addWidget(self._sync_btn)
        top.addWidget(self._participants_btn)
        top.addWidget(settings_btn)
        top.addWidget(backups_btn)

        filters = QHBoxLayout()
        self._type_filter = QComboBox()
        self._type_filter.addItem(t("all_types"), None)
        for entry_type in EntryType:
            self._type_filter.addItem(entry_type_label(entry_type), entry_type)
        self._type_filter.currentIndexChanged.connect(self._apply_filters)

        self._status_filter = QComboBox()
        self._status_filter.addItem(t("all_statuses"), None)
        for status in Status:
            self._status_filter.addItem(status_label(status), status)
        self._status_filter.currentIndexChanged.connect(self._apply_filters)

        self._favorite_filter = QCheckBox(t("favorite"))
        self._favorite_filter.toggled.connect(self._apply_filters)

        self._sort_combo = QComboBox()
        for sort_option in SortOption:
            self._sort_combo.addItem(sort_label(sort_option), sort_option)
        self._sort_combo.currentIndexChanged.connect(self._apply_filters)

        filters.addWidget(self._type_filter)
        filters.addWidget(self._status_filter)
        filters.addWidget(self._favorite_filter)
        filters.addWidget(self._sort_combo)
        filters.addStretch()

        bulk = QHBoxLayout()
        self._bulk_status_combo = QComboBox()
        for status in Status:
            self._bulk_status_combo.addItem(status_label(status), status)
        bulk_apply_btn = QPushButton(t("apply_status_to_selected"))
        bulk_apply_btn.clicked.connect(self._on_bulk_status)
        bulk.addWidget(self._bulk_status_combo)
        bulk.addWidget(bulk_apply_btn)
        bulk.addStretch()

        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._list.itemDoubleClicked.connect(lambda _item: self._on_edit())
        root.addLayout(top)
        root.addLayout(filters)
        root.addLayout(bulk)
        root.addWidget(self._list)
        self.setCentralWidget(central)

    def _reload(self) -> None:
        self._apply_filters()

    def _apply_filters(self) -> None:
        entries = self._service.search(
            self._search.text(),
            status=self._status_filter.currentData(),
            favorites_only=self._favorite_filter.isChecked(),
            entry_type=self._type_filter.currentData(),
            sort=self._sort_combo.currentData(),
        )
        self._render(entries)

    def _selected_entry_id(self) -> int | None:
        item = self._list.currentItem()
        return item.data(_ENTRY_ID_ROLE) if item else None

    def _selected_entry_ids(self) -> list[int]:
        return [item.data(_ENTRY_ID_ROLE) for item in self._list.selectedItems()]

    def _on_add(self) -> None:
        box = QMessageBox(self)
        box.setWindowTitle(t("add_entry_msgbox_title"))
        box.setText(t("how_to_add"))
        by_link = box.addButton(t("by_link"), QMessageBox.ButtonRole.AcceptRole)
        manually = box.addButton(t("manually"), QMessageBox.ButtonRole.AcceptRole)
        box.addButton(t("cancel"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()

        dialog = EntryDialog(self)
        if clicked is by_link:
            url, ok = QInputDialog.getText(self, t("add_by_link_title"), t("paste_link"))
            if not ok or not url.strip():
                return
            url = url.strip()
            if not is_valid_url(url):
                QMessageBox.warning(self, t("validation_title"), t("invalid_url"))
                return
            result = self._providers.resolve(url)
            dialog.prefill_from_url(url, result)
        elif clicked is not manually:
            return

        if dialog.exec() != EntryDialog.DialogCode.Accepted:
            return
        data = dialog.to_create()
        duplicate = self._service.find_duplicate(
            title=data.title, entry_type=data.type, url=data.url
        )
        if duplicate is not None:
            QMessageBox.information(
                self, t("already_in_library_title"), t("already_added", title=duplicate.title)
            )
            return
        self._service.create(data)
        self._reload()

    def _on_watch(self) -> None:
        entry_id = self._selected_entry_id()
        if entry_id is None:
            return
        entry = self._service.get(entry_id)
        if entry is None:
            return
        if not entry.url or not is_valid_url(entry.url):
            QMessageBox.information(self, t("no_link_title"), t("no_valid_link"))
            return
        QDesktopServices.openUrl(QUrl(entry.url))
        self._service.mark_opened(entry_id)
        self._reload()

    def _on_edit(self) -> None:
        entry_id = self._selected_entry_id()
        if entry_id is None:
            return
        entry = self._service.get(entry_id)
        if entry is None:
            return
        dialog = EntryDialog(self, entry=entry)
        if dialog.exec() != EntryDialog.DialogCode.Accepted:
            return
        self._service.update(entry_id, dialog.to_update())
        self._reload()

    def _on_delete(self) -> None:
        entry_ids = self._selected_entry_ids()
        if not entry_ids:
            return
        if len(entry_ids) == 1:
            entry = self._service.get(entry_ids[0])
            if entry is None:
                return
            prompt = t("confirm_delete_one", title=entry.title)
        else:
            prompt = t("confirm_delete_many", count=len(entry_ids))
        answer = QMessageBox.question(self, t("delete_entry_title"), prompt)
        if answer != QMessageBox.StandardButton.Yes:
            return
        for entry_id in entry_ids:
            self._service.delete(entry_id)
        self._reload()

    def _on_bulk_status(self) -> None:
        entry_ids = self._selected_entry_ids()
        if not entry_ids:
            QMessageBox.information(self, t("no_selection_title"), t("select_one_or_more"))
            return
        status = self._bulk_status_combo.currentData()
        for entry_id in entry_ids:
            self._service.update(entry_id, EntryUpdate(status=status))
        self._reload()

    def _configure_sync(self) -> bool:
        server_url, ok = QInputDialog.getText(
            self, t("sync_title"), t("server_address_prompt")
        )
        if not ok or not server_url.strip():
            return False
        key, ok = QInputDialog.getText(self, t("sync_title"), t("key_prompt"))
        if not ok or not key.strip():
            return False
        person_name, ok = QInputDialog.getText(self, t("sync_title"), t("your_name_prompt"))
        if not ok or not person_name.strip():
            return False
        label, ok = QInputDialog.getText(
            self, t("sync_title"), t("device_label_prompt"), text="Windows Desktop"
        )
        if not ok or not label.strip():
            return False
        try:
            token, role = self._sync_service.register_device(
                server_url.strip(), key.strip(), person_name.strip(), label.strip()
            )
        except SyncError as exc:
            QMessageBox.warning(self, t("registration_error_title"), str(exc))
            return False
        self._settings.sync_server_url = server_url.strip()
        self._settings.sync_device_token = token
        self._settings.sync_role = role
        save_settings(self._settings)
        return True

    def _on_sync(self) -> None:
        needs_setup = not self._settings.sync_server_url or not self._settings.sync_device_token
        if needs_setup and not self._configure_sync():
            return
        self._participants_btn.setVisible(self._settings.sync_role == "admin")

        since = None
        if self._settings.sync_last_synced_at:
            since = dt.datetime.fromisoformat(self._settings.sync_last_synced_at)

        assert self._settings.sync_server_url is not None
        assert self._settings.sync_device_token is not None
        assert self._settings.sync_role is not None

        self._sync_btn.setEnabled(False)
        self._sync_btn.setText(t("syncing_ellipsis"))
        worker = SyncWorker(
            self._sync_service,
            self._settings.sync_server_url,
            self._settings.sync_device_token,
            self._settings.sync_role,
            since,
            self,
        )
        worker.succeeded.connect(self._on_sync_succeeded)
        worker.failed.connect(self._on_sync_failed)
        worker.finished.connect(self._on_sync_finished)
        self._sync_worker = worker
        worker.start()

    def _on_sync_succeeded(self, result: SyncResult) -> None:
        self._settings.sync_last_synced_at = result.synced_at.isoformat()
        save_settings(self._settings)
        QMessageBox.information(
            self,
            t("sync_complete_title"),
            t("sync_complete_body", pushed=result.pushed, pulled=result.pulled),
        )
        self._reload()

    def _on_sync_failed(self, message: str) -> None:
        QMessageBox.warning(self, t("sync_error_title"), message)

    def _on_sync_finished(self) -> None:
        self._sync_btn.setEnabled(True)
        self._sync_btn.setText(t("sync"))
        self._sync_worker = None

    def _on_settings(self) -> None:
        dialog = SettingsDialog(self, self._settings)
        dialog.exec()

    def _on_backups(self) -> None:
        if self._backup_service is None:
            return
        dialog = BackupsDialog(self, self._backup_service)
        dialog.exec()

    def _on_participants(self) -> None:
        assert self._settings.sync_server_url is not None
        assert self._settings.sync_device_token is not None
        dialog = ParticipantsDialog(
            self, self._sync_service, self._settings.sync_server_url,
            self._settings.sync_device_token,
        )
        dialog.exec()

    def _render(self, entries: list[EntryRead]) -> None:
        self._list.clear()
        for e in entries:
            fav = "★ " if e.is_favorite else ""
            year = f" ({e.year})" if e.year is not None else ""
            opens = f"  ▶{e.open_count}" if e.open_count else ""
            status = status_label(e.status)
            ratings = []
            if e.rating is not None:
                ratings.append(str(e.rating))
            if e.rating_other is not None:
                ratings.append(t("other_pc_rating", rating=e.rating_other))
            rating_str = f"  [{', '.join(ratings)}]" if ratings else ""
            item = QListWidgetItem(f"{fav}{e.title}{year}{opens}  —  {status}{rating_str}")
            item.setData(_ENTRY_ID_ROLE, e.id)
            item.setBackground(_STATUS_COLORS[e.status])
            self._list.addItem(item)
