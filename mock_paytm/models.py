"""Pydantic response models for the mock Paytm API."""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel


class QrStatus(BaseModel):
    merchant_id: str
    qr_status: str          # "active" | "inactive" | "suspended"
    last_scan_amount: Optional[float] = None
    last_scan_ts: Optional[str] = None
    issue: Optional[str] = None


class SettlementStatus(BaseModel):
    txn_id: str
    status: str             # "settled" | "pending" | "on_hold" | "failed"
    amount: float
    settled_date: Optional[str] = None
    expected_date: Optional[str] = None
    utr: Optional[str] = None


class RefundRequest(BaseModel):
    txn_id: str
    amount: float


class RefundResult(BaseModel):
    txn_id: str
    refund_id: str
    status: str             # "processed" | "initiated" | "failed"
    amount: float
    processed_date: Optional[str] = None


class RefundApprovalRequest(BaseModel):
    txn_id: str
    amount: float
    merchant_id: str
    transaction_date: Optional[str] = None


class RefundApprovalResult(BaseModel):
    approval_id: str
    txn_id: str
    amount: float
    merchant_id: str
    transaction_date: Optional[str] = None
    status: str
    created_at: str


class TicketRequest(BaseModel):
    merchant_id: str
    issue_type: str
    description: str = ""
    priority: Literal["normal", "high"] = "normal"


class TicketResult(BaseModel):
    ticket_id: str
    merchant_id: str
    issue_type: str
    description: str
    priority: str
    status: str
    eta_hours: int
    created_at: str


class SoundboxHealth(BaseModel):
    device_id: str
    online: bool
    last_ping: Optional[str] = None
    firmware: Optional[str] = None
    volume_level: Optional[int] = None
    issue: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
