"""Paytm tool layer — Phase 4.

Four idempotent tools that call the mock Paytm API (or a real one, configured
via MOCK_PAYTM_URL). Each tool:

- carries a 3 s timeout
- returns a typed ToolResult on success or on network/API failure
- never raises — callers always get a result, but may get status="error"

Import only these public helpers:
    lookup_qr(merchant_id)
    settlement_status(txn_id)
    trigger_refund(txn_id, amount)
    soundbox_health(device_id)
    raise_ticket(merchant_id, issue_type, description="", priority="normal")
    spoken_summary(result) -> str
    spoken_summary_for_language(result, language, llm=None) -> str
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import settings

_log = logging.getLogger(__name__)

_TIMEOUT = 3.0  # seconds


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class ToolResult:
    tool: str
    status: str              # "ok" | "not_found" | "error"
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "ok"


# ---------------------------------------------------------------------------
# Internal HTTP helpers
# ---------------------------------------------------------------------------

def _get(path: str) -> dict:
    url = settings.MOCK_PAYTM_URL.rstrip("/") + path
    resp = httpx.get(url, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _post(path: str, payload: dict) -> dict:
    url = settings.MOCK_PAYTM_URL.rstrip("/") + path
    resp = httpx.post(url, json=payload, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Public tools
# ---------------------------------------------------------------------------

def lookup_qr(merchant_id: str) -> ToolResult:
    """Look up QR code status for a merchant."""
    try:
        data = _get(f"/qr/{merchant_id}")
        return ToolResult(tool="lookup_qr", status="ok", data=data)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return ToolResult(tool="lookup_qr", status="not_found",
                              error=f"Merchant {merchant_id!r} not found")
        return ToolResult(tool="lookup_qr", status="error", error=str(exc))
    except Exception as exc:  # noqa: BLE001
        _log.warning("[paytm_tools] lookup_qr failed: %s", exc)
        return ToolResult(tool="lookup_qr", status="error", error=str(exc))


def settlement_status(txn_id: str) -> ToolResult:
    """Get settlement status for a transaction."""
    try:
        data = _get(f"/settlement/{txn_id}")
        return ToolResult(tool="settlement_status", status="ok", data=data)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return ToolResult(tool="settlement_status", status="not_found",
                              error=f"Transaction {txn_id!r} not found")
        return ToolResult(tool="settlement_status", status="error", error=str(exc))
    except Exception as exc:  # noqa: BLE001
        _log.warning("[paytm_tools] settlement_status failed: %s", exc)
        return ToolResult(tool="settlement_status", status="error", error=str(exc))


def trigger_refund(txn_id: str, amount: float) -> ToolResult:
    """Initiate or retrieve a refund for a transaction (idempotent on txn_id)."""
    try:
        data = _post("/refund", {"txn_id": txn_id, "amount": amount})
        return ToolResult(tool="trigger_refund", status="ok", data=data)
    except httpx.HTTPStatusError as exc:
        return ToolResult(tool="trigger_refund", status="error", error=str(exc))
    except Exception as exc:  # noqa: BLE001
        _log.warning("[paytm_tools] trigger_refund failed: %s", exc)
        return ToolResult(tool="trigger_refund", status="error", error=str(exc))


def request_refund_approval(
    txn_id: str,
    amount: float,
    merchant_id: str,
    transaction_date: str | None = None,
) -> ToolResult:
    """Create an approval request without moving funds or initiating a refund."""
    try:
        data = _post(
            "/refund/approval",
            {
                "txn_id": txn_id,
                "amount": amount,
                "merchant_id": merchant_id,
                "transaction_date": transaction_date,
            },
        )
        return ToolResult(tool="refund_approval_request", status="ok", data=data)
    except httpx.HTTPStatusError as exc:
        return ToolResult(
            tool="refund_approval_request",
            status="error",
            error=str(exc),
        )
    except Exception as exc:  # noqa: BLE001
        _log.warning("[paytm_tools] refund approval request failed: %s", exc)
        return ToolResult(
            tool="refund_approval_request",
            status="error",
            error=str(exc),
        )


def soundbox_health(device_id: str) -> ToolResult:
    """Check soundbox connectivity and health."""
    try:
        data = _get(f"/soundbox/{device_id}")
        return ToolResult(tool="soundbox_health", status="ok", data=data)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return ToolResult(tool="soundbox_health", status="not_found",
                              error=f"Device {device_id!r} not found")
        return ToolResult(tool="soundbox_health", status="error", error=str(exc))


def raise_ticket(
    merchant_id: str,
    issue_type: str,
    description: str = "",
    priority: str = "normal",
) -> ToolResult:
    """Create a mock support ticket and return its ETA."""
    try:
        data = _post(
            "/ticket",
            {
                "merchant_id": merchant_id,
                "issue_type": issue_type,
                "description": description,
                "priority": priority,
            },
        )
        return ToolResult(tool="raise_ticket", status="ok", data=data)
    except httpx.HTTPStatusError as exc:
        return ToolResult(tool="raise_ticket", status="error", error=str(exc))
    except Exception as exc:  # noqa: BLE001
        _log.warning("[paytm_tools] raise_ticket failed: %s", exc)
        return ToolResult(tool="raise_ticket", status="error", error=str(exc))
    except Exception as exc:  # noqa: BLE001
        _log.warning("[paytm_tools] soundbox_health failed: %s", exc)
        return ToolResult(tool="soundbox_health", status="error", error=str(exc))


# ---------------------------------------------------------------------------
# Spoken summary  (never speaks raw JSON, formats amounts/dates)
# ---------------------------------------------------------------------------

def spoken_summary(result: ToolResult) -> str:
    """Return a 1-2 sentence spoken summary of a tool result.

    Amounts are formatted as 'rupees X', dates as 'on DATE'.
    Never exposes raw JSON or internal field names.
    """
    if not result.ok:
        if result.status == "not_found":
            return "I couldn't find that record. Please double-check the details and try again."
        return "I wasn't able to fetch that information right now. Please try again in a moment."

    d = result.data

    if result.tool == "lookup_qr":
        qr_status = d.get("qr_status", "unknown")
        if qr_status == "active":
            amount = d.get("last_scan_amount")
            if amount is not None:
                return (
                    f"Your QR code is active. "
                    f"The last scan was for rupees {amount:,.0f}."
                )
            return "Your QR code is active and working normally."
        if qr_status == "inactive":
            issue = d.get("issue", "")
            return f"Your QR code appears to be inactive. {issue}" if issue else \
                   "Your QR code appears to be inactive. Please contact Paytm support."
        return f"Your QR code status is {qr_status}."

    if result.tool == "settlement_status":
        status = d.get("status", "unknown")
        amount = d.get("amount", 0)
        if status == "settled":
            date = d.get("settled_date", "")
            utr = d.get("utr", "")
            return (
                f"Your settlement of rupees {amount:,.0f} has been completed"
                + (f" on {date}" if date else "")
                + (f", UTR {utr}" if utr else "")
                + "."
            )
        if status == "pending":
            expected = d.get("expected_date", "")
            return (
                f"Your settlement of rupees {amount:,.0f} is pending"
                + (f" and expected on {expected}" if expected else "")
                + "."
            )
        if status == "on_hold":
            return (
                f"Your settlement of rupees {amount:,.0f} is on hold. "
                "Please contact Paytm support for details."
            )
        return f"Settlement status is {status}."

    if result.tool == "trigger_refund":
        refund_status = d.get("status", "unknown")
        amount = d.get("amount", 0)
        refund_id = d.get("refund_id", "")
        if refund_status in ("processed", "initiated"):
            return (
                f"A refund of rupees {amount:,.0f} has been {refund_status}"
                + (f", reference {refund_id}" if refund_id else "")
                + "."
            )
        return f"Refund status is {refund_status}."

    if result.tool == "refund_approval_request":
        return (
            f"The refund request {d.get('approval_id', '')} is waiting for "
            "human approval. No refund has been initiated."
        )

    if result.tool == "raise_ticket":
        ticket_id = d.get("ticket_id", "unknown")
        eta = d.get("eta_hours")
        if eta is None:
            return f"Support ticket {ticket_id} has been created."
        return (
            f"Support ticket {ticket_id} has been created. "
            f"Our team expects to respond within {eta} hours."
        )

    if result.tool == "soundbox_health":
        online = d.get("online", False)
        if online:
            return "Your soundbox is online and working normally."
        issue = d.get("issue", "")
        last = d.get("last_ping", "")
        msg = "Your soundbox appears to be offline."
        if issue:
            msg += f" {issue}."
        elif last:
            msg += f" It was last seen on {last}."
        return msg

    return "I've retrieved the information. Would you like to know more?"


# ---------------------------------------------------------------------------
# Language-aware summary (translate via Groq when not English)
# ---------------------------------------------------------------------------

_LANG_NAMES = {
    "hi-IN": "Hindi",
    "kn-IN": "Kannada",
    "en-IN": "English",
}

_TRANSLATE_SYSTEM = (
    "You are a voice assistant translator for a Paytm merchant call. "
    "Translate the English sentence given by the user into {lang_name}. "
    'Return JSON only: {{"translation": "<translated sentence>"}}. '
    "Keep it natural, spoken, and short. No explanations."
)


def spoken_summary_for_language(
    result: ToolResult,
    language: str | None,
    llm=None,
) -> str:
    """Return the tool result summary in the merchant's chosen language.

    - English (en-IN) or no language: returns plain English summary.
    - Hindi (hi-IN) or Kannada (kn-IN): translates via Groq if llm is provided.
    - Falls back to English silently if translation fails or llm is None.
    """
    english = spoken_summary(result)

    if not language or language == "en-IN":
        return english

    lang_name = _LANG_NAMES.get(language, "English")
    if lang_name == "English" or llm is None:
        return english

    try:
        payload = llm.complete_json(
            system=_TRANSLATE_SYSTEM.format(lang_name=lang_name),
            user=english,
            max_tokens=150,
        )
        if isinstance(payload, dict):
            translated = str(payload.get("translation") or "").strip()
            if len(translated) > 2:
                return translated
    except Exception:
        _log.warning("[paytm_tools] translation to %s failed, using English", language)

    return english
