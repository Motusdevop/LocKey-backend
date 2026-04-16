import pytest
from fastapi import FastAPI

from app.api.dependencies import get_health_service
from app.schemas.health import HealthResponse

pytestmark = pytest.mark.asyncio


class ReadyHealthService:
    async def get_status(self) -> HealthResponse:
        return HealthResponse(status="ok", database="up")


class NotReadyHealthService:
    async def get_status(self) -> HealthResponse:
        return HealthResponse(status="degraded", database="down")


def override_health_service(app: FastAPI, service: object) -> None:
    app.dependency_overrides[get_health_service] = lambda: service


async def test_health_check_returns_ok_when_database_is_ready(client, app: FastAPI) -> None:
    override_health_service(app, ReadyHealthService())

    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


async def test_health_check_returns_service_unavailable_when_database_is_down(
    client,
    app: FastAPI,
) -> None:
    override_health_service(app, NotReadyHealthService())

    response = await client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "down"}
