from fastapi import APIRouter

from app.services.demo_opt_out import is_opted_out, list_opted_out
from app.services.demo_scenarios import list_merchants

router = APIRouter(prefix="/demo", tags=["Demo"])


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
