from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.voice.handlers.audio import AudioHandler
from app.services.voice.session import VoiceSession
from app.services.intent import classify_rule
from app.services.paytm_tools import ToolResult


class DemoOptOutLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def test_promotional_loan_opt_out_wording_is_high_priority(self):
        result = classify_rule(
            "No, I want to opt out of this loan offer. Please remove my number."
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.label, "opt_out")

    async def test_demo_opt_out_persists_dnc_and_closes_with_ack(self):
        handler = object.__new__(AudioHandler)
        handler._schedule_phrases = MagicMock()
        session = VoiceSession()
        session.metadata.update(
            {
                "merchant_id": "MID006",
                "call_id": "demo-call",
                "scenario": {"scenario_id": "opt_out"},
            }
        )

        with patch(
            "app.services.voice.handlers.audio.record_opt_out",
            return_value={"merchant_id": "MID006"},
        ) as record_opt_out:
            await handler._close_opt_out(session, MagicMock(), "en-IN")

        record_opt_out.assert_called_once_with("MID006", call_id="demo-call")
        self.assertTrue(session.metadata["opt_out_persisted"])
        self.assertEqual(session.metadata["outcome"], "closed:opt_out")
        handler._schedule_phrases.assert_called_once()
        self.assertEqual(
            handler._schedule_phrases.call_args.kwargs["close_call_outcome"],
            "closed:opt_out",
        )
        self.assertEqual(
            handler._schedule_phrases.call_args.args[2],
            [("demo_opt_out_ack", "en-IN")],
        )

    async def test_demo_opt_out_storage_failure_is_reported_without_false_ack(self):
        handler = object.__new__(AudioHandler)
        handler._schedule_phrases = MagicMock()
        handler._send_error = AsyncMock()
        session = VoiceSession()
        session.metadata.update(
            {
                "merchant_id": "MID006",
                "call_id": "demo-call",
                "scenario": {"scenario_id": "opt_out"},
            }
        )

        with patch(
            "app.services.voice.handlers.audio.record_opt_out",
            side_effect=OSError("disk unavailable"),
        ):
            await handler._close_opt_out(session, MagicMock(), "en-IN")

        handler._send_error.assert_awaited_once()
        self.assertFalse(session.metadata["opt_out_persisted"])
        self.assertEqual(
            handler._schedule_phrases.call_args.args[2],
            [("opt_out_save_failed", "en-IN")],
        )

    async def test_manual_escalation_is_logged_and_closes_call(self):
        handler = object.__new__(AudioHandler)
        session = VoiceSession()
        session.language = "en-IN"
        session.language_locked = True
        session.metadata["call_id"] = "demo-call"
        connection = MagicMock()
        connection.send_json = AsyncMock()

        with patch("app.services.voice.handlers.audio.end_call") as end_call:
            await handler.handle_control(
                session,
                connection,
                {"type": "manual_escalation"},
            )

        self.assertTrue(session.escalated)
        end_call.assert_called_once_with(
            "demo-call",
            outcome="escalated:human_requested",
            language="en-IN",
            escalated=True,
            repeat_complaint_count=0,
        )
        self.assertEqual(connection.send_json.await_count, 2)

    async def test_opted_out_loan_scenario_is_blocked_before_call_start(self):
        handler = object.__new__(AudioHandler)
        session = VoiceSession()
        connection = MagicMock()
        connection.send_json = AsyncMock()

        with (
            patch(
                "app.services.voice.handlers.audio.get_scenario",
                return_value={"scenario_id": "opt_out"},
            ),
            patch(
                "app.services.voice.handlers.audio.is_opted_out",
                return_value=True,
            ),
            patch("app.services.voice.handlers.audio.start_call") as start_call,
        ):
            await handler.handle_control(
                session,
                connection,
                {
                    "type": "session_init",
                    "client_id": "MID006",
                    "merchant_profile": {"merchant_id": "MID006"},
                },
            )

        start_call.assert_not_called()
        connection.send_json.assert_awaited_once()
        self.assertEqual(
            connection.send_json.await_args.args[1]["type"],
            "call_blocked",
        )

    async def test_settlement_confirmation_raises_priority_ticket(self):
        handler = object.__new__(AudioHandler)
        handler.manager = MagicMock()
        handler._schedule_system_message = MagicMock()
        session = VoiceSession()
        session.language = "hi-IN"
        session.language_locked = True
        session.metadata.update(
            {
                "call_id": "demo-call",
                "client_id": "MID002",
                "merchant_id": "MID002",
                "scenario": {"scenario_id": "settlement_pending"},
                "awaiting_settlement_priority": True,
            }
        )
        connection = MagicMock()
        connection.send_json = AsyncMock()

        with (
            patch("app.services.voice.handlers.audio.classify", return_value=MagicMock(
                label="confirmation_yes",
                topic=None,
                slots={},
                confidence=0.99,
                source="rule",
            )),
            patch("app.services.voice.handlers.audio.settings.VOICE_ENABLE_TOOLS", True),
            patch("app.services.voice.handlers.audio.settings.GROQ_API_KEY", ""),
            patch(
                "app.services.voice.handlers.audio.raise_ticket",
                return_value=ToolResult(
                    tool="raise_ticket",
                    status="ok",
                    data={"ticket_id": "TICKET-002", "eta_hours": 4},
                ),
            ) as raise_ticket,
            patch("app.services.voice.handlers.audio.audit_tool_call"),
            patch("app.services.voice.handlers.audio.record_intent"),
            patch("app.services.voice.handlers.audio.record_tool") as record_tool,
        ):
            handled = await handler._dispatch_intent(session, connection, "हाँ")

        self.assertTrue(handled)
        raise_ticket.assert_called_once_with(
            "MID002",
            "settlement_pending",
            "Merchant needs an urgent follow-up for a pending settlement.",
            "high",
        )
        self.assertEqual(session.metadata["outcome"], "resolved:ticket_raised_priority")
        self.assertEqual(session.metadata["ticket_id"], "TICKET-002")
        record_tool.assert_called_once()
