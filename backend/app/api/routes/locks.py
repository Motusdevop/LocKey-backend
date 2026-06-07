from http import HTTPStatus
import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from loguru import logger

from app.api.dependencies import get_external_crm_service, get_lock_manager
from app.schemas.locks import OpenLockResponse, VerifyLockAccessRequest
from app.services.external_crm import AccessWindowClosedError, ExternalCrmService, InvalidAccessCodeError
from app.services.locks import InvalidLockCodeError, LockManager, LockNotConnectedError

router = APIRouter()


@router.get("/locks/{lock_id}/open", response_model=OpenLockResponse, status_code=HTTPStatus.ACCEPTED)
@router.post("/locks/{lock_id}/open", response_model=OpenLockResponse, status_code=HTTPStatus.ACCEPTED)
async def open_lock(
    lock_id: str,
    manager: LockManager = Depends(get_lock_manager),
) -> OpenLockResponse:
    try:
        return await manager.open_lock(lock_id)
    except LockNotConnectedError as exc:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/locks/{lock_id}/verify-access",
    response_model=OpenLockResponse,
    status_code=HTTPStatus.ACCEPTED,
)
async def verify_lock_access(
    lock_id: str,
    payload: VerifyLockAccessRequest,
    manager: LockManager = Depends(get_lock_manager),
    external_crm_service: ExternalCrmService = Depends(get_external_crm_service),
) -> OpenLockResponse:
    try:
        manager.validate_lock_code(lock_id, payload.lock_code)
        external_crm_service.validate_access_code(
            lock_id=lock_id,
            access_code=payload.access_code,
            booking_starts_at=payload.booking_starts_at,
            booking_ends_at=payload.booking_ends_at,
        )
        return await manager.open_lock(lock_id)
    except InvalidLockCodeError as exc:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(exc)) from exc
    except InvalidAccessCodeError as exc:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(exc)) from exc
    except AccessWindowClosedError as exc:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail=str(exc)) from exc
    except LockNotConnectedError as exc:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(exc)) from exc


@router.websocket("/ws/locks/{lock_id}")
async def lock_websocket(
    websocket: WebSocket,
    lock_id: str,
    manager: LockManager = Depends(get_lock_manager),
) -> None:
    await manager.connect(lock_id, websocket)
    logger.info("Lock connected: {}", lock_id)
    codes_task = asyncio.create_task(manager.push_codes(lock_id, websocket))

    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        logger.info("Lock disconnected: {}", lock_id)
    finally:
        codes_task.cancel()
        await manager.disconnect(lock_id, websocket)
