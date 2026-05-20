from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

_ACCESS_TESTER_PATH = Path(__file__).resolve().parents[2] / "static" / "access_tester.html"


@router.get("/debug/access-tester", response_class=FileResponse)
async def access_tester() -> FileResponse:
    return FileResponse(_ACCESS_TESTER_PATH)
