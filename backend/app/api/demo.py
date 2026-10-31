import logging

import httpx
from fastapi import APIRouter
from fastapi import HTTPException

from app.core.config import settings
from app.services.call_log import reset_calls
from app.services.demo_opt_out import is_opted_out, list_opted_out
from app.services.demo_opt_out import reset_opt_outs
from app.services.demo_scenarios import list_merchants

router = APIRouter(prefix="/demo", tags=["Demo"])
_log = logging.getLogger(__name__)


@router.get("/merchants")
def demo_merchants():
    opted_out = list_opted_out()
    return [
        {**merchant, "opted_out": merchant["merchant_id"] in opted_out}
        for merchant in list_merchants()
    ]


@router.get("/merchants/{merchant_id}/eligibility")
def merchant_eligibility(merchant_id: str):
    return {"merchant_id": merchant_id, "opted_out": is_opted_out(merchant_id)}


@router.post("/reset")
def reset_demo():
    if not settings.DEMO_RESET_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Demo reset is only available in development.",
        )
    try:
        response = httpx.post(
            f"{settings.MOCK_PAYTM_URL.rstrip('/')}/demo/reset",
            timeout=3.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        _log.exception("Could not reset mock Paytm demo data")
        raise HTTPException(
            status_code=503,
            detail="Could not reset mock Paytm data. Ensure the mock API is running.",
        ) from exc
    reset_calls()
    reset_opt_outs()
    return {"status": "reset"}
