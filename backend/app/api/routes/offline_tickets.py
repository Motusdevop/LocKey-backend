from datetime import datetime, timezone
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_external_crm_service, get_offline_ticket_service
from app.schemas.offline_tickets import (
    OfflineTicketIssueRequest,
    OfflineTicketIssueResponse,
    OfflineTicketVerifyRequest,
    OfflineTicketVerifyResponse,
)
from app.services.external_crm import ExternalCrmService, InvalidAccessCodeError
from app.services.offline_tickets import (
    InvalidOfflineTicketError,
    OfflineTicketInactiveError,
    OfflineTicketLockMismatchError,
    OfflineTicketService,
)

router = APIRouter()


@router.post("/offline-tickets/issue", response_model=OfflineTicketIssueResponse)
async def issue_offline_ticket(
    payload: OfflineTicketIssueRequest,
    external_crm_service: ExternalCrmService = Depends(get_external_crm_service),
    offline_ticket_service: OfflineTicketService = Depends(get_offline_ticket_service),
) -> OfflineTicketIssueResponse:
    access = external_crm_service.issue_access_code(
        lock_id=payload.lock_id,
        booking_starts_at=payload.booking_starts_at,
        booking_ends_at=payload.booking_ends_at,
    )

    try:
        external_crm_service.validate_access_code_signature(
            lock_id=payload.lock_id,
            access_code=payload.access_code,
            booking_starts_at=access.booking_starts_at,
            booking_ends_at=access.booking_ends_at,
        )
    except InvalidAccessCodeError as exc:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(exc)) from exc

    if access.valid_until <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Booking has already ended",
        )

    return offline_ticket_service.issue_ticket(
        lock_id=payload.lock_id,
        valid_from=access.valid_from,
        valid_until=access.valid_until,
    )


@router.post("/offline-tickets/verify", response_model=OfflineTicketVerifyResponse)
async def verify_offline_ticket(
    payload: OfflineTicketVerifyRequest,
    offline_ticket_service: OfflineTicketService = Depends(get_offline_ticket_service),
) -> OfflineTicketVerifyResponse:
    try:
        return offline_ticket_service.verify_ticket(
            lock_id=payload.lock_id,
            offline_ticket=payload.offline_ticket,
        )
    except (InvalidOfflineTicketError, OfflineTicketLockMismatchError) as exc:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(exc)) from exc
    except OfflineTicketInactiveError as exc:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail=str(exc)) from exc
