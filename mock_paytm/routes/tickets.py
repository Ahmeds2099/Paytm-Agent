from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from mock_paytm.models import TicketRequest, TicketResult
from mock_paytm.seed_data import TICKET_ETA_HOURS, create_ticket

router = APIRouter(prefix="/ticket", tags=["Tickets"])


@router.post("", response_model=TicketResult)
def raise_ticket(request: TicketRequest):
    if request.issue_type not in TICKET_ETA_HOURS:
        raise HTTPException(status_code=422, detail="Unsupported ticket issue type")
    ticket = create_ticket(
        merchant_id=request.merchant_id,
        issue_type=request.issue_type,
        description=request.description,
        priority=request.priority,
    )
    return TicketResult(
        **ticket,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
