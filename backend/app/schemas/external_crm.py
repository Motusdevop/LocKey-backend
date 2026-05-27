from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class ExternalCrmAccessCodeRequest(BaseModel):
    lock_id: str = Field(min_length=1)
    booking_starts_at: datetime
    booking_ends_at: datetime

    @model_validator(mode="after")
    def validate_booking_window(self) -> "ExternalCrmAccessCodeRequest":
        if self.booking_ends_at <= self.booking_starts_at:
            raise ValueError("booking_ends_at must be greater than booking_starts_at")
        return self


class ExternalCrmAccessCodeResponse(BaseModel):
    lock_id: str
    access_code: str
    access_url: str
    booking_starts_at: datetime
    booking_ends_at: datetime
    valid_from: datetime
    valid_until: datetime
