"""Backup browsing + restore (ROADMAP: backup restore screen). BackupService
already does everything needed (create/list/restore, all via SQLite's
backup API) - this dialog is just a GUI window onto it.

Restore takes effect only after the app is restarted - see
BackupService.restore's docstring for why (this process's already-open
engine/connections keep referencing pre-restore state otherwise).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.services.backup_service import BackupService

_PATH_ROLE = Qt.ItemDataRole.UserRole


class BackupsDialog(QDialog):
    def __init__(self, parent: object, backup_service: BackupService) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._backup_service = backup_service
        self.setWindowTitle("Резервные копии")
        self.resize(480, 400)
        self._build_ui()
        self._reload()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        self._list = QListWidget()
        root.addWidget(self._list)

        buttons = QHBoxLayout()
        create_btn = QPushButton("Создать сейчас")
        create_btn.clicked.connect(self._on_create)
        restore_btn = QPushButton("Восстановить выбранную")
        restore_btn.clicked.connect(self._on_restore)
        buttons.addWidget(create_btn)
        buttons.addWidget(restore_btn)
        buttons.addStretch()
        root.addLayout(buttons)

        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        box.rejected.connect(self.reject)
        box.accepted.connect(self.accept)
        root.addWidget(box)

    def _reload(self) -> None:
        self._list.clear()
        for path in self._backup_service.list_backups():
            mtime = dt.datetime.fromtimestamp(path.stat().st_mtime)
            item = QListWidgetItem(f"{path.name}  ({mtime:%Y-%m-%d %H:%M:%S})")
            item.setData(_PATH_ROLE, str(path))
            self._list.addItem(item)

    def _on_create(self) -> None:
        self._backup_service.create(reason="manual")
        self._reload()
        QMessageBox.information(self, "Готово", "Резервная копия создана.")

    def _on_restore(self) -> None:
        item = self._list.currentItem()
        if item is None:
            QMessageBox.information(self, "Выбор", "Выберите резервную копию из списка.")
            return
        answer = QMessageBox.question(
            self,
            "Восстановить",
            "Текущие данные будут заменены выбранной резервной копией "
            "(текущее состояние тоже сохранится в отдельный бэкап перед этим).\n"
            "Изменения вступят в силу после перезапуска приложения. Продолжить?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._backup_service.restore(Path(item.data(_PATH_ROLE)))
        QMessageBox.information(
            self,
            "Восстановлено",
            "Готово. Перезапустите приложение, чтобы увидеть восстановленные данные.",
        )
        self.accept()
