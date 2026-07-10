"""Sync business logic: shared catalog (Title) + per-person state (UserState),
last-write-wins by updated_at within each entity independently.

See docs/MULTIPLATFORM.md for why this split exists: several people can use
one server, but a status/rating is personal and must never be overwritten
by someone else's sync. Only an admin Person may delete a catalog Title -
participants can add and edit, never delete, enforced here (not just hidden
in a client UI).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from sync_server.config import admin_key, participant_key
from sync_server.models import Person
from sync_server.repository import (
    DeviceRepository,
    PersonRepository,
    TitleRepository,
    UserStateRepository,
)
from sync_server.schemas import (
    PullResponse,
    PushResult,
    RegisterResponse,
    TitleSync,
    UserStateSync,
)

ADMIN_ROLE = "admin"
PARTICIPANT_ROLE = "participant"


def _naive_utc(value: dt.datetime) -> dt.datetime:
    """Normalize to naive UTC so stored/compared timestamps are consistent.

    SQLite stores plain (naive) datetimes; incoming JSON payloads may carry
    a timezone offset. Mixing the two raises TypeError on comparison, so
    everything gets normalized at the service boundary. All sync timestamps
    are UTC by convention, offset or not.
    """
    if value.tzinfo is not None:
        return value.astimezone(dt.UTC).replace(tzinfo=None)
    return value


class SyncAuthError(Exception):
    """Invalid key or unknown token."""


class SyncPermissionError(Exception):
    """Authenticated, but not allowed to do this (e.g. reusing the admin's name)."""


@dataclass(frozen=True)
class AuthenticatedDevice:
    """Plain result of authenticate() - never a live ORM object, since the
    session that loaded it closes before the caller uses this."""

    device_id: int
    person_id: int
    person_name: str
    role: str


class SyncService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def register(self, key: str, person_name: str, label: str) -> RegisterResponse:
        with self._session_factory() as session:
            people = PersonRepository(session)

            if key == admin_key():
                person = people.get_admin()
                if person is None:
                    person = people.create(person_name, ADMIN_ROLE)
                # Further admin registrations always reuse the one admin
                # Person, regardless of the name typed this time.
            elif participant_key() is not None and key == participant_key():
                person = people.get_by_name(person_name)
                if person is None:
                    person = people.create(person_name, PARTICIPANT_ROLE)
                elif person.role == ADMIN_ROLE:
                    raise SyncPermissionError("this name is reserved for the admin")
            else:
                raise SyncAuthError("invalid key")

            device = DeviceRepository(session).create(person.id, label)
            session.commit()
            return RegisterResponse(
                device_id=device.id,
                token=device.token,
                person_name=person.name,
                role=person.role,
            )

    def authenticate(self, token: str) -> AuthenticatedDevice | None:
        with self._session_factory() as session:
            device = DeviceRepository(session).get_by_token(token)
            if device is None:
                return None
            person = session.get(Person, device.person_id)
            if person is None:
                return None
            return AuthenticatedDevice(
                device_id=device.id,
                person_id=person.id,
                person_name=person.name,
                role=person.role,
            )

    def push(
        self, auth: AuthenticatedDevice, titles: list[TitleSync], states: list[UserStateSync]
    ) -> tuple[list[PushResult], list[PushResult]]:
        title_results: list[PushResult] = []
        state_results: list[PushResult] = []
        with self._session_factory() as session:
            title_repo = TitleRepository(session)
            state_repo = UserStateRepository(session)

            for incoming in titles:
                incoming.updated_at = _naive_utc(incoming.updated_at)
                incoming.created_at = _naive_utc(incoming.created_at)
                if incoming.deleted_at is not None:
                    incoming.deleted_at = _naive_utc(incoming.deleted_at)

                if incoming.deleted_at is not None and auth.role != ADMIN_ROLE:
                    title_results.append(
                        PushResult(
                            key=incoming.uuid, applied=False, reason="requires admin role"
                        )
                    )
                    continue
                existing = title_repo.get(incoming.uuid)
                if existing is not None and existing.updated_at >= incoming.updated_at:
                    title_results.append(PushResult(key=incoming.uuid, applied=False))
                    continue
                title_repo.upsert(incoming)
                title_results.append(PushResult(key=incoming.uuid, applied=True))

            for incoming_state in states:
                incoming_state.updated_at = _naive_utc(incoming_state.updated_at)
                if incoming_state.last_watched_at is not None:
                    incoming_state.last_watched_at = _naive_utc(incoming_state.last_watched_at)

                existing_state = state_repo.get(incoming_state.title_uuid, auth.person_id)
                is_stale = (
                    existing_state is not None
                    and existing_state.updated_at >= incoming_state.updated_at
                )
                if is_stale:
                    state_results.append(
                        PushResult(key=incoming_state.title_uuid, applied=False)
                    )
                    continue
                state_repo.upsert(auth.person_id, incoming_state)
                state_results.append(PushResult(key=incoming_state.title_uuid, applied=True))

            session.commit()
        return title_results, state_results

    def pull(self, auth: AuthenticatedDevice, since: dt.datetime) -> PullResponse:
        since_naive = _naive_utc(since)
        with self._session_factory() as session:
            titles = TitleRepository(session).changed_since(since_naive)
            states = UserStateRepository(session).changed_since(auth.person_id, since_naive)
            title_syncs = [TitleSync.model_validate(t) for t in titles]
            state_syncs = [UserStateSync.model_validate(s) for s in states]
        return PullResponse(
            titles=title_syncs, states=state_syncs, server_time=dt.datetime.now(dt.UTC)
        )
