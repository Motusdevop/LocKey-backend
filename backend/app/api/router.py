from fastapi import APIRouter

from app.api.routes.debug import router as debug_router
from app.api.routes.external_crm import router as external_crm_router
from app.api.routes.health import router as health_router
from app.api.routes.locks import router as locks_router

api_router = APIRouter()
api_router.include_router(debug_router, tags=["debug"])
api_router.include_router(external_crm_router, tags=["external-crm"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(locks_router, tags=["locks"])
