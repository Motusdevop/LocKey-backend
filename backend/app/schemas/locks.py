from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class OpenLockResponse(BaseModel):
    status: Literal["sent"]
    lock_id: str
    command_id: str


class VerifyLockAccessRequest(BaseModel):
    access_code: str = Field(min_length=1)
    lock_code: str = Field(min_length=1)
    booking_starts_at: datetime
    booking_ends_at: datetime

    @model_validator(mode="after")
    def validate_booking_window(self) -> "VerifyLockAccessRequest":
        if self.booking_ends_at <= self.booking_starts_at:
            raise ValueError("booking_ends_at must be greater than booking_starts_at")
        return self
