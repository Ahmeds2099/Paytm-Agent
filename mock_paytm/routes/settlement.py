from fastapi import APIRouter, HTTPException
from mock_paytm.models import SettlementStatus
from mock_paytm.seed_data import SETTLEMENT_STORE

router = APIRouter(prefix="/settlement", tags=["Settlement"])


@router.get("/{txn_id}", response_model=SettlementStatus)
def get_settlement_status(txn_id: str):
    record = SETTLEMENT_STORE.get(txn_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Transaction {txn_id!r} not found")
    return SettlementStatus(**record)
