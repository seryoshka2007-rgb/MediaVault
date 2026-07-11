"""Main window. Talks ONLY to services — never to repositories/ORM/SQLite."""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
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

from app.dialogs.entry_dialog import EntryDialog
from app.dialogs.participants_dialog import ParticipantsDialog
from app.workers.sync_worker import SyncWorker
from config.settings import Settings, save_settings
from core.enums import (
    ENTRY_TYPE_LABELS_RU,
    SORT_LABELS_RU,
    STATUS_LABELS_RU,
    EntryType,
    SortOption,
    Status,
)
from core.schemas import EntryRead, SyncResult
from core.services.entry_service import EntryService
from core.services.sync_service import SyncError, SyncService
from core.validators.url_validator import is_valid_url

_ENTRY_ID_ROLE = Qt.ItemDataRole.UserRole


class MainWindow(QMainWindow):
    def __init__(
        self, entry_service: EntryService, sync_service: SyncService, settings: Settings
    ) -> None:
        super().__init__()
        self._service = entry_service
        self._sync_service = sync_service
        self._settings = settings
        self._sync_worker: SyncWorker | None = None
        self.setWindowTitle("MediaVault")
        self.resize(900, 600)
        self._build_ui()
        self._reload()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        top = QHBoxLayout()
        self._search = QLineEdit(placeholderText="Поиск…")
        self._search.textChanged.connect(self._apply_filters)
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self._on_add)
        watch_btn = QPushButton("Смотреть")
        watch_btn.clicked.connect(self._on_watch)
        edit_btn = QPushButton("Изменить")
        edit_btn.clicked.connect(self._on_edit)
        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self._on_delete)
        self._sync_btn = QPushButton("Синхронизировать")
        self._sync_btn.clicked.connect(self._on_sync)
        self._participants_btn = QPushButton("Участники")
        self._participants_btn.clicked.connect(self._on_participants)
        self._participants_btn.setVisible(self._settings.sync_role == "admin")
        top.addWidget(self._search)
        top.addWidget(add_btn)
        top.addWidget(watch_btn)
        top.addWidget(edit_btn)
        top.addWidget(delete_btn)
        top.addWidget(self._sync_btn)
        top.addWidget(self._participants_btn)

        filters = QHBoxLayout()
        self._type_filter = QComboBox()
        self._type_filter.addItem("Все типы", None)
        for entry_type in EntryType:
            self._type_filter.addItem(ENTRY_TYPE_LABELS_RU[entry_type], entry_type)
        self._type_filter.currentIndexChanged.connect(self._apply_filters)

        self._status_filter = QComboBox()
        self._status_filter.addItem("Все статусы", None)
        for status in Status:
            self._status_filter.addItem(STATUS_LABELS_RU[status], status)
        self._status_filter.currentIndexChanged.connect(self._apply_filters)

        self._favorite_filter = QCheckBox("Избранное")
        self._favorite_filter.toggled.connect(self._apply_filters)

        self._sort_combo = QComboBox()
        for sort_option in SortOption:
            self._sort_combo.addItem(SORT_LABELS_RU[sort_option], sort_option)
        self._sort_combo.currentIndexChanged.connect(self._apply_filters)

        filters.addWidget(self._type_filter)
        filters.addWidget(self._status_filter)
        filters.addWidget(self._favorite_filter)
        filters.addWidget(self._sort_combo)
        filters.addStretch()

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(lambda _item: self._on_edit())
        root.addLayout(top)
        root.addLayout(filters)
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

    def _on_add(self) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("Добавление записи")
        box.setText("Как добавить запись?")
        by_link = box.addButton("По ссылке", QMessageBox.ButtonRole.AcceptRole)
        manually = box.addButton("Вручную", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()

        dialog = EntryDialog(self)
        if clicked is by_link:
            url, ok = QInputDialog.getText(self, "Добавить по ссылке", "Вставьте ссылку:")
            if not ok or not url.strip():
                return
            url = url.strip()
            if not is_valid_url(url):
                QMessageBox.warning(self, "Проверка", "Ссылка выглядит некорректно.")
                return
            dialog.prefill_from_url(url)
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
                self, "Уже есть в библиотеке", f"Уже добавлено: {duplicate.title}"
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
            QMessageBox.information(self, "Нет ссылки", "У этой записи нет корректной ссылки.")
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
        entry_id = self._selected_entry_id()
        if entry_id is None:
            return
        entry = self._service.get(entry_id)
        if entry is None:
            return
        answer = QMessageBox.question(
            self, "Удалить запись", f"Удалить «{entry.title}»?"
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._service.delete(entry_id)
        self._reload()

    def _configure_sync(self) -> bool:
        server_url, ok = QInputDialog.getText(
            self, "Синхронизация", "Адрес сервера (например http://100.x.x.x:8000):"
        )
        if not ok or not server_url.strip():
            return False
        key, ok = QInputDialog.getText(
            self, "Синхронизация", "Ключ (admin key — ваш, или ключ участника):"
        )
        if not ok or not key.strip():
            return False
        person_name, ok = QInputDialog.getText(
            self, "Синхронизация", "Ваше имя (для общего сервера с другими людьми):"
        )
        if not ok or not person_name.strip():
            return False
        label, ok = QInputDialog.getText(
            self, "Синхронизация", "Название этого устройства:", text="Windows Desktop"
        )
        if not ok or not label.strip():
            return False
        try:
            token, role = self._sync_service.register_device(
                server_url.strip(), key.strip(), person_name.strip(), label.strip()
            )
        except SyncError as exc:
            QMessageBox.warning(self, "Ошибка регистрации", str(exc))
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
        self._sync_btn.setText("Синхронизация…")
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
            "Синхронизация завершена",
            f"Отправлено: {result.pushed}\nПолучено: {result.pulled}",
        )
        self._reload()

    def _on_sync_failed(self, message: str) -> None:
        QMessageBox.warning(self, "Ошибка синхронизации", message)

    def _on_sync_finished(self) -> None:
        self._sync_btn.setEnabled(True)
        self._sync_btn.setText("Синхронизировать")
        self._sync_worker = None

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
            status = STATUS_LABELS_RU[e.status]
            ratings = []
            if e.rating is not None:
                ratings.append(str(e.rating))
            if e.rating_other is not None:
                ratings.append(f"др.ПК: {e.rating_other}")
            rating_str = f"  [{', '.join(ratings)}]" if ratings else ""
            item = QListWidgetItem(f"{fav}{e.title}{year}{opens}  —  {status}{rating_str}")
            item.setData(_ENTRY_ID_ROLE, e.id)
            self._list.addItem(item)
