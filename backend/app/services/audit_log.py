"""Audit log for Paytm tool calls — Phase 4.

Every tool call (successful or failed) is appended as a JSON line to
AUDIT_LOG_PATH. The file is never truncated; agents and operators can
replay or dispute any call from the log.

Usage::

    from app.services.audit_log import audit_tool_call
    audit_tool_call(
        session_id="...",
        client_id="...",
        intent="settlement_query",
        tool="settlement_status",
        args={"txn_id": "TXN001"},
        result=tool_result,
        latency_ms=120,
    )
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.services.paytm_tools import ToolResult

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Log file location — created lazily on first write
# ---------------------------------------------------------------------------

def _audit_path() -> Path:
    raw = getattr(settings, "AUDIT_LOG_PATH", "")
    if raw:
        return Path(raw)
    # Default: backend/.audit/calls.jsonl (relative to this file's grandparent)
    here = Path(__file__).resolve().parent.parent.parent  # backend/
    return here / ".audit" / "calls.jsonl"


def audit_tool_call(
    *,
    session_id: str,
    client_id: str,
    intent: str,
    tool: str,
    args: dict,
    result: ToolResult,
    latency_ms: int,
) -> None:
    """Append one tool-call record to the audit log (fire-and-forget)."""
    entry = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "session_id": session_id,
        "client_id": client_id,
        "intent": intent,
        "tool": tool,
        "args": args,
        "result_status": result.status,
        "result_summary": _summarise(result),
        "latency_ms": latency_ms,
    }
    try:
        path = _audit_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:  # noqa: BLE001
        _log.warning("[audit_log] write failed: %s", exc)


def _summarise(result: ToolResult) -> str:
    """Short human-readable summary for the log, not for speech."""
    if not result.ok:
        return f"{result.status}: {result.error or 'unknown error'}"
    d = result.data
    if result.tool == "settlement_status":
        return f"status={d.get('status')} amount={d.get('amount')}"
    if result.tool == "lookup_qr":
        return f"qr_status={d.get('qr_status')}"
    if result.tool == "trigger_refund":
        return f"refund_id={d.get('refund_id')} status={d.get('status')}"
    if result.tool == "soundbox_health":
        return f"online={d.get('online')}"
    return "ok"
