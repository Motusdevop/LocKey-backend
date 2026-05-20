import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.offline_tickets import OfflineTicketIssueResponse, OfflineTicketVerifyResponse


class InvalidOfflineTicketError(Exception):
    pass


class OfflineTicketInactiveError(Exception):
    pass


class OfflineTicketLockMismatchError(Exception):
    pass


class OfflineTicketService:
    _TICKET_VERSION = "ot1"
    _PAYLOAD_VERSION = 1
    _REQUIRED_FIELDS = {"issued_at", "lock_id", "ticket_id", "v", "valid_from", "valid_until"}

    def __init__(self, secret: str, allowed_time_drift_seconds: int = 60) -> None:
        self._secret = secret.encode()
        self._allowed_time_drift_seconds = allowed_time_drift_seconds

    def issue_ticket(
        self,
        *,
        lock_id: str,
        valid_from: datetime,
        valid_until: datetime,
        issued_at: datetime | None = None,
    ) -> OfflineTicketIssueResponse:
        normalized_valid_from = self._normalize_datetime(valid_from)
        normalized_valid_until = self._normalize_datetime(valid_until)
        normalized_issued_at = self._normalize_datetime(issued_at or datetime.now(timezone.utc))
        ticket_id = str(uuid4())

        payload = {
            "issued_at": int(normalized_issued_at.timestamp()),
            "lock_id": lock_id,
            "ticket_id": ticket_id,
            "v": self._PAYLOAD_VERSION,
            "valid_from": int(normalized_valid_from.timestamp()),
            "valid_until": int(normalized_valid_until.timestamp()),
        }
        payload_b64 = self._urlsafe_encode(self._canonicalize_payload(payload))
        signature = self._sign_payload(payload_b64)
        offline_ticket = f"{self._TICKET_VERSION}.{payload_b64}.{signature}"

        return OfflineTicketIssueResponse(
            ticket_id=ticket_id,
            lock_id=lock_id,
            offline_ticket=offline_ticket,
            issued_at=normalized_issued_at,
            valid_from=normalized_valid_from,
            valid_until=normalized_valid_until,
        )

    def verify_ticket(
        self,
        *,
        lock_id: str,
        offline_ticket: str,
        now: datetime | None = None,
    ) -> OfflineTicketVerifyResponse:
        payload = self._parse_ticket(offline_ticket)
        if payload.get("lock_id") != lock_id:
            raise OfflineTicketLockMismatchError("Offline ticket lock_id does not match request")

        current_time = int(self._normalize_datetime(now or datetime.now(timezone.utc)).timestamp())
        valid_from = int(payload["valid_from"])
        valid_until = int(payload["valid_until"])
        drift = self._allowed_time_drift_seconds

        if current_time < valid_from - drift or current_time > valid_until + drift:
            raise OfflineTicketInactiveError("Offline ticket is not active")

        return OfflineTicketVerifyResponse(
            ticket_id=str(payload["ticket_id"]),
            lock_id=str(payload["lock_id"]),
            issued_at=self._datetime_from_timestamp(int(payload["issued_at"])),
            valid_from=self._datetime_from_timestamp(valid_from),
            valid_until=self._datetime_from_timestamp(valid_until),
        )

    def _parse_ticket(self, offline_ticket: str) -> dict[str, int | str]:
        try:
            version, payload_b64, signature = offline_ticket.split(".")
        except ValueError as exc:
            raise InvalidOfflineTicketError("Offline ticket format is invalid") from exc

        if version != self._TICKET_VERSION:
            raise InvalidOfflineTicketError("Offline ticket version is invalid")
        if not hmac.compare_digest(signature, self._sign_payload(payload_b64)):
            raise InvalidOfflineTicketError("Offline ticket signature is invalid")
        return self._decode_payload(payload_b64)

    def _canonicalize_payload(self, payload: dict[str, int | str]) -> bytes:
        return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()

    def _decode_payload(self, payload_b64: str) -> dict[str, int | str]:
        try:
            payload_json = self._urlsafe_decode(payload_b64)
            payload = json.loads(payload_json)
        except (ValueError, json.JSONDecodeError) as exc:
            raise InvalidOfflineTicketError("Offline ticket payload is invalid") from exc

        if not self._REQUIRED_FIELDS.issubset(payload):
            raise InvalidOfflineTicketError("Offline ticket payload is incomplete")
        if payload.get("v") != self._PAYLOAD_VERSION:
            raise InvalidOfflineTicketError("Offline ticket payload version is invalid")
        return payload

    def _sign_payload(self, payload_b64: str) -> str:
        digest = hmac.new(self._secret, payload_b64.encode(), hashlib.sha256).digest()
        return self._urlsafe_encode(digest)

    def _urlsafe_encode(self, value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode().rstrip("=")

    def _urlsafe_decode(self, value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(value + padding)

    def _datetime_from_timestamp(self, value: int) -> datetime:
        return datetime.fromtimestamp(value, tz=timezone.utc)

    def _normalize_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
