from __future__ import annotations

from array import array
import base64
from io import BytesIO
import unittest
import wave
from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.services.tts.factory import TTSFactory
from app.services.tts.sarvam import SarvamProvider


def pcm_wav(samples: tuple[int, ...], *, channels: int = 1) -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(channels)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(array("h", samples).tobytes())
    return output.getvalue()


class SarvamTTSProviderTests(unittest.TestCase):
    def test_synthesizes_female_voice_and_streams_float32_pcm(self):
        wav_data = pcm_wav((0, 16384, -16384, 32767))
        response = MagicMock()
        response.json.return_value = {"audios": [base64.b64encode(wav_data).decode("ascii")]}
        provider = SarvamProvider()

        with (
            patch("app.services.tts.sarvam.settings.SARVAM_API_KEY", "test-key"),
            patch("app.services.tts.sarvam.settings.SARVAM_TTS_MODEL", "bulbul:v4-flash"),
            patch("app.services.tts.sarvam.httpx.post", return_value=response) as post,
        ):
            self.assertEqual(provider.synthesize("नमस्ते", "hi-IN"), wav_data)
            audio_chunks = list(provider.stream("नमस्ते", "hi-IN"))

        request_body = post.call_args.kwargs["json"]
        self.assertEqual(request_body["speaker"], "ritu_hi_customer")
        self.assertEqual(request_body["model"], "bulbul:v4-flash")
        self.assertEqual(request_body["speech_sample_rate"], 16000)
        self.assertEqual(request_body["output_audio_codec"], "wav")
        self.assertEqual(len(audio_chunks), 1)
        result = array("f")
        result.frombytes(audio_chunks[0])
        self.assertEqual(len(result), 4)
        self.assertAlmostEqual(result[0], 0.0, places=4)
        self.assertAlmostEqual(result[1], 0.5, places=4)
        self.assertAlmostEqual(result[2], -0.5, places=4)

    def test_selects_language_specific_female_speaker(self):
        self.assertEqual(SarvamProvider._speaker("en-IN"), "simran_en_customer")
        self.assertEqual(SarvamProvider._speaker("hi-IN"), "ritu_hi_customer")
        self.assertEqual(SarvamProvider._speaker("kn-IN"), "chaitra_kn_conversation")

    def test_downmixes_stereo_and_rejects_wrong_sample_rate(self):
        stereo = pcm_wav((16384, 0), channels=2)
        output = array("f")
        output.frombytes(SarvamProvider._wav_to_float32(stereo))
        self.assertEqual(len(output), 1)
        self.assertAlmostEqual(output[0], 0.25, places=4)

        mismatched = BytesIO()
        with wave.open(mismatched, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(22050)
            audio.writeframes(array("h", (0, 1)).tobytes())
        with self.assertRaisesRegex(ValueError, "22050 Hz"):
            SarvamProvider._wav_to_float32(mismatched.getvalue())

    def test_factory_switches_providers_without_restarting(self):
        original_provider = settings.VOICE_TTS_PROVIDER
        original_providers = TTSFactory._providers
        sarvam = MagicMock(name="sarvam-provider")
        cartesia = MagicMock(name="cartesia-provider")
        TTSFactory._providers = {}
        try:
            with (
                patch("app.services.tts.factory.settings.SARVAM_API_KEY", "sarvam-key"),
                patch("app.services.tts.factory.settings.CARTESIA_API_KEY", "cartesia-key"),
                patch("app.services.tts.factory.settings.CARTESIA_VOICE_ID", "female-voice"),
                patch("app.services.tts.factory.SarvamProvider", return_value=sarvam),
                patch("app.services.tts.factory.CartesiaProvider", return_value=cartesia),
            ):
                self.assertIs(TTSFactory.set_provider("sarvam"), sarvam)
                self.assertIs(TTSFactory.get_provider(), sarvam)
                self.assertIs(TTSFactory.set_provider("cartesia"), cartesia)
                self.assertIs(TTSFactory.get_provider(), cartesia)
        finally:
            settings.VOICE_TTS_PROVIDER = original_provider
            TTSFactory._providers = original_providers


if __name__ == "__main__":
    unittest.main()
