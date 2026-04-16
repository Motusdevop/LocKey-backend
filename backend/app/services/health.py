from app.db.session import DatabaseManager
from app.schemas.health import HealthResponse


class HealthService:
    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    async def get_status(self) -> HealthResponse:
        database_is_ready = await self._database_manager.ping()
        if database_is_ready:
            return HealthResponse(status="ok", database="up")

        return HealthResponse(status="degraded", database="down")
