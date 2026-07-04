"""Data access for the sync server. Mirrors the desktop app's convention:
all DB access goes through a repository, no raw SQL/queries elsewhere."""
from __future__ import annotations

import datetime as dt
import secrets
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from sync_server.models import Device, SyncEntry


class DeviceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, label: str) -> Device:
        device = Device(token=secrets.token_urlsafe(32), label=label)
        self._session.add(device)
        self._session.flush()
        return device

    def get_by_token(self, token: str) -> Device | None:
        stmt = select(Device).where(Device.token == token)
        return self._session.scalars(stmt).first()


class SyncEntryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, uuid: str) -> SyncEntry | None:
        return self._session.get(SyncEntry, uuid)

    def upsert(self, entry: SyncEntry) -> None:
        self._session.merge(entry)

    def changed_since(self, since: dt.datetime) -> Sequence[SyncEntry]:
        stmt = select(SyncEntry).where(SyncEntry.updated_at > since)
        return self._session.scalars(stmt).all()
