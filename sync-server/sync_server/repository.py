"""Data access for the sync server. Mirrors the desktop app's convention:
all DB access goes through a repository, no raw SQL/queries elsewhere."""
from __future__ import annotations

import datetime as dt
import secrets
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from sync_server.models import Device, Person, Title, UserState
from sync_server.schemas import TitleSync, UserStateSync


class PersonRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_name(self, name: str) -> Person | None:
        stmt = select(Person).where(Person.name == name)
        return self._session.scalars(stmt).first()

    def get_admin(self) -> Person | None:
        stmt = select(Person).where(Person.role == "admin")
        return self._session.scalars(stmt).first()

    def create(self, name: str, role: str) -> Person:
        person = Person(name=name, role=role)
        self._session.add(person)
        self._session.flush()
        return person


class DeviceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, person_id: int, label: str) -> Device:
        device = Device(person_id=person_id, token=secrets.token_urlsafe(32), label=label)
        self._session.add(device)
        self._session.flush()
        return device

    def get_by_token(self, token: str) -> Device | None:
        stmt = select(Device).where(Device.token == token)
        return self._session.scalars(stmt).first()


class TitleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, uuid: str) -> Title | None:
        return self._session.get(Title, uuid)

    def upsert(self, data: TitleSync) -> Title:
        title = self.get(data.uuid)
        if title is None:
            title = Title(uuid=data.uuid)
            self._session.add(title)
        title.type = data.type
        title.title = data.title
        title.original_title = data.original_title
        title.year = data.year
        title.url = data.url
        title.description = data.description
        title.created_at = data.created_at
        title.updated_at = data.updated_at
        title.deleted_at = data.deleted_at
        self._session.flush()
        return title

    def changed_since(self, since: dt.datetime) -> Sequence[Title]:
        stmt = select(Title).where(Title.updated_at > since)
        return self._session.scalars(stmt).all()


class UserStateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, title_uuid: str, person_id: int) -> UserState | None:
        stmt = select(UserState).where(
            UserState.title_uuid == title_uuid, UserState.person_id == person_id
        )
        return self._session.scalars(stmt).first()

    def upsert(self, person_id: int, data: UserStateSync) -> UserState:
        state = self.get(data.title_uuid, person_id)
        if state is None:
            state = UserState(title_uuid=data.title_uuid, person_id=person_id)
            self._session.add(state)
        state.status = data.status
        state.rating = data.rating
        state.rating_other = data.rating_other
        state.is_favorite = data.is_favorite
        state.season = data.season
        state.episode = data.episode
        state.open_count = data.open_count
        state.last_watched_at = data.last_watched_at
        state.comment = data.comment
        state.updated_at = data.updated_at
        self._session.flush()
        return state

    def changed_since(self, person_id: int, since: dt.datetime) -> Sequence[UserState]:
        stmt = select(UserState).where(
            UserState.person_id == person_id, UserState.updated_at > since
        )
        return self._session.scalars(stmt).all()
