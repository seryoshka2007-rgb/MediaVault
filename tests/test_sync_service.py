"""SyncService push/pull, with requests mocked - no real network involved."""
from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
import requests

from core.schemas import EntryCreate
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


def test_register_device_returns_token(
    sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, json: dict[str, Any], timeout: int) -> _FakeResponse:
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse({"device_id": 1, "token": "abc123"})

    monkeypatch.setattr(requests, "post", fake_post)
    token = sync_service.register_device("http://server:8000", "setup-key", "My PC")

    assert token == "abc123"
    assert captured["url"] == "http://server:8000/devices/register"
    assert captured["json"] == {"setup_key": "setup-key", "label": "My PC"}


def test_register_device_network_error_raises_sync_error(
    sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_post(*a: Any, **kw: Any) -> _FakeResponse:  # noqa: ANN401
        raise requests.exceptions.ConnectionError("refused")

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(SyncError):
        sync_service.register_device("http://server:8000", "key", "PC")


def test_push_sends_locally_changed_entries(
    service: EntryService, sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    service.create(EntryCreate(title="Dune"))
    captured: dict[str, Any] = {}

    def fake_post(
        url: str, json: dict[str, Any], headers: dict[str, str], timeout: int
    ) -> _FakeResponse:
        captured["json"] = json
        captured["headers"] = headers
        applied = [{"uuid": json["entries"][0]["uuid"], "applied": True}]
        return _FakeResponse({"results": applied})

    def fake_get(*a: Any, **kw: Any) -> _FakeResponse:  # noqa: ANN401
        return _FakeResponse({"entries": []})

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "get", fake_get)

    result = sync_service.sync_now("http://server:8000", "tok", since=None)

    assert result.pushed == 1
    assert result.pulled == 0
    assert captured["headers"]["Authorization"] == "Bearer tok"
    assert captured["json"]["entries"][0]["title"] == "Dune"


def test_pull_applies_new_entry_from_server(
    service: EntryService, sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = dt.datetime.now(dt.UTC)
    incoming = {
        "uuid": "11111111-1111-1111-1111-111111111111",
        "type": "movie",
        "title": "From Phone",
        "status": "planned",
        "open_count": 0,
        "is_favorite": False,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    monkeypatch.setattr(requests, "post", lambda *a, **kw: _FakeResponse({"results": []}))
    monkeypatch.setattr(
        requests, "get", lambda *a, **kw: _FakeResponse({"entries": [incoming]})
    )

    result = sync_service.sync_now("http://server:8000", "tok", since=None)

    assert result.pulled == 1
    titles = [e.title for e in service.list_all()]
    assert "From Phone" in titles


def test_pull_skips_when_local_copy_is_newer(
    service: EntryService, sync_service: SyncService, monkeypatch: pytest.MonkeyPatch
) -> None:
    local = service.create(EntryCreate(title="Local Newer"))
    stale_incoming = {
        "uuid": local.uuid,
        "type": "movie",
        "title": "Stale From Server",
        "status": "planned",
        "open_count": 0,
        "is_favorite": False,
        "created_at": (local.created_at - dt.timedelta(days=1)).isoformat(),
        "updated_at": (local.updated_at - dt.timedelta(days=1)).isoformat(),
    }

    monkeypatch.setattr(requests, "post", lambda *a, **kw: _FakeResponse({"results": []}))
    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **kw: _FakeResponse({"entries": [stale_incoming]}),
    )

    result = sync_service.sync_now("http://server:8000", "tok", since=None)

    assert result.pulled == 0
    refreshed = service.get(local.id)
    assert refreshed is not None and refreshed.title == "Local Newer"
