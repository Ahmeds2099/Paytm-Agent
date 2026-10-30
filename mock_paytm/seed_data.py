"""Mock Paytm API — seed data.

In-memory store of fixtures used by all routes. All IDs are deterministic so
probes can reference them without state management. The refund store is a dict
keyed by txn_id so repeat POST /refund calls are idempotent.
"""
from __future__ import annotations

from datetime import date, timedelta

TODAY = date.today()

QR_STORE: dict[str, dict] = {
    "MID001": {
        "merchant_id": "MID001",
        "qr_status": "active",
        "last_scan_amount": 500.0,
        "last_scan_ts": "2026-10-29T14:32:00Z",
        "issue": None,
    },
    "MID002": {
        "merchant_id": "MID002",
        "qr_status": "inactive",
        "last_scan_amount": None,
        "last_scan_ts": None,
        "issue": "QR code not rendering — contact support",
    },
}

SETTLEMENT_STORE: dict[str, dict] = {
    "TXN001": {
        "txn_id": "TXN001",
        "status": "settled",
        "amount": 1200.50,
        "settled_date": str(TODAY - timedelta(days=1)),
        "expected_date": str(TODAY - timedelta(days=1)),
        "utr": "UTR123456789",
    },
    "TXN002": {
        "txn_id": "TXN002",
        "status": "pending",
        "amount": 750.0,
        "settled_date": None,
        "expected_date": str(TODAY + timedelta(days=1)),
        "utr": None,
    },
    "TXN003": {
        "txn_id": "TXN003",
        "status": "on_hold",
        "amount": 300.0,
        "settled_date": None,
        "expected_date": None,
        "utr": None,
    },
}

# Refund store: txn_id -> result (idempotency: same txn_id always returns same result)
REFUND_STORE: dict[str, dict] = {
    "TXN001": {
        "txn_id": "TXN001",
        "refund_id": "REF-TXN001-001",
        "status": "processed",
        "amount": 1200.50,
        "processed_date": str(TODAY - timedelta(days=1)),
    },
}

SOUNDBOX_STORE: dict[str, dict] = {
    "SB001": {
        "device_id": "SB001",
        "online": True,
        "last_ping": "2026-10-30T09:00:00Z",
        "firmware": "2.3.1",
        "volume_level": 8,
        "issue": None,
    },
    "SB002": {
        "device_id": "SB002",
        "online": False,
        "last_ping": "2026-10-28T17:00:00Z",
        "firmware": "2.2.0",
        "volume_level": None,
        "issue": "Device offline — check power and WiFi",
    },
}

# Refund counter used to generate new refund IDs
_refund_seq: dict[str, int] = {}


def create_refund(txn_id: str, amount: float) -> dict:
    """Create or return the existing refund for txn_id (idempotent)."""
    if txn_id in REFUND_STORE:
        return REFUND_STORE[txn_id]

    seq = _refund_seq.get(txn_id, 1)
    _refund_seq[txn_id] = seq + 1
    result = {
        "txn_id": txn_id,
        "refund_id": f"REF-{txn_id}-{seq:03d}",
        "status": "initiated",
        "amount": amount,
        "processed_date": None,
    }
    REFUND_STORE[txn_id] = result
    return result
