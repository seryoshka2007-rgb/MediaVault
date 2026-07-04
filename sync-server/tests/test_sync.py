from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
from fastapi.testclient import TestClient

import sync_server.main as main_module


@pytest.fixture(autouse=True)
def _fake_setup_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main_module, "setup_key", lambda: "test-setup-key")


def _register(client: TestClient, label: str = "Test Device") -> str:
    resp = client.post(
        "/devices/register", json={"setup_key": "test-setup-key", "label": label}
    )
    assert resp.status_code == 200
    token = resp.json()["token"]
    assert isinstance(token, str)
    return token


def _entry(
    uuid: str, title: str, updated_at: dt.datetime, **overrides: Any  # noqa: ANN401
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "uuid": uuid,
        "type": "movie",
        "title": title,
        "status": "planned",
        "created_at": updated_at.isoformat(),
        "updated_at": updated_at.isoformat(),
    }
    base.update(overrides)
    return base


def test_register_device_wrong_key_rejected(client: TestClient) -> None:
    resp = client.post(
        "/devices/register", json={"setup_key": "wrong", "label": "X"}
    )
    assert resp.status_code == 403


def test_register_and_push_pull_roundtrip(client: TestClient) -> None:
    token = _register(client)
    now = dt.datetime.now(dt.UTC)
    entry = _entry("11111111-1111-1111-1111-111111111111", "Dune", now)

    push = client.post(
        "/sync/push",
        json={"entries": [entry]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert push.status_code == 200
    assert push.json()["results"] == [{"uuid": entry["uuid"], "applied": True}]

    pull = client.get(
        "/sync/pull",
        params={"since": (now - dt.timedelta(seconds=1)).isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pull.status_code == 200
    titles = [e["title"] for e in pull.json()["entries"]]
    assert titles == ["Dune"]


def test_push_without_token_rejected(client: TestClient) -> None:
    now = dt.datetime.now(dt.UTC)
    resp = client.post(
        "/sync/push",
        json={"entries": [_entry("22222222-2222-2222-2222-222222222222", "Dune", now)]},
    )
    assert resp.status_code == 401  # no Authorization header at all


def test_push_last_write_wins_rejects_older_update(client: TestClient) -> None:
    token = _register(client)
    headers = {"Authorization": f"Bearer {token}"}
    uuid = "33333333-3333-3333-3333-333333333333"
    older = dt.datetime.now(dt.UTC)
    newer = older + dt.timedelta(minutes=5)

    first = client.post(
        "/sync/push", json={"entries": [_entry(uuid, "Dune", newer)]}, headers=headers
    )
    assert first.json()["results"][0]["applied"] is True

    stale = client.post(
        "/sync/push",
        json={"entries": [_entry(uuid, "Dune (stale title)", older)]},
        headers=headers,
    )
    assert stale.json()["results"][0]["applied"] is False

    pull = client.get(
        "/sync/pull",
        params={"since": (older - dt.timedelta(seconds=1)).isoformat()},
        headers=headers,
    )
    titles = [e["title"] for e in pull.json()["entries"]]
    assert titles == ["Dune"]  # the newer push won, stale one was rejected
