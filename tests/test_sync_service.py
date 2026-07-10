"""SyncService push/pull, with requests mocked - no real network involved."""
from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
import requests

from core.enums import Status
from core.schemas import EntryCreate, EntryUpdate
from core.services.entry_service import EntryService
from core.services.sync_service import SyncError, SyncService


class _FakeResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(str(self.status_code))


def _empty_pull(*a: Any, **kw: Any) -> _FakeResponse:  # noqa: ANN401
    return _FakeResponse({"titles": [], "states": []})


def test_register_device_returns_token_and_role(
    sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, json: dict[str, Any], timeout: int) -> _FakeResponse:
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse({"device_id": 1, "token": "abc123", "role": "participant"})

    monkeypatch.setattr(requests, "post", fake_post)
    token, role = sync_service.register_device(
        "http://server:8000", "participant-key", "Alice", "My PC"
    )

    assert (token, role) == ("abc123", "participant")
    assert captured["url"] == "http://server:8000/devices/register"
    assert captured["json"] == {
        "key": "participant-key",
        "person_name": "Alice",
        "label": "My PC",
    }


def test_register_device_network_error_raises_sync_error(
    sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_post(*a: Any, **kw: Any) -> _FakeResponse:  # noqa: ANN401
        raise requests.exceptions.ConnectionError("refused")

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(SyncError):
        sync_service.register_device("http://server:8000", "key", "Alice", "PC")


def test_push_sends_title_and_state_for_new_entry(
    service: EntryService, sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    service.create(EntryCreate(title="Dune"))
    captured: dict[str, Any] = {}

    def fake_post(
        url: str, json: dict[str, Any], headers: dict[str, str], timeout: int
    ) -> _FakeResponse:
        captured["json"] = json
        captured["headers"] = headers
        return _FakeResponse({"title_results": [], "state_results": []})

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "get", _empty_pull)

    result = sync_service.sync_now("http://server:8000", "tok", "admin", since=None)

    assert result.pushed == 2  # one title + one state
    assert captured["headers"]["Authorization"] == "Bearer tok"
    assert captured["json"]["titles"][0]["title"] == "Dune"
    assert captured["json"]["states"][0]["status"] == "planned"


def test_push_participant_skips_deleted_entry_entirely(
    service: EntryService, sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A participant's local delete never even attempts to push the
    deletion - there's nothing else to push either, so no POST happens."""
    entry = service.create(EntryCreate(title="Dune"))
    service.delete(entry.id)
    post_called = False

    def fake_post(*a: Any, **kw: Any) -> _FakeResponse:  # noqa: ANN401
        nonlocal post_called
        post_called = True
        return _FakeResponse({"title_results": [], "state_results": []})

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "get", _empty_pull)

    result = sync_service.sync_now("http://server:8000", "tok", "participant", since=None)

    assert result.pushed == 0
    assert post_called is False


def test_pull_applies_new_title_and_state_from_server(
    service: EntryService, sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = dt.datetime.now(dt.UTC)
    uuid = "11111111-1111-1111-1111-111111111111"
    title = {
        "uuid": uuid,
        "type": "movie",
        "title": "From Phone",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    state = {"title_uuid": uuid, "status": "watching", "updated_at": now.isoformat()}

    monkeypatch.setattr(
        requests, "post", lambda *a, **kw: _FakeResponse({"title_results": [], "state_results": []})
    )
    monkeypatch.setattr(
        requests, "get", lambda *a, **kw: _FakeResponse({"titles": [title], "states": [state]})
    )

    result = sync_service.sync_now("http://server:8000", "tok", "admin", since=None)

    assert result.pulled == 2  # one title + one state applied
    entries = service.list_all()
    assert len(entries) == 1
    assert entries[0].title == "From Phone"
    assert entries[0].status.value == "watching"


def test_pull_skips_stale_title_keeps_local_catalog_data(
    service: EntryService, sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    local = service.create(EntryCreate(title="Local Newer"))
    stale_title = {
        "uuid": local.uuid,
        "type": "movie",
        "title": "Stale From Server",
        "created_at": (local.created_at - dt.timedelta(days=1)).isoformat(),
        "updated_at": (local.created_at - dt.timedelta(days=1)).isoformat(),
    }

    monkeypatch.setattr(
        requests, "post", lambda *a, **kw: _FakeResponse({"title_results": [], "state_results": []})
    )
    monkeypatch.setattr(
        requests, "get", lambda *a, **kw: _FakeResponse({"titles": [stale_title], "states": []})
    )

    result = sync_service.sync_now("http://server:8000", "tok", "admin", since=None)

    assert result.pulled == 0
    refreshed = service.get(local.id)
    assert refreshed is not None and refreshed.title == "Local Newer"


def test_pull_skips_stale_state_keeps_local_personal_data(
    service: EntryService, sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = service.create(EntryCreate(title="Dune"))
    local = service.update(created.id, EntryUpdate(status=Status.COMPLETED))
    assert local is not None
    stale_state = {
        "title_uuid": local.uuid,
        "status": "planned",
        "updated_at": (local.updated_at - dt.timedelta(days=1)).isoformat(),
    }

    monkeypatch.setattr(
        requests, "post", lambda *a, **kw: _FakeResponse({"title_results": [], "state_results": []})
    )
    monkeypatch.setattr(
        requests, "get", lambda *a, **kw: _FakeResponse({"titles": [], "states": [stale_state]})
    )

    result = sync_service.sync_now("http://server:8000", "tok", "admin", since=None)

    assert result.pulled == 0
    refreshed = service.get(local.id)
    assert refreshed is not None and refreshed.status == Status.COMPLETED
