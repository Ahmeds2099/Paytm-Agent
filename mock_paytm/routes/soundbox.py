from fastapi import APIRouter, HTTPException
from mock_paytm.models import SoundboxHealth
from mock_paytm.seed_data import SOUNDBOX_STORE

router = APIRouter(prefix="/soundbox", tags=["Soundbox"])


@router.get("/{device_id}", response_model=SoundboxHealth)
def get_soundbox_health(device_id: str):
    record = SOUNDBOX_STORE.get(device_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Device {device_id!r} not found")
    return SoundboxHealth(**record)
