import pytest


@pytest.mark.asyncio
async def test_access_tester_page_is_served(client) -> None:
    response = await client.get("/api/v1/debug/access-tester")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "LocKey Access Tester" in response.text
