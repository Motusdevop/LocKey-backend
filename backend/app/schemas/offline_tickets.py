from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class OfflineTicketIssueRequest(BaseModel):
    lock_id: str = Field(min_length=1)
    access_code: str = Field(min_length=1)
    booking_starts_at: datetime
    booking_ends_at: datetime

    @model_validator(mode="after")
    def validate_booking_window(self) -> "OfflineTicketIssueRequest":
        if self.booking_ends_at <= self.booking_starts_at:
            raise ValueError("booking_ends_at must be greater than booking_starts_at")
        return self


class OfflineTicketIssueResponse(BaseModel):
    ticket_id: str
    lock_id: str
    offline_ticket: str
    issued_at: datetime
    valid_from: datetime
    valid_until: datetime


class OfflineTicketVerifyRequest(BaseModel):
    lock_id: str = Field(min_length=1)
    offline_ticket: str = Field(min_length=1)


class OfflineTicketVerifyResponse(BaseModel):
    status: str = "valid"
    ticket_id: str
    lock_id: str
    issued_at: datetime
    valid_from: datetime
    valid_until: datetime
