from datetime import datetime, timedelta, timezone

import pytest


@pytest.mark.asyncio
async def test_issue_external_crm_access_code_returns_code_and_window(client) -> None:
    starts_at = datetime(2026, 4, 22, 12, 0, tzinfo=timezone.utc)
    ends_at = starts_at + timedelta(hours=2)

    response = await client.post(
        "/api/v1/external-crm/access-code",
        json={
            "lock_id": "studio-a1",
            "booking_starts_at": starts_at.isoformat(),
            "booking_ends_at": ends_at.isoformat(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["lock_id"] == "studio-a1"
    assert len(payload["access_code"]) == 10
    assert payload["access_code"].isalnum()
    assert payload["access_url"] == (
        f"lockey://open?lock_id=studio-a1&access_code={payload['access_code']}"
        "&booking_starts_at=2026-04-22T12:00:00Z&booking_ends_at=2026-04-22T14:00:00Z"
    )
    assert payload["booking_starts_at"] == starts_at.isoformat().replace("+00:00", "Z")
    assert payload["booking_ends_at"] == ends_at.isoformat().replace("+00:00", "Z")
    assert payload["valid_from"] == (starts_at - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    assert payload["valid_until"] == ends_at.isoformat().replace("+00:00", "Z")


@pytest.mark.asyncio
async def test_issue_external_crm_access_code_rejects_invalid_window(client) -> None:
    starts_at = datetime(2026, 4, 22, 12, 0, tzinfo=timezone.utc)

    response = await client.post(
        "/api/v1/external-crm/access-code",
        json={
            "lock_id": "studio-a1",
            "booking_starts_at": starts_at.isoformat(),
            "booking_ends_at": starts_at.isoformat(),
        },
    )

    assert response.status_code == 422
