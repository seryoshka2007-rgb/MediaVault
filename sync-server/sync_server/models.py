"""ORM models for the sync server.

``SyncEntry`` mirrors the desktop app's ``Entry`` (see
``core/models/entry.py`` in the main project), but is keyed by a
client-generated ``uuid`` instead of a local autoincrement id, since the
same integer id means different things on different devices. ``deleted_at``
makes deletions visible to other devices on their next pull (a hard DELETE
would be invisible to sync).
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from sync_server.database import Base


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class Device(Base):
    """A paired client device, identified by its own bearer token."""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)


class SyncEntry(Base):
    """Server-side mirror of one library entry, keyed by client uuid."""

    __tablename__ = "sync_entries"

    uuid: Mapped[str] = mapped_column(String(36), primary_key=True)
    type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(500))
    original_title: Mapped[str | None] = mapped_column(String(500), default=None)
    status: Mapped[str] = mapped_column(String(20))
    rating: Mapped[int | None] = mapped_column(Integer, default=None)
    rating_other: Mapped[int | None] = mapped_column(Integer, default=None)
    year: Mapped[int | None] = mapped_column(Integer, default=None)
    url: Mapped[str | None] = mapped_column(String(2000), default=None)
    open_count: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    comment: Mapped[str | None] = mapped_column(Text, default=None)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    season: Mapped[int | None] = mapped_column(Integer, default=None)
    episode: Mapped[int | None] = mapped_column(Integer, default=None)
    last_watched_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=None)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, index=True)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=None)
