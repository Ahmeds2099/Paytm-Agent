from fastapi import APIRouter
from mock_paytm.models import (
    RefundApprovalRequest,
    RefundApprovalResult,
    RefundRequest,
    RefundResult,
)
from mock_paytm.seed_data import create_refund, create_refund_approval

router = APIRouter(prefix="/refund", tags=["Refund"])


@router.post("", response_model=RefundResult)
def trigger_refund(request: RefundRequest):
    """Idempotent: same txn_id always returns the same refund result."""
    result = create_refund(request.txn_id, request.amount)
    return RefundResult(**result)


@router.post("/approval", response_model=RefundApprovalResult)
def request_refund_approval(request: RefundApprovalRequest):
    """Queue a refund for approval without initiating a funds transfer."""
    result = create_refund_approval(
        request.txn_id,
        request.amount,
        request.merchant_id,
        request.transaction_date,
    )
    return RefundApprovalResult(**result)
