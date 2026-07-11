"""Admin-only dialog: who's registered on the sync server, and a button to
revoke a device's token. Talks only to core.services.sync_service — never
to the server directly."""
from __future__ import annotations

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

from core.services.sync_service import SyncError, SyncService

_DEVICE_ID_ROLE = Qt.ItemDataRole.UserRole


class ParticipantsDialog(QDialog):
    """Shown only when the local device is registered with the admin role -
    the server also enforces this independently on every request."""

    def __init__(
        self, parent: object, sync_service: SyncService, server_url: str, token: str
    ) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._sync_service = sync_service
        self._server_url = server_url
        self._token = token
        self.setWindowTitle("Участники")
        self.resize(480, 400)
        self._build_ui()
        self._reload()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        self._list = QListWidget()
        root.addWidget(self._list)

        buttons = QHBoxLayout()
        revoke_btn = QPushButton("Отозвать токен устройства")
        revoke_btn.clicked.connect(self._on_revoke)
        buttons.addWidget(revoke_btn)
        buttons.addStretch()
        root.addLayout(buttons)

        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        box.rejected.connect(self.reject)
        box.accepted.connect(self.accept)
        root.addWidget(box)

    def _reload(self) -> None:
        self._list.clear()
        try:
            participants = self._sync_service.list_participants(self._server_url, self._token)
        except SyncError as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            return
        for person in participants:
            header = QListWidgetItem(f"{person.name}  ({person.role})")
            header.setData(_DEVICE_ID_ROLE, None)
            header_font = header.font()
            header_font.setBold(True)
            header.setFont(header_font)
            self._list.addItem(header)
            for device in person.devices:
                item = QListWidgetItem(f"    {device.label}")
                item.setData(_DEVICE_ID_ROLE, device.device_id)
                self._list.addItem(item)

    def _on_revoke(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        device_id = item.data(_DEVICE_ID_ROLE)
        if device_id is None:
            QMessageBox.information(self, "Выбор", "Выберите устройство (не строку с именем).")
            return
        answer = QMessageBox.question(
            self, "Отозвать токен", f"Отозвать токен «{item.text().strip()}»?"
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self._sync_service.revoke_device(self._server_url, self._token, device_id)
        except SyncError as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            return
        self._reload()
