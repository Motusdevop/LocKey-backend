import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


@contextmanager
def connect_lock(test_client: TestClient, lock_id: str):
    with test_client.websocket_connect(f"/api/v1/ws/locks/{lock_id}") as websocket:
        yield websocket


def test_lock_websocket_pushes_short_code(sync_client: TestClient) -> None:
    with connect_lock(sync_client, "studio-a1") as websocket:
        payload = websocket.receive_json()

        assert payload["type"] == "code"
        assert len(payload["value"]) == 6
        assert payload["value"].isalnum()
        assert payload["expires_at"] >= int(time.time())


def test_open_command_is_delivered_to_connected_lock(sync_client: TestClient) -> None:
    with connect_lock(sync_client, "studio-a1") as websocket:
        first_message = websocket.receive_json()
        assert first_message["type"] == "code"

        response = sync_client.post("/api/v1/locks/studio-a1/open")

        assert response.status_code == 202
        payload = response.json()
        assert payload["status"] == "sent"
        assert payload["lock_id"] == "studio-a1"
        assert isinstance(payload["command_id"], str)
        assert websocket.receive_json() == {
            "type": "open",
            "command_id": payload["command_id"],
        }


def test_open_link_is_delivered_to_connected_lock(sync_client: TestClient) -> None:
    with connect_lock(sync_client, "studio-a1") as websocket:
        first_message = websocket.receive_json()
        assert first_message["type"] == "code"

        response = sync_client.get("/api/v1/locks/studio-a1/open")

        assert response.status_code == 202
        payload = response.json()
        assert payload["status"] == "sent"
        assert payload["lock_id"] == "studio-a1"
        assert websocket.receive_json() == {
            "type": "open",
            "command_id": payload["command_id"],
        }


def test_open_command_returns_not_found_for_offline_lock(sync_client: TestClient) -> None:
    response = sync_client.post("/api/v1/locks/studio-a1/open")

    assert response.status_code == 404
    assert response.json() == {"detail": "Lock is offline"}


def test_verify_access_opens_connected_lock(sync_client: TestClient) -> None:
    with connect_lock(sync_client, "studio-a1") as websocket:
        first_message = websocket.receive_json()
        assert first_message["type"] == "code"

        starts_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        ends_at = starts_at + timedelta(hours=2)
        access_response = sync_client.post(
            "/api/v1/external-crm/access-code",
            json={
                "lock_id": "studio-a1",
                "booking_starts_at": starts_at.isoformat(),
                "booking_ends_at": ends_at.isoformat(),
            },
        )
        assert access_response.status_code == 200
        access_payload = access_response.json()

        response = sync_client.post(
            "/api/v1/locks/studio-a1/verify-access",
            json={
                "access_code": access_payload["access_code"],
                "lock_code": first_message["value"],
                "booking_starts_at": access_payload["booking_starts_at"],
                "booking_ends_at": access_payload["booking_ends_at"],
            },
        )

        assert response.status_code == 202
        payload = response.json()
        assert payload["status"] == "sent"
        assert payload["lock_id"] == "studio-a1"
        assert websocket.receive_json() == {
            "type": "open",
            "command_id": payload["command_id"],
        }


def test_verify_access_rejects_invalid_lock_code(sync_client: TestClient) -> None:
    with connect_lock(sync_client, "studio-a1") as websocket:
        websocket.receive_json()

        starts_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        ends_at = starts_at + timedelta(hours=2)
        access_response = sync_client.post(
            "/api/v1/external-crm/access-code",
            json={
                "lock_id": "studio-a1",
                "booking_starts_at": starts_at.isoformat(),
                "booking_ends_at": ends_at.isoformat(),
            },
        )
        access_payload = access_response.json()

        response = sync_client.post(
            "/api/v1/locks/studio-a1/verify-access",
            json={
                "access_code": access_payload["access_code"],
                "lock_code": "ZZZZZZ",
                "booking_starts_at": access_payload["booking_starts_at"],
                "booking_ends_at": access_payload["booking_ends_at"],
            },
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "Lock code is invalid or expired"}


def test_verify_access_rejects_closed_booking_window(sync_client: TestClient) -> None:
    with connect_lock(sync_client, "studio-a1") as websocket:
        first_message = websocket.receive_json()

        starts_at = datetime.now(timezone.utc) + timedelta(hours=1)
        ends_at = starts_at + timedelta(hours=2)
        access_response = sync_client.post(
            "/api/v1/external-crm/access-code",
            json={
                "lock_id": "studio-a1",
                "booking_starts_at": starts_at.isoformat(),
                "booking_ends_at": ends_at.isoformat(),
            },
        )
        access_payload = access_response.json()

        response = sync_client.post(
            "/api/v1/locks/studio-a1/verify-access",
            json={
                "access_code": access_payload["access_code"],
                "lock_code": first_message["value"],
                "booking_starts_at": access_payload["booking_starts_at"],
                "booking_ends_at": access_payload["booking_ends_at"],
            },
        )

        assert response.status_code == 403
        assert response.json() == {"detail": "Booking access window is closed"}

# codex resume 019d9511-47c2-7133-a60d-2a7cdbb981d5
