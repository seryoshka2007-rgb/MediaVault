"""Sync business logic: last-write-wins conflict resolution by updated_at.

See docs/MULTIPLATFORM.md for why this is deliberately simple (whole-record
LWW, not per-field merge or CRDT) - this serves one person's library across
their own devices, not multi-user collaboration.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session, sessionmaker

from sync_server.models import Device, SyncEntry
from sync_server.repository import DeviceRepository, SyncEntryRepository
from sync_server.schemas import (
    EntrySync,
    PullResponse,
    PushResult,
    RegisterDeviceResponse,
)


def _naive_utc(value: dt.datetime) -> dt.datetime:
    """Normalize to naive UTC so stored/compared timestamps are consistent.

    SQLite stores plain (naive) datetimes; incoming JSON payloads may carry
    a timezone offset. Mixing the two raises TypeError on comparison, so
    everything gets normalized to naive UTC at the service boundary. All
    sync timestamps are UTC by convention, offset or not.
    """
    if value.tzinfo is not None:
        return value.astimezone(dt.UTC).replace(tzinfo=None)
    return value


class SyncService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def register_device(self, label: str) -> RegisterDeviceResponse:
        with self._session_factory() as session:
            device = DeviceRepository(session).create(label)
            session.commit()
            return RegisterDeviceResponse(device_id=device.id, token=device.token)

    def authenticate(self, token: str) -> Device | None:
        with self._session_factory() as session:
            return DeviceRepository(session).get_by_token(token)

    def push(self, entries: list[EntrySync]) -> list[PushResult]:
        results: list[PushResult] = []
        with self._session_factory() as session:
            repo = SyncEntryRepository(session)
            for incoming in entries:
                existing = repo.get(incoming.uuid)
                incoming_updated = _naive_utc(incoming.updated_at)
                if existing is not None and existing.updated_at >= incoming_updated:
                    results.append(PushResult(uuid=incoming.uuid, applied=False))
                    continue
                data = incoming.model_dump()
                data["updated_at"] = incoming_updated
                data["created_at"] = _naive_utc(incoming.created_at)
                data["deleted_at"] = (
                    _naive_utc(incoming.deleted_at) if incoming.deleted_at else None
                )
                data["last_watched_at"] = (
                    _naive_utc(incoming.last_watched_at) if incoming.last_watched_at else None
                )
                repo.upsert(SyncEntry(**data))
                results.append(PushResult(uuid=incoming.uuid, applied=True))
            session.commit()
        return results

    def pull(self, since: dt.datetime) -> PullResponse:
        since_naive = _naive_utc(since)
        with self._session_factory() as session:
            rows = SyncEntryRepository(session).changed_since(since_naive)
            entries = [EntrySync.model_validate(r) for r in rows]
        return PullResponse(entries=entries, server_time=dt.datetime.now(dt.UTC))
