from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
from fastapi.testclient import TestClient

import sync_server.config as config_module

ADMIN_KEY = "admin-secret"
PARTICIPANT_KEY = "participant-secret"


@pytest.fixture(autouse=True)
def _fake_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module, "admin_key", lambda: ADMIN_KEY)
    monkeypatch.setattr(config_module, "participant_key", lambda: PARTICIPANT_KEY)
    import sync_server.service as service_module

    monkeypatch.setattr(service_module, "admin_key", lambda: ADMIN_KEY)
    monkeypatch.setattr(service_module, "participant_key", lambda: PARTICIPANT_KEY)


def _register(
    client: TestClient, *, key: str, person_name: str, label: str = "Test Device"
) -> dict[str, Any]:
    resp = client.post(
        "/devices/register",
        json={"key": key, "person_name": person_name, "label": label},
    )
    assert resp.status_code == 200, resp.text
    result: dict[str, Any] = resp.json()
    return result


def _title(
    uuid: str, title: str, updated_at: dt.datetime, **overrides: Any  # noqa: ANN401
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "uuid": uuid,
        "type": "movie",
        "title": title,
        "created_at": updated_at.isoformat(),
        "updated_at": updated_at.isoformat(),
    }
    base.update(overrides)
    return base


def _state(
    title_uuid: str, status: str, updated_at: dt.datetime, **overrides: Any  # noqa: ANN401
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "title_uuid": title_uuid,
        "status": status,
        "updated_at": updated_at.isoformat(),
    }
    base.update(overrides)
    return base


def test_admin_registration(client: TestClient) -> None:
    resp = _register(client, key=ADMIN_KEY, person_name="Me")
    assert resp["role"] == "admin"


def test_participant_registration(client: TestClient) -> None:
    resp = _register(client, key=PARTICIPANT_KEY, person_name="Alice")
    assert resp["role"] == "participant"
    assert resp["person_name"] == "Alice"


def test_wrong_key_rejected(client: TestClient) -> None:
    resp = client.post(
        "/devices/register",
        json={"key": "nope", "person_name": "Anyone", "label": "X"},
    )
    assert resp.status_code == 403


def test_participant_cannot_reuse_admin_name(client: TestClient) -> None:
    _register(client, key=ADMIN_KEY, person_name="Owner")
    resp = client.post(
        "/devices/register",
        json={"key": PARTICIPANT_KEY, "person_name": "Owner", "label": "X"},
    )
    assert resp.status_code == 409


def test_second_device_same_name_shares_person_state(client: TestClient) -> None:
    """Two devices registered under the same participant name are the same
    Person - personal state pushed from one is visible when the other pulls."""
    device1 = _register(client, key=PARTICIPANT_KEY, person_name="Alice", label="Phone")
    device2 = _register(client, key=PARTICIPANT_KEY, person_name="Alice", label="Laptop")
    headers1 = {"Authorization": f"Bearer {device1['token']}"}
    headers2 = {"Authorization": f"Bearer {device2['token']}"}

    now = dt.datetime.now(dt.UTC)
    uuid = "11111111-1111-1111-1111-111111111111"
    client.post(
        "/sync/push",
        json={"titles": [_title(uuid, "Dune", now)], "states": []},
        headers=headers1,
    )
    client.post(
        "/sync/push",
        json={"titles": [], "states": [_state(uuid, "watching", now)]},
        headers=headers1,
    )

    pull = client.get(
        "/sync/pull",
        params={"since": (now - dt.timedelta(seconds=1)).isoformat()},
        headers=headers2,
    )
    states = pull.json()["states"]
    assert len(states) == 1
    assert states[0]["status"] == "watching"


def test_title_shared_state_private_between_participants(client: TestClient) -> None:
    alice = _register(client, key=PARTICIPANT_KEY, person_name="Alice")
    bob = _register(client, key=PARTICIPANT_KEY, person_name="Bob")
    alice_headers = {"Authorization": f"Bearer {alice['token']}"}
    bob_headers = {"Authorization": f"Bearer {bob['token']}"}

    now = dt.datetime.now(dt.UTC)
    uuid = "22222222-2222-2222-2222-222222222222"

    # Alice adds the title and marks it completed.
    client.post(
        "/sync/push",
        json={"titles": [_title(uuid, "Interstellar", now)], "states": []},
        headers=alice_headers,
    )
    client.post(
        "/sync/push",
        json={"titles": [], "states": [_state(uuid, "completed", now)]},
        headers=alice_headers,
    )

    # Bob pulls: sees the shared title, but not Alice's personal state.
    pull_bob = client.get(
        "/sync/pull",
        params={"since": (now - dt.timedelta(seconds=1)).isoformat()},
        headers=bob_headers,
    )
    body = pull_bob.json()
    assert [t["title"] for t in body["titles"]] == ["Interstellar"]
    assert body["states"] == []

    # Bob sets his own status - doesn't clobber Alice's.
    client.post(
        "/sync/push",
        json={"titles": [], "states": [_state(uuid, "planned", now)]},
        headers=bob_headers,
    )
    pull_alice = client.get(
        "/sync/pull",
        params={"since": (now - dt.timedelta(seconds=1)).isoformat()},
        headers=alice_headers,
    )
    alice_states = pull_alice.json()["states"]
    assert len(alice_states) == 1
    assert alice_states[0]["status"] == "completed"


