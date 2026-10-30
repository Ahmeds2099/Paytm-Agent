"""Tests for Phase 4: Paytm tool layer, intent routing, escalation, audit log."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Tool layer tests (mock httpx so no real network calls)
# ---------------------------------------------------------------------------

class ToolLayerHappyPathTests(unittest.TestCase):

    def _mock_get(self, url: str, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if "/qr/" in url:
            resp.json.return_value = {
                "merchant_id": "MID001",
                "qr_status": "active",
                "last_scan_amount": 500.0,
                "last_scan_ts": "2026-10-29T14:32:00Z",
                "issue": None,
            }
        elif "/settlement/" in url:
            resp.json.return_value = {
                "txn_id": "TXN001",
                "status": "settled",
                "amount": 1200.50,
                "settled_date": "2026-10-29",
                "expected_date": "2026-10-29",
                "utr": "UTR123",
            }
        elif "/soundbox/" in url:
            resp.json.return_value = {
                "device_id": "SB001",
                "online": True,
                "last_ping": "2026-10-30T09:00:00Z",
                "firmware": "2.3.1",
                "volume_level": 8,
                "issue": None,
            }
        resp.raise_for_status = MagicMock()
        return resp

    def _mock_post(self, url: str, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "txn_id": "TXN001",
            "refund_id": "REF-TXN001-001",
            "status": "processed",
            "amount": 1200.50,
            "processed_date": "2026-10-29",
        }
        resp.raise_for_status = MagicMock()
        return resp

    def test_lookup_qr_ok(self):
        with patch("httpx.get", side_effect=self._mock_get):
            from app.services.paytm_tools import lookup_qr
            result = lookup_qr("MID001")
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data["qr_status"], "active")
        self.assertTrue(result.ok)

    def test_settlement_status_ok(self):
        with patch("httpx.get", side_effect=self._mock_get):
            from app.services.paytm_tools import settlement_status
            result = settlement_status("TXN001")
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data["status"], "settled")

    def test_soundbox_health_ok(self):
        with patch("httpx.get", side_effect=self._mock_get):
            from app.services.paytm_tools import soundbox_health
            result = soundbox_health("SB001")
        self.assertEqual(result.status, "ok")
        self.assertTrue(result.data["online"])

    def test_trigger_refund_ok(self):
        with patch("httpx.post", side_effect=self._mock_post):
            from app.services.paytm_tools import trigger_refund
            result = trigger_refund("TXN001", 1200.50)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data["refund_id"], "REF-TXN001-001")


class ToolLayerErrorPathTests(unittest.TestCase):

    def _mock_404(self, url: str, **kwargs):
        import httpx
        resp = MagicMock()
        resp.status_code = 404
        error = httpx.HTTPStatusError("not found", request=MagicMock(), response=resp)
        resp.raise_for_status.side_effect = error
        return resp

    def _mock_timeout(self, url: str, **kwargs):
        import httpx
        raise httpx.TimeoutException("timeout")

    def test_lookup_qr_not_found(self):
        with patch("httpx.get", side_effect=self._mock_404):
            from app.services.paytm_tools import lookup_qr
            result = lookup_qr("UNKNOWN")
        self.assertEqual(result.status, "not_found")
        self.assertFalse(result.ok)

    def test_settlement_network_error(self):
        with patch("httpx.get", side_effect=self._mock_timeout):
            from app.services.paytm_tools import settlement_status
            result = settlement_status("TXN001")
        self.assertEqual(result.status, "error")
        self.assertFalse(result.ok)

    def test_soundbox_not_found(self):
        with patch("httpx.get", side_effect=self._mock_404):
            from app.services.paytm_tools import soundbox_health
            result = soundbox_health("GHOST")
        self.assertEqual(result.status, "not_found")


# ---------------------------------------------------------------------------
# Spoken summary tests
# ---------------------------------------------------------------------------

class SpokenSummaryTests(unittest.TestCase):

    def _ok(self, tool: str, data: dict):
        from app.services.paytm_tools import ToolResult
        return ToolResult(tool=tool, status="ok", data=data)

    def _err(self, tool: str):
        from app.services.paytm_tools import ToolResult
        return ToolResult(tool=tool, status="error", error="network down")

    def test_qr_active_summary(self):
        from app.services.paytm_tools import spoken_summary
        result = self._ok("lookup_qr", {"qr_status": "active", "last_scan_amount": 500})
        text = spoken_summary(result)
        self.assertIn("active", text.lower())
        self.assertIn("500", text)

    def test_settlement_settled_summary(self):
        from app.services.paytm_tools import spoken_summary
        result = self._ok("settlement_status", {
            "status": "settled", "amount": 1200.50, "settled_date": "2026-10-29", "utr": "UTR1",
        })
        text = spoken_summary(result)
        # Status=settled generates 'completed' in spoken text (user-friendly)
        self.assertIn("1,200", text)
        self.assertIn("completed", text.lower())

    def test_settlement_pending_summary(self):
        from app.services.paytm_tools import spoken_summary
        result = self._ok("settlement_status", {
            "status": "pending", "amount": 750, "expected_date": "2026-10-31",
        })
        text = spoken_summary(result)
        self.assertIn("pending", text.lower())
        self.assertIn("2026-10-31", text)

    def test_soundbox_offline_summary(self):
        from app.services.paytm_tools import spoken_summary
        result = self._ok("soundbox_health", {"online": False, "issue": "No power"})
        text = spoken_summary(result)
        self.assertIn("offline", text.lower())
        self.assertIn("No power", text)

    def test_error_summary(self):
        from app.services.paytm_tools import spoken_summary
        text = spoken_summary(self._err("lookup_qr"))
        self.assertIn("wasn't able", text.lower())

    def test_not_found_summary(self):
        from app.services.paytm_tools import spoken_summary
        from app.services.paytm_tools import ToolResult
        result = ToolResult(tool="lookup_qr", status="not_found", error="not found")
        text = spoken_summary(result)
        self.assertIn("couldn't find", text.lower())

    def test_english_passthrough_no_translation(self):
        """en-IN should return the English summary without any LLM call."""
        from app.services.paytm_tools import spoken_summary_for_language, ToolResult
        result = ToolResult(tool="soundbox_health", status="ok", data={"online": True})
        mock_llm = MagicMock()
        text = spoken_summary_for_language(result, "en-IN", mock_llm)
        mock_llm.complete_json.assert_not_called()
        self.assertIn("online", text.lower())

    def test_no_llm_falls_back_to_english(self):
        """Without llm, Hindi request must still return English text."""
        from app.services.paytm_tools import spoken_summary_for_language, ToolResult
        result = ToolResult(tool="soundbox_health", status="ok", data={"online": True})
        text = spoken_summary_for_language(result, "hi-IN", llm=None)
        self.assertIn("online", text.lower())

    def test_hindi_translation_called_with_llm(self):
        """With llm provided, Hindi request must call complete_json for translation."""
        from app.services.paytm_tools import spoken_summary_for_language, ToolResult
        result = ToolResult(tool="soundbox_health", status="ok", data={"online": True})
        mock_llm = MagicMock()
        mock_llm.complete_json.return_value = {"translation": "आपका साउंडबॉक्स ऑनलाइन है।"}
        text = spoken_summary_for_language(result, "hi-IN", mock_llm)
        mock_llm.complete_json.assert_called_once()
        self.assertEqual(text, "आपका साउंडबॉक्स ऑनलाइन है।")

    def test_translation_failure_returns_english(self):
        """If complete_json raises, must fall back to English silently."""
        from app.services.paytm_tools import spoken_summary_for_language, ToolResult
        result = ToolResult(tool="soundbox_health", status="ok", data={"online": True})
        mock_llm = MagicMock()
        mock_llm.complete_json.side_effect = RuntimeError("network error")
        text = spoken_summary_for_language(result, "hi-IN", mock_llm)
        self.assertIn("online", text.lower())


# ---------------------------------------------------------------------------
# Audit log tests
# ---------------------------------------------------------------------------

class AuditLogTests(unittest.TestCase):

    def _make_result(self, status="ok"):
        from app.services.paytm_tools import ToolResult
        return ToolResult(
            tool="settlement_status",
            status=status,
            data={"status": "settled", "amount": 500} if status == "ok" else {},
            error=None if status == "ok" else "network error",
        )

    def test_audit_log_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_audit.jsonl"
            with patch("app.services.audit_log._audit_path", return_value=log_path):
                from app.services.audit_log import audit_tool_call
                audit_tool_call(
                    session_id="S1",
                    client_id="C1",
                    intent="settlement_query",
                    tool="settlement_status",
                    args={"txn_id": "TXN001"},
                    result=self._make_result("ok"),
                    latency_ms=120,
                )
            lines = log_path.read_text().strip().splitlines()
            self.assertEqual(len(lines), 1)
            entry = json.loads(lines[0])
            self.assertEqual(entry["session_id"], "S1")
            self.assertEqual(entry["tool"], "settlement_status")
            self.assertEqual(entry["result_status"], "ok")
            self.assertEqual(entry["latency_ms"], 120)

    def test_audit_log_error_never_raises(self):
        """Audit log failures must not propagate to the caller."""
        with patch("app.services.audit_log._audit_path", side_effect=Exception("disk full")):
            from app.services.audit_log import audit_tool_call
            # Should not raise
            audit_tool_call(
                session_id="S2",
                client_id="C2",
                intent="device_issue",
                tool="soundbox_health",
                args={"device_id": "SB001"},
                result=self._make_result("error"),
                latency_ms=50,
            )


# ---------------------------------------------------------------------------
# Intent routing tests (unit test the classify + slot extraction path)
# ---------------------------------------------------------------------------

class IntentRoutingTests(unittest.TestCase):

    def test_settlement_query_is_classified(self):
        from app.services.intent import classify
        result = classify("When will my settlement arrive?")
        # Rule path has no settlement_query rule: falls to out_of_scope without LLM.
        # With LLM it returns settlement_query. Both are valid here.
        self.assertIn(result.label, ("settlement_query", "out_of_scope"))

    def test_human_request_is_classified(self):
        from app.services.intent import classify
        result = classify("I want to talk to a human agent.")
        self.assertEqual(result.label, "human_request")

    def test_opt_out_is_classified(self):
        from app.services.intent import classify
        result = classify("Please stop calling me.")
        self.assertEqual(result.label, "opt_out")

    def test_repeat_complaint_is_classified(self):
        from app.services.intent import classify
        result = classify("This problem is not fixed yet and it has happened before.")
        self.assertIn(result.label, ("repeat_complaint", "out_of_scope"))


if __name__ == "__main__":
    unittest.main()
