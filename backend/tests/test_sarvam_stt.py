import unittest
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import asyncio

from app.core.config import settings
from app.services.stt.sarvam import SarvamStreamingSTT
from app.services.voice.deepgram import DeepgramStreamingSTT
from app.services.voice.handlers.audio import AudioHandler
from app.services.voice.language import (
    cartesia_language_code,
    normalize_language_code,
)


class LanguageTests(unittest.TestCase):
    def test_aliases_map_to_bcp47(self):
        self.assertEqual(normalize_language_code("hi"), "hi-IN")
        self.assertEqual(normalize_language_code("KN"), "kn-IN")
        self.assertEqual(normalize_language_code("en_in"), "en-IN")
        self.assertEqual(normalize_language_code(""), "auto")
        self.assertEqual(normalize_language_code(None), "auto")

    def test_unsupported_language_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_language_code("fr-FR")

    def test_cartesia_uses_default_for_auto(self):
        self.assertEqual(
            cartesia_language_code("auto", "en-IN"),
            "en-IN",
        )
        self.assertEqual(
            cartesia_language_code("hi-IN", "en-IN"),
            "hi-IN",
        )
        self.assertEqual(
            cartesia_language_code(None, "kn-IN"),
            "kn-IN",
        )


class SarvamStreamTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.events = []
        self.errors = []

        async def on_transcript(event):
            self.events.append(event)

        async def on_error(reason):
            self.errors.append(reason)

        self.provider = SarvamStreamingSTT(
            on_transcript=on_transcript,
            on_error=on_error,
            language_code="hi-IN",
        )

    def test_url_contains_supported_parameters(self):
        query = parse_qs(urlparse(self.provider._url()).query)

        self.assertEqual(query["language_code"], ["hi-IN"])
        self.assertEqual(query["encoding"], ["linear16"])
        self.assertEqual(query["sample_rate"], ["16000"])
        self.assertEqual(query["endpointing"], ["vad"])
        self.assertIn("silence_duration_ms", query)
        self.assertNotIn("api-subscription-key", query)

    async def test_partial_and_final_events(self):
        await self.provider._handle_message(
            {
                "event": "transcript.partial",
                "utterance_idx": 0,
                "text": "मेरा QR",
                "language": "hi-IN",
            }
        )
        await self.provider._handle_message(
            {
                "event": "transcript.final",
                "utterance_idx": 0,
                "text": "मेरा QR कोड काम नहीं कर रहा",
                "language": "hi-IN",
                "language_confidence": "0.91",
            }
        )

        self.assertEqual(len(self.events), 2)
        self.assertFalse(self.events[0].is_final)
        self.assertEqual(self.events[0].text, "मेरा QR")
        self.assertEqual(self.events[0].provider, "sarvam")
        self.assertTrue(self.events[1].is_final)
        self.assertTrue(self.events[1].speech_final)
        self.assertAlmostEqual(self.events[1].confidence, 0.91)
        self.assertEqual(self.events[1].language, "hi-IN")

    async def test_locked_language_is_echoed_when_server_omits_it(self):
        await self.provider._handle_message(
            {
                "event": "transcript.final",
                "utterance_idx": 0,
                "text": "ನಮಸ್ಕಾರ",
            }
        )
        self.assertEqual(self.events[0].language, "hi-IN")

    async def test_fatal_error_reports_once(self):
        await self.provider._handle_message(
            {
                "event": "error",
                "code": "quota_exceeded",
                "is_fatal": True,
                "message": "quota exceeded",
                "status_code": 403,
            }
        )
        await self.provider._handle_message(
            {
                "event": "error",
                "code": "quota_exceeded",
                "is_fatal": True,
                "message": "quota exceeded",
            }
        )
        await asyncio.sleep(0)

        self.assertEqual(len(self.errors), 1)
        self.assertIn("quota_exceeded", self.errors[0])
        self.assertIn("403", self.errors[0])

    async def test_non_fatal_error_keeps_stream(self):
        await self.provider._handle_message(
            {
                "event": "error",
                "code": "invalid_config",
                "is_fatal": False,
                "message": "rejected",
            }
        )
        self.assertEqual(self.errors, [])

    async def test_set_language_sends_config_update(self):
        self.provider.started = True

        applied = await self.provider.set_language("kn-IN")

        self.assertTrue(applied)
        self.assertEqual(self.provider.language_code, "kn-IN")
        self.assertEqual(
            self.provider.send_queue.get_nowait(),
            {"event": "config.update", "language_code": "kn-IN"},
        )

    async def test_empty_final_is_ignored(self):
        await self.provider._handle_message(
            {
                "event": "transcript.final",
                "utterance_idx": 0,
                "text": "   ",
            }
        )
        self.assertEqual(self.events, [])

    def test_close_code_reasons(self):
        reason = SarvamStreamingSTT._close_reason(1003, "")
        self.assertIn("invalid subscription key", reason)
        reason = SarvamStreamingSTT._close_reason(1008, "")
        self.assertIn("inactivity", reason)


