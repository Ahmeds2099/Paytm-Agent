"""Local JSONL call records for the merchant demo and admin dashboard."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import uuid4

from app.services.demo_scenarios import get_scenario

_log = logging.getLogger(__name__)
_lock = RLock()
_PATH = Path(__file__).resolve().parents[2] / ".audit" / "call_log.jsonl"


def _read_records() -> list[dict]:
    if not _PATH.exists():
        return []
    records: list[dict] = []
    with _PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                _log.warning("Ignoring malformed call-log row %s:%d", _PATH, line_number)
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def _write_records(records: list[dict]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = _PATH.with_suffix(".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as file:
            for record in records:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, _PATH)
    except OSError:
        _log.exception("Could not persist demo call log")
        raise


def _update(call_id: str, changes: dict) -> dict | None:
    with _lock:
        records = _read_records()
        for index, record in enumerate(records):
            if record.get("call_id") == call_id:
                record.update(changes)
                records[index] = record
                _write_records(records)
                return dict(record)
    return None


def start_call(session_id: str, merchant_id: str) -> dict | None:
    merchant = get_scenario(merchant_id)
    if merchant is None:
        return None
    with _lock:
        records = _read_records()
        existing = next(
            (record for record in records if record.get("session_id") == session_id),
            None,
        )
        if existing is not None:
            return dict(existing)
        started = datetime.now(timezone.utc).isoformat()
        record = {
            "call_id": str(uuid4()),
            "merchant_id": merchant_id,
            "merchant_name": merchant["name"],
            "business_name": merchant["business_name"],
            "city": merchant["city"],
            "session_id": session_id,
            "started_at": started,
            "ended_at": None,
            "duration_seconds": 0,
            "language": None,
            "scenario": merchant["scenario_id"],
            "scenario_label": merchant["scenario_label"],
            "outcome": "open",
            "ticket_id": None,
            "escalated": False,
            "opt_out": False,
            "attention_required": False,
            "tool_calls": [],
            "tool_results": [],
            "intent_sequence": [],
            "turn_count": 0,
            "repeat_complaint_count": 0,
            "summary": "Outbound demo call in progress.",
        }
        records.append(record)
        _write_records(records)
        return dict(record)


def record_turn(
    call_id: str,
    *,
    intent: str | None = None,
    language: str | None = None,
    repeat_complaint_count: int | None = None,
) -> None:
    with _lock:
        record = next(
            (item for item in _read_records() if item.get("call_id") == call_id),
            None,
        )
        if record is None or record.get("ended_at"):
            return
        record["turn_count"] = int(record.get("turn_count", 0)) + 1
        if intent:
            record["intent_sequence"].append(intent)
        if language:
            record["language"] = language
        if repeat_complaint_count is not None:
            record["repeat_complaint_count"] = repeat_complaint_count
        _replace_record(record)


def record_intent(
    call_id: str,
    *,
    intent: str,
    language: str | None = None,
    repeat_complaint_count: int | None = None,
) -> None:
    with _lock:
        record = next(
            (item for item in _read_records() if item.get("call_id") == call_id),
            None,
        )
        if record is None or record.get("ended_at"):
            return
        record["turn_count"] = int(record.get("turn_count", 0)) + 1
        if intent:
            record["intent_sequence"].append(intent)
        if language:
            record["language"] = language
        if repeat_complaint_count is not None:
            record["repeat_complaint_count"] = repeat_complaint_count
        _replace_record(record)


def record_tool(
    call_id: str,
    *,
    tool: str,
    status: str,
    latency_ms: int,
    data: dict | None = None,
) -> None:
    with _lock:
        record = next(
            (item for item in _read_records() if item.get("call_id") == call_id),
            None,
        )
        if record is None or record.get("ended_at"):
            return
        record["tool_calls"].append(tool)
        record["tool_results"].append(
            {
                "tool": tool,
                "status": status,
                "latency_ms": latency_ms,
                "data": data or {},
            }
        )
        _replace_record(record)


def _replace_record(record: dict) -> None:
    records = _read_records()
    for index, current in enumerate(records):
        if current.get("call_id") == record.get("call_id"):
            records[index] = record
            _write_records(records)
            return


def end_call(
    call_id: str,
    *,
    outcome: str,
    language: str | None = None,
    ticket_id: str | None = None,
    escalated: bool = False,
    opt_out: bool = False,
    repeat_complaint_count: int = 0,
    agent_spoke_seconds: int = 0,
) -> dict | None:
    with _lock:
        record = next(
            (item for item in _read_records() if item.get("call_id") == call_id),
            None,
        )
        if record is None:
            return None
        if record.get("ended_at"):
            return dict(record)
        ended = datetime.now(timezone.utc)
        try:
            started = datetime.fromisoformat(record["started_at"])
            duration = max(0, int((ended - started).total_seconds()))
        except (KeyError, ValueError):
            duration = 0
        failed_tools = any(
            item.get("status") == "error"
            for item in record.get("tool_results", [])
        )
        attention_required = (
            (escalated and outcome == "escalated:human_requested")
            or repeat_complaint_count >= 2
            or (outcome == "closed:no_response" and agent_spoke_seconds > 30)
            or (failed_tools and outcome not in {"resolved:ticket_raised", "resolved:refund_initiated"})
        )
        record.update(
            {
                "ended_at": ended.isoformat(),
                "duration_seconds": duration,
                "language": language or record.get("language"),
                "outcome": outcome,
                "ticket_id": ticket_id or record.get("ticket_id"),
                "escalated": escalated,
                "opt_out": opt_out,
                "attention_required": attention_required,
                "repeat_complaint_count": repeat_complaint_count,
                "summary": _summary(record, outcome, ticket_id, escalated, opt_out),
            }
        )
        _replace_record(record)
        return dict(record)


def _summary(
    record: dict,
    outcome: str,
    ticket_id: str | None,
    escalated: bool,
    opt_out: bool,
) -> str:
    if opt_out:
        return "Merchant opted out of the promotional loan offer; local demo DNC suppression recorded."
    if escalated:
        return "Call escalated for human follow-up."
    if ticket_id:
        return f"{record['scenario_label']} reported. Ticket {ticket_id} was raised."
    if outcome == "resolved:refund_initiated":
        return "Merchant requested a refund; refund initiation was confirmed by the mock Paytm API."
    if outcome == "resolved:self_service":
        return "Merchant restored the soundbox through guided troubleshooting."
    return f"Call ended with outcome {outcome}."


def list_calls(*, since: str | None = None) -> list[dict]:
    with _lock:
        records = _read_records()
    if since:
        records = [record for record in records if record.get("started_at", "") >= since]
    return sorted(records, key=lambda record: record.get("started_at", ""), reverse=True)


def get_call(call_id: str) -> dict | None:
    with _lock:
        return next(
            (dict(record) for record in _read_records() if record.get("call_id") == call_id),
            None,
        )


def call_id_for_session(session_id: str) -> str | None:
    with _lock:
        record = next(
            (item for item in _read_records() if item.get("session_id") == session_id),
            None,
        )
        return str(record["call_id"]) if record else None
