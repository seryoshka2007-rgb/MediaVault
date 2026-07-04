"""Data access for Entry. All DB access goes through repositories — no raw SQL,
no SQLAlchemy calls anywhere else in the codebase.
"""
from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from core.enums import Status
from core.models.entry import Entry


class EntryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entry: Entry) -> Entry:
        self._session.add(entry)
        self._session.flush()  # assign PK without committing
        return entry

    def get(self, entry_id: int) -> Entry | None:
        return self._session.get(Entry, entry_id)

    def delete(self, entry: Entry) -> None:
        self._session.delete(entry)

    def list_all(self) -> Sequence[Entry]:
        stmt = select(Entry).order_by(Entry.updated_at.desc())
        return self._session.scalars(stmt).all()

    def search(
        self,
        query: str = "",
        *,
        status: Status | None = None,
        favorites_only: bool = False,
    ) -> Sequence[Entry]:
        """Parameterized search across title/description/comment/url + filters."""
        stmt = select(Entry)
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