class DeepgramLanguageTests(unittest.TestCase):
    def _provider(self):
        async def on_transcript(_event):
            return None

        async def on_error(_reason):
            return None

        return DeepgramStreamingSTT(
            on_transcript=on_transcript,
            on_error=on_error,
        )

    def test_language_mapping(self):
        provider = self._provider()

        provider.language_code = "hi"
        self.assertIn("language=hi", provider._url())

        provider.language_code = "kn"
        self.assertIn("language=kn", provider._url())

        provider.language_code = "en-IN"
        self.assertIn("language=en-IN", provider._url())

    def test_nova3_uses_keyterm(self):
        provider = self._provider()
        url = provider._url()

        self.assertIn("keyterm=", url)
        self.assertNotIn("keywords=", url)


class ProviderChainTests(unittest.TestCase):
    """Fallback order: Sarvam -> Deepgram -> Whisper."""

    def setUp(self):
        # ``__new__`` keeps the heavy ConversationManager out of the test.
        self.handler = AudioHandler.__new__(AudioHandler)
        self._saved = (
            settings.VOICE_STT_PROVIDER,
            settings.VOICE_ALLOW_DEEPGRAM_FALLBACK,
        )

    def tearDown(self):
        (
            settings.VOICE_STT_PROVIDER,
            settings.VOICE_ALLOW_DEEPGRAM_FALLBACK,
        ) = self._saved

    def test_sarvam_is_primary_with_deepgram_backup(self):
        settings.VOICE_STT_PROVIDER = "sarvam"
        settings.VOICE_ALLOW_DEEPGRAM_FALLBACK = True

        self.assertEqual(
            self.handler._streaming_candidates(),
            ["sarvam", "deepgram"],
        )
        self.assertEqual(self.handler._fallback_after("sarvam"), ["deepgram"])
        self.assertEqual(self.handler._fallback_after("deepgram"), [])

    def test_deepgram_primary_has_no_streaming_backup(self):
        settings.VOICE_STT_PROVIDER = "deepgram"

        self.assertEqual(
            self.handler._streaming_candidates(),
            ["deepgram"],
        )

    def test_deepgram_fallback_can_be_disabled(self):
        settings.VOICE_STT_PROVIDER = "sarvam"
        settings.VOICE_ALLOW_DEEPGRAM_FALLBACK = False

        self.assertEqual(self.handler._streaming_candidates(), ["sarvam"])
        self.assertEqual(self.handler._fallback_after("sarvam"), [])

    def test_whisper_primary_skips_streaming(self):
        settings.VOICE_STT_PROVIDER = "whisper"

        self.assertEqual(self.handler._streaming_candidates(), [])

    def test_provider_factory_uses_session_language(self):
        session = SimpleNamespace(language="kn-IN")

        provider = self.handler._build_streaming_provider(
            "sarvam",
            session,
            None,
        )

        self.assertIsInstance(provider, SarvamStreamingSTT)
        self.assertEqual(provider.language_code, "kn-IN")
        self.assertEqual(
            provider.model,
            settings.SARVAM_STT_MODEL,
        )

    def test_provider_factory_builds_deepgram(self):
        session = SimpleNamespace(language="hi-IN")

        provider = self.handler._build_streaming_provider(
            "deepgram",
            session,
            None,
        )

        self.assertIsInstance(provider, DeepgramStreamingSTT)
        self.assertEqual(provider.name, "deepgram")


if __name__ == "__main__":
    unittest.main()
