"""Persistent local do-not-call suppression for demo merchants."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from app.services.demo_scenarios import get_scenario

_log = logging.getLogger(__name__)
_lock = Lock()
_PATH = Path(__file__).resolve().parents[2] / ".audit" / "demo_dnc.json"


def _read() -> dict[str, dict[str, str]]:
    if not _PATH.exists():
        return {}
    with _PATH.open("r", encoding="utf-8") as file:
        records = json.load(file)
    if not isinstance(records, dict):
        raise ValueError(f"Invalid demo DNC data in {_PATH}")
    return records


def _write(records: dict[str, dict[str, str]]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = _PATH.with_suffix(".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(records, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, _PATH)
    except OSError:
        _log.exception("Could not persist demo do-not-call records")
        raise


def record_opt_out(merchant_id: str, *, call_id: str = "") -> dict[str, str]:
    if get_scenario(merchant_id) is None:
        raise ValueError(f"Unknown demo merchant: {merchant_id}")
    with _lock:
        records = _read()
        record = records.get(merchant_id)
        if record is None:
            record = {
                "merchant_id": merchant_id,
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "call_id": call_id,
            }
            records[merchant_id] = record
            _write(records)
        return dict(record)


def is_opted_out(merchant_id: str) -> bool:
    with _lock:
        return merchant_id in _read()


def list_opted_out() -> set[str]:
    with _lock:
        return set(_read())


def reset_opt_outs() -> None:
    with _lock:
        _write({})
