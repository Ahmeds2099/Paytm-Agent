"""Merchant fixtures and conversation context for repeatable voice demos."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

_TODAY = date.today()

MERCHANTS: tuple[dict[str, Any], ...] = (
    {
        "merchant_id": "MID001",
        "name": "Ravi Kumar",
        "business_name": "Ravi General Store",
        "city": "Bengaluru",
        "phone": "+91 98441 12345",
        "language": "kn-IN",
        "language_display": "Kannada",
        "avatar": "🏪",
        "scenario_id": "qr_inactive",
        "scenario_label": "QR Not Working",
        "scenario_description": "The merchant's QR code is inactive. Explain the issue and offer support; only confirm a ticket after it is created.",
        "member_since": "Jan 2023",
        "total_transactions": 847,
        "account_balance": "₹12,450",
        "open_tickets": 1,
        "transaction_id": None,
        "transaction_amount": None,
        "transaction_status": None,
        "transaction_date": None,
        "expected_date": None,
        "device_id": None,
    },
    {
        "merchant_id": "MID002",
        "name": "Sunita Devi",
        "business_name": "Sunita Sarees",
        "city": "Patna",
        "phone": "+91 98350 23456",
        "language": "hi-IN",
        "language_display": "Hindi",
        "avatar": "👗",
        "scenario_id": "settlement_pending",
        "scenario_label": "Pending Settlement · Priority Follow-up",
        "scenario_description": "TXN002 for ₹750 is pending and expected the next day. Ask about it to hear the status and be offered a priority support ticket.",
        "member_since": "Mar 2022",
        "total_transactions": 1240,
        "account_balance": "₹8,750",
        "open_tickets": 0,
        "transaction_id": "TXN002",
        "transaction_amount": 750.0,
        "transaction_status": "pending",
        "transaction_date": str(_TODAY),
        "expected_date": str(_TODAY + timedelta(days=1)),
        "device_id": None,
    },
    {
        "merchant_id": "MID003",
        "name": "Mohammed Farooq",
        "business_name": "Farooq Electronics",
        "city": "Hyderabad",
        "phone": "+91 98490 34567",
        "language": "en-IN",
        "language_display": "English",
        "avatar": "📱",
        "scenario_id": "soundbox_offline",
        "scenario_label": "Soundbox Offline",
        "scenario_description": "Soundbox SB002 is offline. Try power, Wi-Fi, and a five-second reset; if it stays offline, ask for support follow-up.",
        "member_since": "Jun 2021",
        "total_transactions": 2134,
        "account_balance": "₹24,100",
        "open_tickets": 0,
        "transaction_id": None,
        "transaction_amount": None,
        "transaction_status": None,
        "transaction_date": None,
        "expected_date": None,
        "device_id": "SB002",
    },
    {
        "merchant_id": "MID004",
        "name": "Lakshmi Venkat",
        "business_name": "Lakshmi Textiles",
        "city": "Chennai",
        "phone": "+91 98400 45678",
        "language": "en-IN",
        "language_display": "English",
        "avatar": "🧵",
        "scenario_id": "refund_pending",
        "scenario_label": "Refund Not Initiated",
        "scenario_description": "Confirm the recent ₹2,400 transaction with the merchant. Any refund request needs human approval; do not claim a refund was issued.",
        "member_since": "Feb 2020",
        "total_transactions": 3081,
        "account_balance": "₹31,600",
        "open_tickets": 0,
        "transaction_id": "TXN004",
        "transaction_amount": 2400.0,
        "transaction_status": "settled",
        "transaction_date": str(_TODAY),
        "expected_date": str(_TODAY),
        "device_id": None,
        "recommended": True,
    },
    {
        "merchant_id": "MID005",
        "name": "Amit Sharma",
        "business_name": "Amit Kirana",
        "city": "Delhi",
        "phone": "+91 98100 56789",
        "language": "hi-IN",
        "language_display": "Hindi",
        "avatar": "🏬",
        "scenario_id": "repeated_escalation",
        "scenario_label": "Repeated Complaint",
        "scenario_description": "TXN003 for ₹300 is on hold and two support tickets are open. The first repeated complaint gets an empathetic response; a second consecutive repeat triggers human escalation.",
        "member_since": "Oct 2022",
        "total_transactions": 986,
        "account_balance": "₹5,200",
        "open_tickets": 2,
        "transaction_id": "TXN003",
        "transaction_amount": 300.0,
        "transaction_status": "on_hold",
        "transaction_date": str(_TODAY - timedelta(days=2)),
        "expected_date": None,
        "device_id": None,
    },
    {
        "merchant_id": "MID006",
        "name": "Priya Nair",
        "business_name": "Priya Beauty Parlour",
        "city": "Kochi",
        "phone": "+91 98470 67890",
        "language": "en-IN",
        "language_display": "English",
        "avatar": "💄",
        "scenario_id": "opt_out",
        "scenario_label": "Promotional Loan Offer · Opt Out",
        "scenario_description": "An outbound promotional loan offer. After the language choice, present the offer; if the merchant declines or asks to be removed, stop and record the opt-out.",
        "member_since": "May 2024",
        "total_transactions": 412,
        "account_balance": "₹6,400",
        "open_tickets": 0,
        "transaction_id": None,
        "transaction_amount": None,
        "transaction_status": None,
        "transaction_date": None,
        "expected_date": None,
        "device_id": None,
    },
)

_BY_ID = {merchant["merchant_id"]: merchant for merchant in MERCHANTS}

_SCENARIO_GUIDANCE = {
    "qr_inactive": (
        "For an inactive QR, explain the status plainly and create a support "
        "ticket. Only confirm ticket creation after the ticket tool succeeds."
    ),
    "settlement_pending": (
        "Explain that TXN002 is ₹750 and is expected tomorrow. Acknowledge "
        "urgency and offer a priority ticket. If the merchant agrees, the "
        "priority ticket is created by the next confirmation turn."
    ),
    "soundbox_offline": (
        "For SB002, explain it is offline. Ask the merchant to check power and "
        "Wi-Fi, then guide them to hold the rear reset button for five seconds. "
        "If it remains offline, offer support follow-up rather than claiming it "
        "was fixed."
    ),
    "refund_pending": (
        "For TXN004, confirm the ₹2,400 transaction with the merchant before "
        "initiating a refund. Clearly state the refund ID and 5–7 business day "
        "ETA only after the refund tool succeeds."
    ),
    "repeated_escalation": (
        "TXN003 is a ₹300 settlement on hold and the merchant already has two "
        "open support tickets. Acknowledge the first repeat complaint with "
        "empathy. The intent handler automatically escalates after a second "
        "consecutive repeat complaint. If a human is requested before the "
        "merchant explains the issue, first ask what needs resolving; escalate "
        "if they renew the request. Never claim a human has joined unless that "
        "handoff actually occurs."
    ),
    "opt_out": (
        "This is an outbound promotional loan-offer call. After the language "
        "gate, state the offer. If the merchant declines or requests removal, "
        "stop the offer immediately, record local demo DNC suppression, and "
        "close the call."
    ),
}


def get_scenario(merchant_id: str) -> dict[str, Any] | None:
    merchant = _BY_ID.get(merchant_id)
    if merchant is None:
        return None
    return {
        **merchant,
        "prompt_context": (
            f"You are making an outbound Paytm support call to {merchant['name']} "
            f"at {merchant['business_name']} in {merchant['city']}. Their demo "
            f"scenario is {merchant['scenario_label']}. Use the matching merchant "
            "account data and available tools; never claim an action succeeded "
            "unless its tool result confirms it. Keep the conversation natural "
            "and in the merchant's chosen language. "
            f"{_SCENARIO_GUIDANCE[merchant['scenario_id']]}"
        ),
    }


def list_merchants() -> list[dict[str, Any]]:
    return [dict(merchant) for merchant in MERCHANTS]
