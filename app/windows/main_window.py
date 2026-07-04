"""Main window. Talks ONLY to services — never to repositories/ORM/SQLite."""
from __future__ import annotations

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
from core.enums import STATUS_LABELS_RU
from core.schemas import EntryRead
from core.services.entry_service import EntryService
from core.validators.url_validator import is_valid_url

_ENTRY_ID_ROLE = Qt.ItemDataRole.UserRole


class MainWindow(QMainWindow):
    def __init__(self, entry_service: EntryService) -> None:
        super().__init__()
        self._service = entry_service
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
        top.addWidget(self._search)
        top.addWidget(add_btn)
        top.addWidget(watch_btn)
        top.addWidget(edit_btn)
        top.addWidget(delete_btn)

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
