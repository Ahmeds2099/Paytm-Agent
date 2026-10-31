from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.api import demo as demo_api
from app.services.intent import classify_rule
from app.services.voice.handlers.audio import AudioHandler
from app.services.voice.phrases import phrase_text
from app.services.voice.session import VoiceSession
from app.services.paytm_tools import ToolResult


class DemoVoiceBehaviorTests(unittest.IsolatedAsyncioTestCase):
    def _handler(self):
        handler = object.__new__(AudioHandler)
        handler.manager = MagicMock()
        handler._schedule_system_message = MagicMock()
        handler._schedule_phrases = MagicMock()
        return handler

    async def test_general_settlement_lookup_requests_transaction_id(self):
        handler = self._handler()
        session = VoiceSession()
        session.language = "en-IN"
        session.language_locked = True
        connection = MagicMock()
        connection.send_json = AsyncMock()
        classified = MagicMock(
            label="settlement_query",
            topic=None,
            slots={},
            confidence=0.99,
            source="rule",
        )

        with (
            patch("app.services.voice.handlers.audio.classify", return_value=classified),
            patch("app.services.voice.handlers.audio.settings.VOICE_ENABLE_TOOLS", True),
            patch("app.services.voice.handlers.audio.settings.GROQ_API_KEY", ""),
            patch("app.services.voice.handlers.audio.settlement_status") as lookup,
            patch("app.services.voice.handlers.audio.record_intent"),
        ):
            handled = await handler._dispatch_intent(session, connection, "Where is my payment?")

        self.assertTrue(handled)
        self.assertTrue(session.metadata["awaiting_transaction_lookup_id"])
        lookup.assert_not_called()
        self.assertIn("transaction ID", handler._schedule_system_message.call_args.args[2])

    async def test_refund_confirms_profile_transaction_before_approval(self):
        handler = self._handler()
        session = VoiceSession()
        session.language = "en-IN"
        session.language_locked = True
        session.metadata.update(
            {
                "call_id": "demo-call",
                "client_id": "MID004",
                "merchant_id": "MID004",
                "scenario": {"scenario_id": "refund_pending", "transaction_id": "TXN004"},
            }
        )
        connection = MagicMock()
        connection.send_json = AsyncMock()
        refund_query = MagicMock(
            label="out_of_scope",
            topic="refund_query",
            slots={},
            confidence=0.99,
            source="rule",
        )
        confirmation = MagicMock(
            label="confirmation_yes",
            topic=None,
            slots={},
            confidence=0.99,
            source="rule",
        )
        approval_confirmation = MagicMock(
            label="confirmation_yes",
            topic=None,
            slots={},
            confidence=0.99,
            source="rule",
        )

        with (
            patch(
                "app.services.voice.handlers.audio.classify",
                side_effect=[refund_query, confirmation, approval_confirmation],
            ),
            patch("app.services.voice.handlers.audio.settings.VOICE_ENABLE_TOOLS", True),
            patch("app.services.voice.handlers.audio.settings.GROQ_API_KEY", ""),
            patch(
                "app.services.voice.handlers.audio.settlement_status",
                return_value=ToolResult(
                    tool="settlement_status",
                    status="ok",
                    data={
                        "txn_id": "TXN004",
                        "status": "settled",
                        "amount": 2400,
                        "settled_date": "2026-10-31",
                    },
                ),
            ) as settlement_lookup,
            patch(
                "app.services.voice.handlers.audio.request_refund_approval",
                return_value=ToolResult(
                    tool="refund_approval_request",
                    status="ok",
                    data={"approval_id": "REF-APP-001", "status": "pending_approval"},
                ),
            ) as request_approval,
            patch("app.services.voice.handlers.audio.trigger_refund") as trigger_refund,
            patch("app.services.voice.handlers.audio.audit_tool_call"),
            patch("app.services.voice.handlers.audio.record_intent"),
            patch("app.services.voice.handlers.audio.record_tool"),
        ):
            self.assertTrue(await handler._dispatch_intent(session, connection, "I need a refund"))
            settlement_lookup.assert_called_once_with("TXN004")
            self.assertEqual(session.metadata["refund_amount"], 2400)
            self.assertTrue(session.metadata["awaiting_refund_transaction_confirmation"])
            self.assertFalse(session.metadata.get("awaiting_refund_approval", False))
            self.assertIn("TXN004", handler._schedule_system_message.call_args.args[2])
            self.assertIn("profile", handler._schedule_system_message.call_args.args[2])
            request_approval.assert_not_called()

            self.assertTrue(await handler._dispatch_intent(session, connection, "Yes"))
            self.assertFalse(session.metadata["awaiting_refund_transaction_confirmation"])
            self.assertTrue(session.metadata["awaiting_refund_approval"])
            self.assertIn("human approval", handler._schedule_system_message.call_args.args[2])
            request_approval.assert_not_called()

            self.assertTrue(await handler._dispatch_intent(session, connection, "Yes"))

        request_approval.assert_called_once_with("TXN004", 2400, "MID004", "2026-10-31")
        trigger_refund.assert_not_called()
        self.assertTrue(session.metadata["requires_human_approval"])
        self.assertEqual(session.metadata["refund_request"]["status"], "pending_approval")
        self.assertEqual(
            handler._schedule_system_message.call_args.kwargs["close_call_outcome"],
            "pending:refund_approval",
        )

    async def test_missing_refund_amount_never_says_zero_or_requests_approval(self):
        handler = self._handler()
        session = VoiceSession()
        session.language = "en-IN"
        session.language_locked = True
        session.metadata.update(
            {
                "call_id": "demo-call",
                "client_id": "MID004",
                "merchant_id": "MID004",
                "scenario": {"scenario_id": "refund_pending", "transaction_id": "TXN004"},
            }
        )
        connection = MagicMock()
        connection.send_json = AsyncMock()
        classified = MagicMock(
            label="out_of_scope",
            topic="refund_query",
            slots={},
            confidence=0.99,
            source="rule",
        )

        with (
            patch("app.services.voice.handlers.audio.classify", return_value=classified),
            patch("app.services.voice.handlers.audio.settings.VOICE_ENABLE_TOOLS", True),
            patch("app.services.voice.handlers.audio.settings.GROQ_API_KEY", ""),
            patch(
                "app.services.voice.handlers.audio.settlement_status",
                return_value=ToolResult(tool="settlement_status", status="ok", data={"txn_id": "TXN004"}),
            ),
            patch("app.services.voice.handlers.audio.request_refund_approval") as request_approval,
            patch("app.services.voice.handlers.audio.audit_tool_call"),
            patch("app.services.voice.handlers.audio.record_intent"),
            patch("app.services.voice.handlers.audio.record_tool"),
        ):
            handled = await handler._dispatch_intent(session, connection, "I need a refund")

        self.assertTrue(handled)
        self.assertFalse(session.metadata.get("awaiting_refund_approval", False))
        request_approval.assert_not_called()
        reply = handler._schedule_system_message.call_args.args[2]
        self.assertNotIn("0 rupees", reply)
        self.assertIn("couldn't verify", reply)

    async def test_declining_profile_transaction_asks_for_correct_transaction_id(self):
        handler = self._handler()
        session = VoiceSession()
        session.language = "en-IN"
        session.language_locked = True
        session.metadata.update(
            {
                "call_id": "demo-call",
                "client_id": "MID004",
                "merchant_id": "MID004",
                "scenario": {"scenario_id": "refund_pending", "transaction_id": "TXN004"},
                "awaiting_refund_transaction_confirmation": True,
                "refund_txn_id": "TXN004",
                "refund_amount": 2400,
            }
        )
        connection = MagicMock()
        connection.send_json = AsyncMock()
        confirmation_no = MagicMock(
            label="confirmation_no",
            topic=None,
            slots={},
            confidence=0.99,
            source="rule",
        )

        with (
            patch("app.services.voice.handlers.audio.classify", return_value=confirmation_no),
            patch("app.services.voice.handlers.audio.settings.VOICE_ENABLE_TOOLS", True),
            patch("app.services.voice.handlers.audio.settings.GROQ_API_KEY", ""),
            patch("app.services.voice.handlers.audio.request_refund_approval") as request_approval,
            patch("app.services.voice.handlers.audio.record_intent"),
        ):
            handled = await handler._dispatch_intent(session, connection, "No")

        self.assertTrue(handled)
        self.assertFalse(session.metadata["awaiting_refund_transaction_confirmation"])
        self.assertTrue(session.metadata["awaiting_refund_txn_id"])
        self.assertIn("transaction ID", handler._schedule_system_message.call_args.args[2])
        request_approval.assert_not_called()

    async def test_declining_profile_transaction_can_provide_alternate_id_immediately(self):
        handler = self._handler()
        session = VoiceSession()
        session.language = "en-IN"
        session.language_locked = True
        session.metadata.update(
            {
                "call_id": "demo-call",
                "client_id": "MID004",
                "merchant_id": "MID004",
                "scenario": {"scenario_id": "refund_pending", "transaction_id": "TXN004"},
                "awaiting_refund_transaction_confirmation": True,
                "refund_txn_id": "TXN004",
                "refund_amount": 2400,
            }
        )
        connection = MagicMock()
        connection.send_json = AsyncMock()
        correction = MagicMock(
            label="confirmation_no",
            topic="refund_query",
            slots={"transaction_id": "TXN001"},
            confidence=0.99,
            source="rule",
        )

        with (
            patch("app.services.voice.handlers.audio.classify", return_value=correction),
            patch("app.services.voice.handlers.audio.settings.VOICE_ENABLE_TOOLS", True),
            patch("app.services.voice.handlers.audio.settings.GROQ_API_KEY", ""),
            patch(
                "app.services.voice.handlers.audio.settlement_status",
                return_value=ToolResult(
                    tool="settlement_status",
                    status="ok",
                    data={
                        "txn_id": "TXN001",
                        "status": "settled",
                        "amount": 1200.5,
                        "settled_date": "2026-10-30",
                    },
                ),
            ) as settlement_lookup,
            patch("app.services.voice.handlers.audio.audit_tool_call"),
            patch("app.services.voice.handlers.audio.record_intent"),
            patch("app.services.voice.handlers.audio.record_tool"),
        ):
            handled = await handler._dispatch_intent(
                session,
                connection,
                "No, use TXN001 instead",
            )

        self.assertTrue(handled)
        settlement_lookup.assert_called_once_with("TXN001")
        self.assertTrue(session.metadata["awaiting_refund_transaction_confirmation"])
        self.assertEqual(session.metadata["refund_txn_id"], "TXN001")
        self.assertEqual(session.metadata["refund_amount"], 1200.5)
        self.assertIn("TXN001", handler._schedule_system_message.call_args.args[2])

    async def test_first_human_request_offers_resolution_and_second_escalates(self):
        handler = self._handler()
        session = VoiceSession()
        connection = MagicMock()
        connection.send_json = AsyncMock()

        await handler._handle_human_request(session, connection, "kn-IN")
        self.assertTrue(session.metadata["human_request_deferred"])
        self.assertFalse(session.escalated)
        handler._schedule_phrases.assert_called_once()

        await handler._handle_human_request(session, connection, "kn-IN")
        self.assertTrue(session.escalated)
        connection.send_json.assert_awaited_once()
        self.assertEqual(
            handler._schedule_phrases.call_args.kwargs["close_call_outcome"],
            "escalated:human_requested",
        )

    def test_kannada_human_request_is_deterministic_and_hindi_voice_is_feminine(self):
        self.assertEqual(classify_rule("ನಾನು ಮಾನವನ ಜೊತೆ ಮಾತನಾಡಬೇಕು").label, "human_request")
        self.assertIn("कर सकती हूँ", phrase_text("confirm", "hi-IN"))


class DemoResetEndpointTests(unittest.TestCase):
    def test_reset_requires_development_flag(self):
        with patch.object(demo_api.settings, "DEMO_RESET_ENABLED", False):
            with self.assertRaises(demo_api.HTTPException) as raised:
                demo_api.reset_demo()
        self.assertEqual(raised.exception.status_code, 403)

    def test_reset_reports_mock_api_unavailable_without_clearing_local_data(self):
        with (
            patch.object(demo_api.settings, "DEMO_RESET_ENABLED", True),
            patch("app.api.demo.httpx.post", side_effect=demo_api.httpx.ConnectError("offline")),
            patch("app.api.demo.reset_calls") as reset_calls,
            patch("app.api.demo.reset_opt_outs") as reset_opt_outs,
            self.assertRaises(demo_api.HTTPException) as raised,
        ):
            demo_api.reset_demo()
        self.assertEqual(raised.exception.status_code, 503)
        reset_calls.assert_not_called()
        reset_opt_outs.assert_not_called()


if __name__ == "__main__":
    unittest.main()
