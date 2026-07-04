"""Main window. Talks ONLY to services — never to repositories/ORM/SQLite."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.schemas import EntryRead
from core.services.entry_service import EntryService


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
        add_btn.clicked.connect(self._on_quick_add)
        top.addWidget(self._search)
        top.addWidget(add_btn)

        self._list = QListWidget()
        root.addLayout(top)
        root.addWidget(self._list)
        self.setCentralWidget(central)

    def _reload(self) -> None:
        self._render(self._service.list_all())

    def _on_search(self, text: str) -> None:
        self._render(self._service.search(text))

    def _on_quick_add(self) -> None:
        text = self._search.text().strip()
        if text:
            self._service.quick_add(text)
            self._search.clear()
            self._reload()

    def _render(self, entries: list[EntryRead]) -> None:
        self._list.clear()
        for e in entries:
            fav = "★ " if e.is_favorite else ""
            self._list.addItem(QListWidgetItem(f"{fav}{e.title}  —  {e.status.value}"))
