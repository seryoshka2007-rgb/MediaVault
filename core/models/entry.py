"""ORM model for a media library entry."""
from __future__ import annotations

import datetime as dt

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
    type: Mapped[EntryType] = mapped_column(SAEnum(EntryType), index=True)

    title: Mapped[str] = mapped_column(String(500), index=True)
    original_title: Mapped[str | None] = mapped_column(String(500), default=None)

    status: Mapped[Status] = mapped_column(
        SAEnum(Status), default=Status.PLANNED, index=True
    )
    rating: Mapped[int | None] = mapped_column(Integer, default=None)  # 0..10
    url: Mapped[str | None] = mapped_column(String(2000), default=None)
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

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Entry id={self.id} type={self.type.value!r} title={self.title!r}>"
