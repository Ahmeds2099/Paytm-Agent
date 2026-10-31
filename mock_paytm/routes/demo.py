from fastapi import APIRouter

from mock_paytm.seed_data import reset_demo_fixtures

router = APIRouter(prefix="/demo", tags=["Demo"])


@router.post("/reset")
def reset_demo():
    reset_demo_fixtures()
    return {"status": "reset"}
