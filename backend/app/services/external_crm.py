import base64
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from app.schemas.external_crm import ExternalCrmAccessCodeResponse


MSK_TZ = timezone(timedelta(hours=3), "MSK")


class InvalidAccessCodeError(Exception):
    pass


class AccessWindowClosedError(Exception):
    pass


class ExternalCrmService:
    _access_url_base = "lockey://open"

    def __init__(self, code_secret: str, early_access_buffer_minutes: int) -> None:
        self._code_secret = code_secret.encode()
        self._early_access_buffer_minutes = early_access_buffer_minutes

    def issue_access_code(
        self,
        lock_id: str,
        booking_starts_at: datetime,
        booking_ends_at: datetime,
    ) -> ExternalCrmAccessCodeResponse:
        starts_at, ends_at = self._normalize_window(booking_starts_at, booking_ends_at)
        access_code = self._build_access_code(lock_id, starts_at, ends_at)
        return ExternalCrmAccessCodeResponse(
            lock_id=lock_id,
            access_code=access_code,
            access_url=self._build_access_url(lock_id, access_code, starts_at, ends_at),
            booking_starts_at=starts_at,
            booking_ends_at=ends_at,
            valid_from=starts_at - timedelta(minutes=self._early_access_buffer_minutes),
            valid_until=ends_at,
        )

    def validate_access_code(
        self,
        lock_id: str,
        access_code: str,
        booking_starts_at: datetime,
        booking_ends_at: datetime,
        *,
        now: datetime | None = None,
    ) -> None:
        access = self.issue_access_code(lock_id, booking_starts_at, booking_ends_at)
        self._ensure_access_code_matches(access_code, access.access_code)
        self.ensure_access_window_is_open(
            valid_from=access.valid_from,
            valid_until=access.valid_until,
            now=now,
        )

    def validate_access_code_signature(
        self,
        *,
        lock_id: str,
        access_code: str,
        booking_starts_at: datetime,
        booking_ends_at: datetime,
    ) -> None:
        expected_code = self.issue_access_code(lock_id, booking_starts_at, booking_ends_at).access_code
        self._ensure_access_code_matches(access_code, expected_code)

    def ensure_access_window_is_open(
        self,
        *,
        valid_from: datetime,
        valid_until: datetime,
        now: datetime | None = None,
    ) -> None:
        valid_from = self._normalize_datetime(valid_from)
        valid_until = self._normalize_datetime(valid_until)
        current_time = self._normalize_datetime(now or datetime.now(MSK_TZ))

        if current_time < valid_from or current_time > valid_until:
            raise AccessWindowClosedError("Booking access window is closed")

    def _build_access_code(
        self,
        lock_id: str,
        booking_starts_at: datetime,
        booking_ends_at: datetime,
    ) -> str:
        payload = f"{lock_id}|{booking_starts_at.isoformat()}|{booking_ends_at.isoformat()}"
        digest = hmac.new(
            self._code_secret,
            payload.encode(),
            hashlib.sha256,
        ).digest()
        return base64.b32encode(digest).decode().rstrip("=")[:10]

    def _build_access_url(
        self,
        lock_id: str,
        access_code: str,
        booking_starts_at: datetime,
        booking_ends_at: datetime,
    ) -> str:
        query = urlencode(
            {
                "lock_id": lock_id,
                "access_code": access_code,
                "booking_starts_at": self._format_url_datetime(booking_starts_at),
                "booking_ends_at": self._format_url_datetime(booking_ends_at),
            },
            safe=":-",
        )
        return f"{self._access_url_base}?{query}"

    def _format_url_datetime(self, value: datetime) -> str:
        return value.isoformat()

    def _ensure_access_code_matches(self, access_code: str, expected_code: str) -> None:
        if not hmac.compare_digest(access_code, expected_code):
            raise InvalidAccessCodeError("Access code is invalid")

    def _normalize_window(self, starts_at: datetime, ends_at: datetime) -> tuple[datetime, datetime]:
        return self._normalize_datetime(starts_at), self._normalize_datetime(ends_at)

    def _normalize_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=MSK_TZ)
        return value.astimezone(MSK_TZ)
