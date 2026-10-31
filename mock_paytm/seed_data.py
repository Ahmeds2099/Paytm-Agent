"""Mock Paytm API — seed data.

In-memory store of fixtures used by all routes. All IDs are deterministic so
probes can reference them without state management. The refund store is a dict
keyed by txn_id so repeat POST /refund calls are idempotent.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from threading import Lock
from uuid import uuid4

TODAY = date.today()

QR_STORE: dict[str, dict] = {
    "MID001": {
        "merchant_id": "MID001",
        "qr_status": "inactive",
        "last_scan_amount": None,
        "last_scan_ts": None,
        "issue": "QR code not rendering — contact support",
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
    "TXN004": {
        "txn_id": "TXN004",
        "status": "settled",
        "amount": 2400.0,
        "settled_date": str(TODAY),
        "expected_date": str(TODAY),
        "utr": "UTR0042400",
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
REFUND_APPROVAL_STORE: dict[str, dict] = {}
_refund_approval_lock = Lock()


def create_refund_approval(
    txn_id: str,
    amount: float,
    merchant_id: str,
    transaction_date: str | None = None,
) -> dict:
    with _refund_approval_lock:
        record = {
            "approval_id": f"REF-APP-{uuid4().hex[:8].upper()}",
            "txn_id": txn_id,
            "amount": amount,
            "merchant_id": merchant_id,
            "transaction_date": transaction_date,
            "status": "pending_approval",
            "created_at": date.today().isoformat(),
        }
        REFUND_APPROVAL_STORE[record["approval_id"]] = record
        return dict(record)

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

# Ticket records are deterministic demo data and kept in memory like the other
# mock API fixtures.
TICKET_STORE: dict[str, dict] = {
    "TICKET-PRIOR-001": {
        "ticket_id": "TICKET-PRIOR-001",
        "merchant_id": "MID005",
        "issue_type": "settlement_delayed",
        "description": "Prior settlement follow-up",
        "priority": "normal",
        "status": "open",
        "eta_hours": 24,
    },
    "TICKET-PRIOR-002": {
        "ticket_id": "TICKET-PRIOR-002",
        "merchant_id": "MID005",
        "issue_type": "settlement_delayed",
        "description": "Repeated settlement follow-up",
        "priority": "normal",
        "status": "open",
        "eta_hours": 24,
    },
}
_ticket_lock = Lock()
_ticket_seq = 0
TICKET_ETA_HOURS = {
    "qr_inactive": 4,
    "settlement_delayed": 24,
    "soundbox_offline": 8,
    "refund_failed": 48,
    "escalation": 1,
}


def create_ticket(
    merchant_id: str,
    issue_type: str,
    description: str = "",
    priority: str = "normal",
) -> dict:
    global _ticket_seq
    with _ticket_lock:
        _ticket_seq += 1
        ticket_id = f"TICKET-{_ticket_seq:03d}"
        record = {
            "ticket_id": ticket_id,
            "merchant_id": merchant_id,
            "issue_type": issue_type,
            "description": description,
            "priority": priority,
            "status": "open",
            "eta_hours": TICKET_ETA_HOURS[issue_type],
        }
        TICKET_STORE[ticket_id] = record
        return dict(record)


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


_INITIAL_QR_STORE = deepcopy(QR_STORE)
_INITIAL_SETTLEMENT_STORE = deepcopy(SETTLEMENT_STORE)
_INITIAL_REFUND_STORE = deepcopy(REFUND_STORE)
_INITIAL_SOUNDBOX_STORE = deepcopy(SOUNDBOX_STORE)
_INITIAL_TICKET_STORE = deepcopy(TICKET_STORE)


def reset_demo_fixtures() -> None:
    global _ticket_seq
    for store, initial in (
        (QR_STORE, _INITIAL_QR_STORE),
        (SETTLEMENT_STORE, _INITIAL_SETTLEMENT_STORE),
        (REFUND_STORE, _INITIAL_REFUND_STORE),
        (SOUNDBOX_STORE, _INITIAL_SOUNDBOX_STORE),
        (TICKET_STORE, _INITIAL_TICKET_STORE),
    ):
        store.clear()
        store.update(deepcopy(initial))
    REFUND_APPROVAL_STORE.clear()
    _refund_seq.clear()
    _ticket_seq = 0
