from http import HTTPStatus

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.dependencies import get_health_service
from app.schemas.health import HealthResponse
from app.services.health import HealthService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    service: HealthService = Depends(get_health_service),
) -> HealthResponse | JSONResponse:
    result = await service.get_status()
    if result.status == "ok":
        return result

    return JSONResponse(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        content=result.model_dump(),
    )
