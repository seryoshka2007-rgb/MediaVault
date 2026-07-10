"""ORM model for a media library entry."""
from __future__ import annotations

import datetime as dt
import uuid as uuid_module

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from core.enums import EntryType, Status
from core.models.base import Base


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class Entry(Base):
    """A single item in the media library (movie, series, ...)."""

    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, default=lambda: str(uuid_module.uuid4())
    )
    type: Mapped[EntryType] = mapped_column(SAEnum(EntryType), index=True)

    title: Mapped[str] = mapped_column(String(500), index=True)
    original_title: Mapped[str | None] = mapped_column(String(500), default=None)

    status: Mapped[Status] = mapped_column(
        SAEnum(Status), default=Status.PLANNED, index=True
    )
    rating: Mapped[int | None] = mapped_column(Integer, default=None)  # 0..10
    rating_other: Mapped[int | None] = mapped_column(Integer, default=None)  # 0..10
    year: Mapped[int | None] = mapped_column(Integer, default=None)
    url: Mapped[str | None] = mapped_column(String(2000), default=None)
    open_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    description: Mapped[str | None] = mapped_column(Text, default=None)
    comment: Mapped[str | None] = mapped_column(Text, default=None)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Episodic fields (NULL for non-episodic types).
    season: Mapped[int | None] = mapped_column(Integer, default=None)
    episode: Mapped[int | None] = mapped_column(Integer, default=None)
    last_watched_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime, default=None
    )

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime, default=None)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Entry id={self.id} type={self.type.value!r} title={self.title!r}>"
