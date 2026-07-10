"""Main window. Talks ONLY to services — never to repositories/ORM/SQLite."""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
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
from config.settings import Settings, save_settings
from core.enums import STATUS_LABELS_RU
from core.schemas import EntryRead
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
        self.setWindowTitle("MediaVault")
        self.resize(900, 600)
        self._build_ui()
        self._reload()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        top = QHBoxLayout()
        self._search = QLineEdit(placeholderText="Поиск…")
        self._search.textChanged.connect(self._on_search)
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self._on_add)
        watch_btn = QPushButton("Смотреть")
        watch_btn.clicked.connect(self._on_watch)
        edit_btn = QPushButton("Изменить")
        edit_btn.clicked.connect(self._on_edit)
        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self._on_delete)
        sync_btn = QPushButton("Синхронизировать")
        sync_btn.clicked.connect(self._on_sync)
        top.addWidget(self._search)
        top.addWidget(add_btn)
        top.addWidget(watch_btn)
        top.addWidget(edit_btn)
        top.addWidget(delete_btn)
        top.addWidget(sync_btn)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(lambda _item: self._on_edit())
        root.addLayout(top)
        root.addWidget(self._list)
        self.setCentralWidget(central)

    def _reload(self) -> None:
        self._render(self._service.list_all())

    def _on_search(self, text: str) -> None:
        self._render(self._service.search(text))

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

        since = None
        if self._settings.sync_last_synced_at:
            since = dt.datetime.fromisoformat(self._settings.sync_last_synced_at)

        assert self._settings.sync_server_url is not None
        assert self._settings.sync_device_token is not None
        assert self._settings.sync_role is not None
        try:
            result = self._sync_service.sync_now(
                self._settings.sync_server_url,
                self._settings.sync_device_token,
                self._settings.sync_role,
                since,
            )
        except SyncError as exc:
            QMessageBox.warning(self, "Ошибка синхронизации", str(exc))
            return

        self._settings.sync_last_synced_at = result.synced_at.isoformat()
        save_settings(self._settings)
        QMessageBox.information(
            self,
            "Синхронизация завершена",
            f"Отправлено: {result.pushed}\nПолучено: {result.pulled}",
        )
        self._reload()

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
