from typing import Literal

from pydantic import BaseModel


class CodeMessage(BaseModel):
    type: Literal["code"] = "code"
    value: str
    expires_at: int


class OpenMessage(BaseModel):
    type: Literal["open"] = "open"
    command_id: str


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    detail: str
