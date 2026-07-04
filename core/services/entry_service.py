"""Business logic for entries. The GUI calls ONLY services (never repos/ORM/DB)."""
from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy.orm import Session, sessionmaker

from core.enums import EntryType, Status
from core.models.entry import Entry
from core.repositories.entry_repository import EntryRepository
from core.schemas import EntryCreate, EntryRead, EntryUpdate

log = logging.getLogger(__name__)


class EntryService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # -- create ---------------------------------------------------------------
    def create(self, data: EntryCreate) -> EntryRead:
        with self._session_factory() as session:
            repo = EntryRepository(session)
            entry = Entry(
                type=data.type,
                title=data.title,
                original_title=data.original_title,
                status=data.status,
                rating=data.rating,
                rating_other=data.rating_other,
                year=data.year,
                url=data.url,
                description=data.description,
                comment=data.comment,
                is_favorite=data.is_favorite,
                season=data.season,
                episode=data.episode,
            )
            repo.add(entry)
            session.commit()
            log.info("Created entry id=%s title=%r", entry.id, entry.title)
            return EntryRead.model_validate(entry)

    def quick_add(self, title: str) -> EntryRead:
        """Быстрое добавление: только название."""
        return self.create(EntryCreate(title=title, type=EntryType.MOVIE))

    def find_duplicate(
        self, *, title: str, entry_type: EntryType, url: str | None
    ) -> EntryRead | None:
        """Check whether an entry matching this url (or title+type) already exists."""
        with self._session_factory() as session:
            entry = EntryRepository(session).find_duplicate(
                url=url, title=title, entry_type=entry_type
            )
            return EntryRead.model_validate(entry) if entry else None

    # -- read -----------------------------------------------------------------
    def get(self, entry_id: int) -> EntryRead | None:
        with self._session_factory() as session:
            entry = EntryRepository(session).get(entry_id)
            return EntryRead.model_validate(entry) if entry else None

    def list_all(self) -> list[EntryRead]:
        with self._session_factory() as session:
            rows = EntryRepository(session).list_all()
            return [EntryRead.model_validate(r) for r in rows]

    def search(
        self, query: str = "", *, status: Status | None = None,
        favorites_only: bool = False,
    ) -> list[EntryRead]:
        with self._session_factory() as session:
            rows = EntryRepository(session).search(
                query, status=status, favorites_only=favorites_only
            )
            return [EntryRead.model_validate(r) for r in rows]

    # -- update ---------------------------------------------------------------
    def update(self, entry_id: int, data: EntryUpdate) -> EntryRead | None:
        with self._session_factory() as session:
            repo = EntryRepository(session)
            entry = repo.get(entry_id)
            if entry is None:
                return None
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(entry, field, value)
            session.commit()
            return EntryRead.model_validate(entry)

    # -- delete ---------------------------------------------------------------
    def delete(self, entry_id: int) -> bool:
        with self._session_factory() as session:
            repo = EntryRepository(session)
            entry = repo.get(entry_id)
            if entry is None:
                return False
            repo.delete(entry)
            session.commit()
            log.info("Deleted entry id=%s", entry_id)
            return True

    # -- watch -------------------------------------------------------------
    def mark_opened(self, entry_id: int) -> EntryRead | None:
        """Bump the open-link counter (called when the user follows the URL)."""
        with self._session_factory() as session:
            entry = EntryRepository(session).get(entry_id)
            if entry is None:
                return None
            entry.open_count += 1
            session.commit()
            return EntryRead.model_validate(entry)

    # -- series navigation ----------------------------------------------------
    def next_episode(self, entry_id: int) -> EntryRead | None:
        return self._shift_episode(entry_id, +1)

    def prev_episode(self, entry_id: int) -> EntryRead | None:
        return self._shift_episode(entry_id, -1)

    def _shift_episode(self, entry_id: int, delta: int) -> EntryRead | None:
        with self._session_factory() as session:
            entry = EntryRepository(session).get(entry_id)
            if entry is None or not entry.type.is_episodic:
                return None
            entry.episode = max(1, (entry.episode or 1) + delta)
            entry.last_watched_at = dt.datetime.now(dt.UTC)
            if entry.status == Status.PLANNED:
                entry.status = Status.WATCHING
            session.commit()
            return EntryRead.model_validate(entry)