def test_participant_cannot_delete_title_admin_can(client: TestClient) -> None:
    admin = _register(client, key=ADMIN_KEY, person_name="Owner")
    participant = _register(client, key=PARTICIPANT_KEY, person_name="Alice")
    admin_headers = {"Authorization": f"Bearer {admin['token']}"}
    participant_headers = {"Authorization": f"Bearer {participant['token']}"}

    now = dt.datetime.now(dt.UTC)
    uuid = "33333333-3333-3333-3333-333333333333"
    client.post(
        "/sync/push",
        json={"titles": [_title(uuid, "Dune", now)], "states": []},
        headers=admin_headers,
    )

    later = now + dt.timedelta(minutes=1)
    reject = client.post(
        "/sync/push",
        json={
            "titles": [_title(uuid, "Dune", later, deleted_at=later.isoformat())],
            "states": [],
        },
        headers=participant_headers,
    )
    result = reject.json()["title_results"][0]
    assert result["applied"] is False
    assert result["reason"] == "requires admin role"

    accept = client.post(
        "/sync/push",
        json={
            "titles": [_title(uuid, "Dune", later, deleted_at=later.isoformat())],
            "states": [],
        },
        headers=admin_headers,
    )
    assert accept.json()["title_results"][0]["applied"] is True


def test_admin_can_list_people_and_devices(client: TestClient) -> None:
    admin = _register(client, key=ADMIN_KEY, person_name="Owner")
    _register(client, key=PARTICIPANT_KEY, person_name="Alice", label="Phone")
    admin_headers = {"Authorization": f"Bearer {admin['token']}"}

    resp = client.get("/admin/people", headers=admin_headers)

    assert resp.status_code == 200
    people = resp.json()
    names = {p["name"]: p for p in people}
    assert set(names) == {"Owner", "Alice"}
    assert names["Alice"]["role"] == "participant"
    assert [d["label"] for d in names["Alice"]["devices"]] == ["Phone"]


def test_participant_cannot_list_people(client: TestClient) -> None:
    participant = _register(client, key=PARTICIPANT_KEY, person_name="Alice")
    headers = {"Authorization": f"Bearer {participant['token']}"}

    resp = client.get("/admin/people", headers=headers)

    assert resp.status_code == 403


def test_admin_can_revoke_a_participant_device(client: TestClient) -> None:
    admin = _register(client, key=ADMIN_KEY, person_name="Owner")
    participant = _register(client, key=PARTICIPANT_KEY, person_name="Alice")
    admin_headers = {"Authorization": f"Bearer {admin['token']}"}
    participant_headers = {"Authorization": f"Bearer {participant['token']}"}

    revoke = client.delete(f"/admin/devices/{participant['device_id']}", headers=admin_headers)
    assert revoke.status_code == 204

    now = dt.datetime.now(dt.UTC)
    resp = client.get(
        "/sync/pull", params={"since": now.isoformat()}, headers=participant_headers
    )
    assert resp.status_code == 401


def test_participant_cannot_revoke_devices(client: TestClient) -> None:
    admin = _register(client, key=ADMIN_KEY, person_name="Owner")
    participant = _register(client, key=PARTICIPANT_KEY, person_name="Alice")
    participant_headers = {"Authorization": f"Bearer {participant['token']}"}

    resp = client.delete(f"/admin/devices/{admin['device_id']}", headers=participant_headers)

    assert resp.status_code == 403


def test_admin_cannot_revoke_own_device(client: TestClient) -> None:
    admin = _register(client, key=ADMIN_KEY, person_name="Owner")
    admin_headers = {"Authorization": f"Bearer {admin['token']}"}

    resp = client.delete(f"/admin/devices/{admin['device_id']}", headers=admin_headers)

    assert resp.status_code == 403


def test_revoke_unknown_device_is_404(client: TestClient) -> None:
    admin = _register(client, key=ADMIN_KEY, person_name="Owner")
    admin_headers = {"Authorization": f"Bearer {admin['token']}"}

    resp = client.delete("/admin/devices/999999", headers=admin_headers)

    assert resp.status_code == 404


def test_push_without_token_rejected(client: TestClient) -> None:
    now = dt.datetime.now(dt.UTC)
    uuid = "44444444-4444-4444-4444-444444444444"
    resp = client.post(
        "/sync/push",
        json={"titles": [_title(uuid, "Dune", now)], "states": []},
    )
    assert resp.status_code == 401
