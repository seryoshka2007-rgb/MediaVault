"""ORM models for the sync server.

Split into a shared catalog (``Title``) and per-person state
(``UserState``), instead of one flat row per entry: several people can use
the same server, and one person's watch status/rating must never overwrite
another's. ``Title`` mirrors the catalog-ish fields of the desktop app's
``Entry`` (see ``core/models/entry.py``); ``UserState`` mirrors the
personal fields, scoped to a ``Person``.

Both are keyed by client-generated ``uuid``/composite identity rather than
local autoincrement ids, since the same integer id means different things
on different devices. ``deleted_at`` on ``Title`` makes catalog deletions
visible to other devices on their next pull (a hard DELETE would be
invisible to sync) - but per the sync-server's permission rules (see
service.py), only an admin Person's push may set it.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from sync_server.database import Base


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class Person(Base):
    """A human using the server - possibly across several devices, which
    all share this one Person's personal state (status/rating/...)."""

    __tablename__ = "people"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20))  # "admin" | "participant"
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)


class Device(Base):
    """A paired client device, identified by its own bearer token. Belongs
    to exactly one Person; several devices may belong to the same Person."""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)


class Title(Base):
    """Shared catalog entry - the same movie/series as seen by everyone on
    this server. No personal fields here (see UserState)."""

    __tablename__ = "titles"

    uuid: Mapped[str] = mapped_column(String(36), primary_key=True)
    type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(500))
    original_title: Mapped[str | None] = mapped_column(String(500), default=None)
    year: Mapped[int | None] = mapped_column(Integer, default=None)
    url: Mapped[str | None] = mapped_column(String(2000), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, index=True)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=None)


class UserState(Base):
    """One person's personal relationship to one Title - status, rating,
    favorite, series progress. Never shared with other people."""

    __tablename__ = "user_states"
    __table_args__ = (UniqueConstraint("title_uuid", "person_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title_uuid: Mapped[str] = mapped_column(ForeignKey("titles.uuid"), index=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), index=True)

    status: Mapped[str] = mapped_column(String(20))
    rating: Mapped[int | None] = mapped_column(Integer, default=None)
    rating_other: Mapped[int | None] = mapped_column(Integer, default=None)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    season: Mapped[int | None] = mapped_column(Integer, default=None)
    episode: Mapped[int | None] = mapped_column(Integer, default=None)
    open_count: Mapped[int] = mapped_column(Integer, default=0)
    last_watched_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=None)
    comment: Mapped[str | None] = mapped_column(Text, default=None)

    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, index=True)
