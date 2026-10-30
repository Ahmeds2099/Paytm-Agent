from fastapi import APIRouter, HTTPException, Query

from app.services.call_log import get_call, list_calls

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/calls")
def admin_calls(since: str | None = Query(default=None)):
    return list_calls(since=since)


@router.get("/calls/{call_id}")
def admin_call_detail(call_id: str):
    record = get_call(call_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Call record not found")
    return record
