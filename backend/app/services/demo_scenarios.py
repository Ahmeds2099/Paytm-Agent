"""Merchant fixtures and conversation context for repeatable voice demos."""
from __future__ import annotations

from typing import Any


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
        "member_since": "Jan 2023",
        "total_transactions": 847,
        "account_balance": "₹12,450",
        "open_tickets": 1,
        "transaction_id": None,
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
        "scenario_label": "Settlement Delayed",
        "member_since": "Mar 2022",
        "total_transactions": 1240,
        "account_balance": "₹8,750",
        "open_tickets": 0,
        "transaction_id": "TXN002",
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
        "member_since": "Jun 2021",
        "total_transactions": 2134,
        "account_balance": "₹24,100",
        "open_tickets": 0,
        "transaction_id": None,
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
        "member_since": "Feb 2020",
        "total_transactions": 3081,
        "account_balance": "₹31,600",
        "open_tickets": 0,
        "transaction_id": "TXN004",
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
        "member_since": "Oct 2022",
        "total_transactions": 986,
        "account_balance": "₹5,200",
        "open_tickets": 2,
        "transaction_id": "TXN003",
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
        "member_since": "May 2024",
        "total_transactions": 412,
        "account_balance": "₹6,400",
        "open_tickets": 0,
        "transaction_id": None,
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
        "Acknowledge the repeat settlement complaint with empathy. Escalate "
        "when the merchant asks for a senior colleague; never claim a human "
        "has joined unless that handoff actually occurs."
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
