from fastapi import APIRouter, HTTPException
from mock_paytm.models import QrStatus
from mock_paytm.seed_data import QR_STORE

router = APIRouter(prefix="/qr", tags=["QR"])


@router.get("/{merchant_id}", response_model=QrStatus)
def get_qr_status(merchant_id: str):
    record = QR_STORE.get(merchant_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Merchant {merchant_id!r} not found")
    return QrStatus(**record)
