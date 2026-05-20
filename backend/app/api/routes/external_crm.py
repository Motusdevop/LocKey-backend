from fastapi import APIRouter, Depends

from app.api.dependencies import get_external_crm_service
from app.schemas.external_crm import ExternalCrmAccessCodeRequest, ExternalCrmAccessCodeResponse
from app.services.external_crm import ExternalCrmService

router = APIRouter()


@router.post("/external-crm/access-code", response_model=ExternalCrmAccessCodeResponse)
async def issue_external_crm_access_code(
    payload: ExternalCrmAccessCodeRequest,
    service: ExternalCrmService = Depends(get_external_crm_service),
) -> ExternalCrmAccessCodeResponse:
    return service.issue_access_code(
        lock_id=payload.lock_id,
        booking_starts_at=payload.booking_starts_at,
        booking_ends_at=payload.booking_ends_at,
    )
