from datetime import datetime, timedelta, timezone

import pytest

from app.services.offline_tickets import OfflineTicketService


@pytest.mark.asyncio
async def test_issue_offline_ticket_returns_ticket_for_future_booking(client) -> None:
    starts_at = datetime.now(timezone.utc) + timedelta(hours=2)
    ends_at = starts_at + timedelta(hours=2)

    access_response = await client.post(
        "/api/v1/external-crm/access-code",
        json={
            "lock_id": "studio-a1",
            "booking_starts_at": starts_at.isoformat(),
            "booking_ends_at": ends_at.isoformat(),
        },
    )
    access_payload = access_response.json()

    response = await client.post(
        "/api/v1/offline-tickets/issue",
        json={
            "lock_id": "studio-a1",
            "access_code": access_payload["access_code"],
            "booking_starts_at": access_payload["booking_starts_at"],
            "booking_ends_at": access_payload["booking_ends_at"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["lock_id"] == "studio-a1"
    assert payload["offline_ticket"].startswith("ot1.")
    assert payload["valid_from"] == (starts_at - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    assert payload["valid_until"] == ends_at.isoformat().replace("+00:00", "Z")


@pytest.mark.asyncio
async def test_verify_offline_ticket_returns_valid_payload(client) -> None:
    starts_at = datetime.now(timezone.utc) - timedelta(minutes=2)
    ends_at = starts_at + timedelta(hours=1)

    access_response = await client.post(
        "/api/v1/external-crm/access-code",
        json={
            "lock_id": "studio-a1",
            "booking_starts_at": starts_at.isoformat(),
            "booking_ends_at": ends_at.isoformat(),
        },
    )
    access_payload = access_response.json()
    issue_response = await client.post(
        "/api/v1/offline-tickets/issue",
        json={
            "lock_id": "studio-a1",
            "access_code": access_payload["access_code"],
            "booking_starts_at": access_payload["booking_starts_at"],
            "booking_ends_at": access_payload["booking_ends_at"],
        },
    )
    issue_payload = issue_response.json()

    response = await client.post(
        "/api/v1/offline-tickets/verify",
        json={
            "lock_id": "studio-a1",
            "offline_ticket": issue_payload["offline_ticket"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "valid"
    assert payload["lock_id"] == "studio-a1"
    assert payload["ticket_id"] == issue_payload["ticket_id"]


@pytest.mark.asyncio
async def test_verify_offline_ticket_rejects_tampered_signature(client) -> None:
    starts_at = datetime.now(timezone.utc) - timedelta(minutes=2)
    ends_at = starts_at + timedelta(hours=1)

    access_response = await client.post(
        "/api/v1/external-crm/access-code",
        json={
            "lock_id": "studio-a1",
            "booking_starts_at": starts_at.isoformat(),
            "booking_ends_at": ends_at.isoformat(),
        },
    )
    access_payload = access_response.json()
    issue_response = await client.post(
        "/api/v1/offline-tickets/issue",
        json={
            "lock_id": "studio-a1",
            "access_code": access_payload["access_code"],
            "booking_starts_at": access_payload["booking_starts_at"],
            "booking_ends_at": access_payload["booking_ends_at"],
        },
    )
    issue_payload = issue_response.json()
    tampered_ticket = issue_payload["offline_ticket"][:-1] + (
        "A" if issue_payload["offline_ticket"][-1] != "A" else "B"
    )

    response = await client.post(
        "/api/v1/offline-tickets/verify",
        json={
            "lock_id": "studio-a1",
            "offline_ticket": tampered_ticket,
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Offline ticket signature is invalid"}


@pytest.mark.asyncio
async def test_issue_offline_ticket_rejects_finished_booking(client) -> None:
    starts_at = datetime.now(timezone.utc) - timedelta(hours=3)
    ends_at = starts_at + timedelta(hours=1)

    access_response = await client.post(
        "/api/v1/external-crm/access-code",
        json={
            "lock_id": "studio-a1",
            "booking_starts_at": starts_at.isoformat(),
            "booking_ends_at": ends_at.isoformat(),
        },
    )
    access_payload = access_response.json()

    response = await client.post(
        "/api/v1/offline-tickets/issue",
        json={
            "lock_id": "studio-a1",
            "access_code": access_payload["access_code"],
            "booking_starts_at": access_payload["booking_starts_at"],
            "booking_ends_at": access_payload["booking_ends_at"],
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Booking has already ended"}


@pytest.mark.asyncio
async def test_verify_offline_ticket_rejects_inactive_ticket(client) -> None:
    service = OfflineTicketService(secret="change-me-offline-ticket-secret", allowed_time_drift_seconds=60)
    ticket = service.issue_ticket(
        lock_id="studio-a1",
        valid_from=datetime.now(timezone.utc) - timedelta(hours=3),
        valid_until=datetime.now(timezone.utc) - timedelta(hours=2),
        issued_at=datetime.now(timezone.utc) - timedelta(hours=4),
    )

    response = await client.post(
        "/api/v1/offline-tickets/verify",
        json={
            "lock_id": "studio-a1",
            "offline_ticket": ticket.offline_ticket,
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Offline ticket is not active"}
