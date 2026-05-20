import pytest


@pytest.mark.asyncio
async def test_access_tester_page_is_served(client) -> None:
    response = await client.get("/api/v1/debug/access-tester")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "LocKey Access Tester" in response.text


@pytest.mark.asyncio
async def test_openapi_does_not_expose_offline_ticket_routes(client) -> None:
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    assert all("offline-tickets" not in path for path in response.json()["paths"])
