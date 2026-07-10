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
from core.schemas import TitleSyncData, UserStateSyncData

# Sentinel for a freshly-synced Title with no personal state applied yet -
# guarantees the first incoming UserState always looks newer, regardless of
# how it compares to the Title's own timestamp.
_NO_STATE_YET = dt.datetime(1970, 1, 1)


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
        deletion is visible to other devices on their next sync pull.
        Deletion is a catalog-level fact, so it also bumps catalog_updated_at
        (only actually pushed upstream by an admin device, see sync_service)."""
        now = dt.datetime.now(dt.UTC)
        entry.deleted_at = now
        entry.catalog_updated_at = now

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

    def upsert_title_from_sync(self, data: TitleSyncData) -> Entry:
        """Apply an incoming catalog record from the sync server: update the
        local row's catalog fields, or create one (with default personal
        state) if this device has never seen this title before.

        Caller is responsible for the last-write-wins timestamp check before
        calling this - it always applies unconditionally. Personal fields
        (status/rating/...) are left untouched - see upsert_state_from_sync.
        """
        entry = self.find_by_uuid(data.uuid)
        if entry is None:
            # updated_at defaults to "now" otherwise, which would look
            # newer than a state pulled in the same round (its own
            # updated_at reflects whenever it was actually set on another
            # device) and get incorrectly skipped as "already up to date".
            entry = Entry(uuid=data.uuid, updated_at=_NO_STATE_YET)
            self._session.add(entry)
        entry.type = data.type
        entry.title = data.title
        entry.original_title = data.original_title
        entry.year = data.year
        entry.url = data.url
        entry.description = data.description
        entry.created_at = data.created_at
        entry.catalog_updated_at = data.updated_at
        entry.deleted_at = data.deleted_at
        self._session.flush()
        return entry

    def upsert_state_from_sync(self, title_uuid: str, data: UserStateSyncData) -> Entry | None:
        """Apply this device's own incoming personal state. Returns None if
        we don't have a local row for this title yet (nothing to attach the
        state to - the matching Title should already have arrived first)."""
        entry = self.find_by_uuid(title_uuid)
        if entry is None:
            return None
        entry.status = data.status
        entry.rating = data.rating
        entry.rating_other = data.rating_other
        entry.is_favorite = data.is_favorite
        entry.season = data.season
        entry.episode = data.episode
        entry.open_count = data.open_count
        entry.last_watched_at = data.last_watched_at
        entry.comment = data.comment
        entry.updated_at = data.updated_at
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
