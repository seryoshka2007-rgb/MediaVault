"""Runs a sync round-trip off the GUI thread, so a slow/unreachable server
never freezes the window. GUI-layer concern (QThread) - still calls only
into core/services/sync_service.py, never repositories/ORM directly.
"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import QObject, QThread, Signal

from core.schemas import SyncResult
from core.services.sync_service import SyncError, SyncService


class SyncWorker(QThread):
    succeeded = Signal(SyncResult)
    failed = Signal(str)

    def __init__(
        self,
        sync_service: SyncService,
        server_url: str,
        token: str,
        role: str,
        since: dt.datetime | None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._sync_service = sync_service
        self._server_url = server_url
        self._token = token
        self._role = role
        self._since = since

    def run(self) -> None:
        try:
            result = self._sync_service.sync_now(
                self._server_url, self._token, self._role, self._since
            )
        except SyncError as exc:
            self.failed.emit(str(exc))
            return
        self.succeeded.emit(result)
