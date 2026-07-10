"""Client for the MediaVault sync server (see ../../sync-server and
docs/MULTIPLATFORM.md for the protocol). Bidirectional push/pull with
last-write-wins conflict resolution by `updated_at`, matching the server.
"""
from __future__ import annotations

import datetime as dt
import logging

import requests
from sqlalchemy.orm import Session, sessionmaker

from core.repositories.entry_repository import EntryRepository
from core.schemas import EntrySyncData, SyncResult

log = logging.getLogger(__name__)

_EPOCH = dt.datetime(1970, 1, 1)


class SyncError(Exception):
    """Raised when the sync server can't be reached or rejects the request."""


def _naive_utc(value: dt.datetime) -> dt.datetime:
    """Normalize to naive UTC. Local SQLite timestamps are naive; the server
    may send back timezone-aware ISO strings — mixing the two raises
    TypeError on comparison, so everything is normalized at this boundary."""
    if value.tzinfo is not None:
        return value.astimezone(dt.UTC).replace(tzinfo=None)
    return value


class SyncService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def register_device(self, server_url: str, setup_key: str, label: str) -> str:
        """Pair this installation with the server. Returns the device token
        to save (e.g. in Settings.sync_device_token)."""
        try:
            resp = requests.post(
                f"{server_url.rstrip('/')}/devices/register",
                json={"setup_key": setup_key, "label": label},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise SyncError(f"Не удалось зарегистрировать устройство: {exc}") from exc
        token = resp.json()["token"]
        assert isinstance(token, str)
        return token

    def sync_now(
        self, server_url: str, device_token: str, since: dt.datetime | None
    ) -> SyncResult:
        since_naive = _naive_utc(since) if since is not None else _EPOCH
        pushed = self._push(server_url, device_token, since_naive)
        pulled = self._pull(server_url, device_token, since_naive)
        return SyncResult(pushed=pushed, pulled=pulled, synced_at=dt.datetime.now(dt.UTC))

    def _push(self, server_url: str, token: str, since: dt.datetime) -> int:
        with self._session_factory() as session:
            repo = EntryRepository(session)
            entries = repo.changed_since(since)
            payload = [
                EntrySyncData.model_validate(e).model_dump(mode="json") for e in entries
            ]
        if not payload:
            return 0
        try:
            resp = requests.post(
                f"{server_url.rstrip('/')}/sync/push",
                json={"entries": payload},
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise SyncError(f"Не удалось отправить изменения на сервер: {exc}") from exc
        return len(payload)

    def _pull(self, server_url: str, token: str, since: dt.datetime) -> int:
        try:
            resp = requests.get(
                f"{server_url.rstrip('/')}/sync/pull",
                params={"since": since.isoformat()},
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise SyncError(f"Не удалось получить изменения с сервера: {exc}") from exc

        incoming = [
            EntrySyncData.model_validate(item) for item in resp.json()["entries"]
        ]
        applied = 0
        with self._session_factory() as session:
            repo = EntryRepository(session)
            for data in incoming:
                data.updated_at = _naive_utc(data.updated_at)
                data.created_at = _naive_utc(data.created_at)
                if data.last_watched_at is not None:
                    data.last_watched_at = _naive_utc(data.last_watched_at)
                if data.deleted_at is not None:
                    data.deleted_at = _naive_utc(data.deleted_at)

                local = repo.find_by_uuid(data.uuid)
                if local is None and data.deleted_at is not None:
                    continue  # tombstone for something we never had - nothing to do
                if local is not None and local.updated_at >= data.updated_at:
                    continue  # local copy is newer or equal - keep it

                repo.upsert_from_sync(data)
                applied += 1
            session.commit()
        return applied
