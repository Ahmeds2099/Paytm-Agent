"""Pydantic response models for the mock Paytm API."""
from __future__ import annotations

from typing import Optional
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
