import asyncio
import hashlib
import hmac
import time
from dataclasses import dataclass, field
from uuid import uuid4

from fastapi import WebSocket

from app.schemas.locks import OpenLockResponse
from app.schemas.ws import CodeMessage, OpenMessage


class LockNotConnectedError(Exception):
    pass


class InvalidLockCodeError(Exception):
    pass


@dataclass(slots=True)
class LockConnection:
    websocket: WebSocket
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class LockManager:
    def __init__(
        self,
        qr_secret: str,
        qr_step_seconds: int,
        qr_allowed_drift_steps: int = 1,
    ) -> None:
        self._connections: dict[str, LockConnection] = {}
        self._lock = asyncio.Lock()
        self._qr_secret = qr_secret
        self._qr_step_seconds = qr_step_seconds
        self._qr_allowed_drift_steps = qr_allowed_drift_steps

    async def connect(self, lock_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[lock_id] = LockConnection(websocket=websocket)

    async def disconnect(self, lock_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            connection = self._connections.get(lock_id)
            if connection is not None and connection.websocket is websocket:
                self._connections.pop(lock_id, None)

    async def open_lock(self, lock_id: str) -> OpenLockResponse:
        command_id = str(uuid4())
        await self._send_to_lock(lock_id, OpenMessage(command_id=command_id).model_dump())
        return OpenLockResponse(status="sent", lock_id=lock_id, command_id=command_id)

    def validate_lock_code(self, lock_id: str, code: str) -> None:
        expected_codes = {
            self._build_code(lock_id, self._current_step_timestamp() + (offset * self._qr_step_seconds))
            for offset in range(-self._qr_allowed_drift_steps, self._qr_allowed_drift_steps + 1)
        }
        if code.upper() not in expected_codes:
            raise InvalidLockCodeError("Lock code is invalid or expired")

    async def push_codes(self, lock_id: str, websocket: WebSocket) -> None:
        sent_step: int | None = None
        while True:
            step = self._current_step_timestamp()
            if step != sent_step:
                await self._send_code(lock_id, websocket, step)
                sent_step = step
            await asyncio.sleep(1)

    async def _send_code(self, lock_id: str, websocket: WebSocket, step: int) -> None:
        code = self._build_code(lock_id, step)
        expires_at = step + self._qr_step_seconds
        await self._send_json(
            websocket,
            CodeMessage(value=code, expires_at=expires_at).model_dump(),
        )

    async def _send_to_lock(self, lock_id: str, payload: dict[str, str]) -> None:
        async with self._lock:
            connection = self._connections.get(lock_id)

        if connection is None:
            raise LockNotConnectedError("Lock is offline")

        await self._send_json(connection.websocket, payload, connection.send_lock)

    async def _send_json(
        self,
        websocket: WebSocket,
        payload: dict[str, str | int],
        send_lock: asyncio.Lock | None = None,
    ) -> None:
        lock = send_lock
        if lock is None:
            async with self._lock:
                connection = next(
                    (item for item in self._connections.values() if item.websocket is websocket),
                    None,
                )
            if connection is None:
                raise LockNotConnectedError("Lock is offline")
            lock = connection.send_lock

        async with lock:
            await websocket.send_json(payload)

    def _build_code(self, lock_id: str, issued_at: int) -> str:
        message = f"{lock_id}:{issued_at}"
        return hmac.new(
            self._qr_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()[:6].upper()

    def _current_step_timestamp(self) -> int:
        return int(time.time()) // self._qr_step_seconds * self._qr_step_seconds
