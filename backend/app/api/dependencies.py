from fastapi import Request
from starlette.requests import HTTPConnection

from app.core.config import get_settings
from app.db.session import DatabaseManager
from app.services.external_crm import ExternalCrmService
from app.services.health import HealthService
from app.services.locks import LockManager


def get_database_manager(request: Request) -> DatabaseManager:
    return request.app.state.database_manager


def get_health_service(request: Request) -> HealthService:
    database_manager = get_database_manager(request)
    return HealthService(database_manager)


def get_external_crm_service() -> ExternalCrmService:
    settings = get_settings()
    return ExternalCrmService(
        code_secret=settings.external_crm_code_secret,
        early_access_buffer_minutes=settings.booking_early_access_buffer_minutes,
    )


def get_lock_manager(connection: HTTPConnection) -> LockManager:
    return connection.app.state.lock_manager
