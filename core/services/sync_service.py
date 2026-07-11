"""Client for the MediaVault sync server (see ../../sync-server and
docs/MULTIPLATFORM.md for the protocol). Bidirectional push/pull of a
shared catalog (Title) and this person's own state (UserState), each with
independent last-write-wins conflict resolution by `updated_at`, matching
the server. Only an admin device may push a catalog deletion - the server
enforces this too, but the client avoids even trying, to keep participants'
sync results easy to reason about (they never see a rejected delete).
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any, NoReturn

import requests
from sqlalchemy.orm import Session, sessionmaker

from core.repositories.entry_repository import EntryRepository
from core.schemas import ParticipantSummary, SyncResult, TitleSyncData, UserStateSyncData

log = logging.getLogger(__name__)

_EPOCH = dt.datetime(1970, 1, 1)
ADMIN_ROLE = "admin"


class SyncError(Exception):
    """Raised when the sync server can't be reached or rejects the request."""


def _naive_utc(value: dt.datetime) -> dt.datetime:
    """Normalize to naive UTC. Local SQLite timestamps are naive; the server
    may send back timezone-aware ISO strings — mixing the two raises
    TypeError on comparison, so everything is normalized at this boundary."""
    if value.tzinfo is not None:
        return value.astimezone(dt.UTC).replace(tzinfo=None)
    return value


_UNREACHABLE_MESSAGE = (
    "Сервер синхронизации сейчас недоступен. Повторите попытку позже — "
    "изменения останутся локально и синхронизируются при следующей попытке."
)


def _error_detail(exc: requests.exceptions.RequestException) -> str:
    if exc.response is not None:
        try:
            detail = exc.response.json().get("detail")
        except ValueError:
            detail = None
        if detail:
            return str(detail)
    return str(exc)


def _raise_sync_error(exc: requests.exceptions.RequestException, action: str) -> NoReturn:
    """Connection-level failures (no response at all - refused/timed out/DNS)
    get a friendly, actionable message instead of the raw exception text;
    a real HTTP error response (403/500/...) still shows its detail, since
    that's actionable in a different way (e.g. "requires admin role")."""
    if exc.response is None:
        raise SyncError(_UNREACHABLE_MESSAGE) from exc
    raise SyncError(f"Не удалось {action}: {_error_detail(exc)}") from exc


class SyncService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def register_device(
        self, server_url: str, key: str, person_name: str, label: str
    ) -> tuple[str, str]:
        """Pair this installation with the server. Returns (token, role) -
        both should be saved (e.g. in Settings.sync_device_token/sync_role)."""
        try:
            resp = requests.post(
                f"{server_url.rstrip('/')}/devices/register",
                json={"key": key, "person_name": person_name, "label": label},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            _raise_sync_error(exc, "зарегистрировать устройство")
        data = resp.json()
        token = data["token"]
        role = data["role"]
        assert isinstance(token, str)
        assert isinstance(role, str)
        return token, role

    def list_participants(self, server_url: str, token: str) -> list[ParticipantSummary]:
        """Admin-only: who's registered on the server and their devices."""
        try:
            resp = requests.get(
                f"{server_url.rstrip('/')}/admin/people",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            _raise_sync_error(exc, "получить список участников")
        return [ParticipantSummary.model_validate(item) for item in resp.json()]

    def revoke_device(self, server_url: str, token: str, device_id: int) -> None:
        """Admin-only: invalidate someone's device token immediately."""
        try:
            resp = requests.delete(
                f"{server_url.rstrip('/')}/admin/devices/{device_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            _raise_sync_error(exc, "отозвать токен")

    def sync_now(
        self, server_url: str, device_token: str, role: str, since: dt.datetime | None
    ) -> SyncResult:
        since_naive = _naive_utc(since) if since is not None else _EPOCH
        pushed = self._push(server_url, device_token, role, since_naive)
        pulled = self._pull(server_url, device_token, since_naive)
        return SyncResult(pushed=pushed, pulled=pulled, synced_at=dt.datetime.now(dt.UTC))

    def _push(self, server_url: str, token: str, role: str, since: dt.datetime) -> int:
        with self._session_factory() as session:
            repo = EntryRepository(session)
            entries = repo.changed_since(since)

            titles: list[dict[str, Any]] = []
            states: list[dict[str, Any]] = []
            for entry in entries:
                if entry.deleted_at is not None and role != ADMIN_ROLE:
                    # Participants can't delete a catalog Title - the server
                    # would reject it anyway; skip both parts for this row
                    # rather than send a request we know will be refused.
                    continue
                if entry.catalog_updated_at > since:
                    titles.append(TitleSyncData.model_validate(entry).model_dump(mode="json"))
                state = UserStateSyncData(
                    title_uuid=entry.uuid,
                    status=entry.status,
                    rating=entry.rating,
                    rating_other=entry.rating_other,
                    is_favorite=entry.is_favorite,
                    season=entry.season,
                    episode=entry.episode,
                    open_count=entry.open_count,
                    last_watched_at=entry.last_watched_at,
                    comment=entry.comment,
                    updated_at=entry.updated_at,
                )
                states.append(state.model_dump(mode="json"))

        if not titles and not states:
            return 0
        try:
            resp = requests.post(
                f"{server_url.rstrip('/')}/sync/push",
                json={"titles": titles, "states": states},
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            _raise_sync_error(exc, "отправить изменения на сервер")
        return len(titles) + len(states)

    def _pull(self, server_url: str, token: str, since: dt.datetime) -> int:
        try:
            resp = requests.get(
                f"{server_url.rstrip('/')}/sync/pull",
                params={"since": since.isoformat()},
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            _raise_sync_error(exc, "получить изменения с сервера")

        body = resp.json()
        incoming_titles = [TitleSyncData.model_validate(item) for item in body["titles"]]
        incoming_states = [UserStateSyncData.model_validate(item) for item in body["states"]]

        applied = 0
        with self._session_factory() as session:
            repo = EntryRepository(session)

            for title_data in incoming_titles:
                title_data.updated_at = _naive_utc(title_data.updated_at)
                title_data.created_at = _naive_utc(title_data.created_at)
                if title_data.deleted_at is not None:
                    title_data.deleted_at = _naive_utc(title_data.deleted_at)

                local = repo.find_by_uuid(title_data.uuid)
                if local is None and title_data.deleted_at is not None:
                    continue  # tombstone for a title we never had - nothing to do
                if local is not None and local.catalog_updated_at >= title_data.updated_at:
                    continue  # our catalog copy is newer or equal - keep it
                repo.upsert_title_from_sync(title_data)
                applied += 1

            for state_data in incoming_states:
                state_data.updated_at = _naive_utc(state_data.updated_at)
                if state_data.last_watched_at is not None:
                    state_data.last_watched_at = _naive_utc(state_data.last_watched_at)

                local = repo.find_by_uuid(state_data.title_uuid)
                if local is None:
                    continue  # no local title to attach this personal state to yet
                if local.updated_at >= state_data.updated_at:
                    continue  # our state copy is newer or equal - keep it
                repo.upsert_state_from_sync(state_data.title_uuid, state_data)
                applied += 1

            session.commit()
        return applied
