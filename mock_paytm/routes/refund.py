from fastapi import APIRouter
from mock_paytm.models import RefundRequest, RefundResult
from mock_paytm.seed_data import create_refund

router = APIRouter(prefix="/refund", tags=["Refund"])


@router.post("", response_model=RefundResult)
def trigger_refund(request: RefundRequest):
    """Idempotent: same txn_id always returns the same refund result."""
    result = create_refund(request.txn_id, request.amount)
    return RefundResult(**result)
