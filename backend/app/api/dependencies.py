from fastapi import Request

from app.db.session import DatabaseManager
from app.services.health import HealthService


def get_database_manager(request: Request) -> DatabaseManager:
    return request.app.state.database_manager


def get_health_service(request: Request) -> HealthService:
    database_manager = get_database_manager(request)
    return HealthService(database_manager)
