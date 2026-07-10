"""Data access for Entry. All DB access goes through repositories — no raw SQL,
no SQLAlchemy calls anywhere else in the codebase.
"""
from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from core.enums import EntryType, Status
from core.models.entry import Entry
from core.schemas import EntrySyncData


class EntryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entry: Entry) -> Entry:
        self._session.add(entry)
        self._session.flush()  # assign PK without committing
        return entry

    def get(self, entry_id: int) -> Entry | None:
        entry = self._session.get(Entry, entry_id)
        return entry if entry is not None and entry.deleted_at is None else None

    def delete(self, entry: Entry) -> None:
        """Soft-delete: mark as deleted rather than removing the row, so the
        deletion is visible to other devices on their next sync pull."""
        entry.deleted_at = dt.datetime.now(dt.UTC)

    def find_by_uuid(self, uuid: str) -> Entry | None:
        """Look up by sync uuid, including soft-deleted rows (needed to apply
        an incoming tombstone from another device)."""
        stmt = select(Entry).where(Entry.uuid == uuid)
        return self._session.scalars(stmt).first()

    def changed_since(self, since: dt.datetime) -> Sequence[Entry]:
        """Entries touched after `since`, including soft-deleted ones - a sync
        push must carry tombstones too, not just live rows."""
        stmt = select(Entry).where(Entry.updated_at > since)
        return self._session.scalars(stmt).all()

    def upsert_from_sync(self, data: EntrySyncData) -> Entry:
        """Apply an incoming record from another device: update the local row
        matching `data.uuid`, or create one if this device has never seen it.

        Caller is responsible for the last-write-wins timestamp check before
        calling this - it always applies unconditionally.
        """
        entry = self.find_by_uuid(data.uuid)
        if entry is None:
            entry = Entry(uuid=data.uuid)
            self._session.add(entry)
        entry.type = data.type
        entry.title = data.title
        entry.original_title = data.original_title
        entry.status = data.status
        entry.rating = data.rating
        entry.rating_other = data.rating_other
        entry.year = data.year
        entry.url = data.url
        entry.open_count = data.open_count
        entry.description = data.description
        entry.comment = data.comment
        entry.is_favorite = data.is_favorite
        entry.season = data.season
        entry.episode = data.episode
        entry.last_watched_at = data.last_watched_at
        entry.created_at = data.created_at
        entry.updated_at = data.updated_at
        entry.deleted_at = data.deleted_at
        self._session.flush()
        return entry

    def find_duplicate(
        self, *, url: str | None, title: str, entry_type: EntryType
    ) -> Entry | None:
        """Look up an existing entry matching by url (if given) or by title+type."""
        if url:
            stmt = select(Entry).where(Entry.url == url, Entry.deleted_at.is_(None))
        else:
            stmt = select(Entry).where(
                Entry.title.ilike(title),
                Entry.type == entry_type,
                Entry.deleted_at.is_(None),
            )
        return self._session.scalars(stmt).first()

    def list_all(self) -> Sequence[Entry]:
        stmt = (
            select(Entry)
            .where(Entry.deleted_at.is_(None))
            .order_by(Entry.updated_at.desc())
        )
        return self._session.scalars(stmt).all()

    def search(
        self,
        query: str = "",
        *,
        status: Status | None = None,
        favorites_only: bool = False,
    ) -> Sequence[Entry]:
        """Parameterized search across title/description/comment/url + filters."""
        stmt = select(Entry).where(Entry.deleted_at.is_(None))
        if query:
            like = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Entry.title.ilike(like),
                    Entry.original_title.ilike(like),
                    Entry.description.ilike(like),
                    Entry.comment.ilike(like),
                    Entry.url.ilike(like),
                )
            )
        if status is not None:
            stmt = stmt.where(Entry.status == status)
        if favorites_only:
            stmt = stmt.where(Entry.is_favorite.is_(True))
        stmt = stmt.order_by(Entry.updated_at.desc())
        return self._session.scalars(stmt).all()
