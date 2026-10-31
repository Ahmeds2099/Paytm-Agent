from __future__ import annotations

from array import array
import base64
from io import BytesIO
import sys
import wave

import httpx

from app.core.config import settings
from app.services.tts.base import TextToSpeechProvider
from app.services.voice.language import normalize_language_code


_FEMALE_SPEAKERS = {
    "en-IN": "simran_en_customer",
    "hi-IN": "ritu_hi_customer",
    "kn-IN": "chaitra_kn_conversation",
}


class SarvamProvider(TextToSpeechProvider):
    """Sarvam Bulbul TTS, converted to the app's 16 kHz float32 PCM format."""

    name = "sarvam"
    BASE_URL = "https://api.sarvam.ai/text-to-speech"

    @staticmethod
    def _speaker(language: str) -> str:
        try:
            return _FEMALE_SPEAKERS[language]
        except KeyError as exc:
            raise ValueError(f"Sarvam TTS does not support {language}.") from exc

    @staticmethod
    def _wav_to_float32(data: bytes) -> bytes:
        try:
            with wave.open(BytesIO(data), "rb") as audio:
                if audio.getcomptype() != "NONE":
                    raise ValueError("Sarvam returned compressed audio; expected PCM WAV.")
                channels = audio.getnchannels()
                sample_width = audio.getsampwidth()
                sample_rate = audio.getframerate()
                frames = audio.readframes(audio.getnframes())
        except (wave.Error, EOFError) as exc:
            raise ValueError("Sarvam returned an invalid WAV audio response.") from exc

        if sample_rate != settings.VOICE_SAMPLE_RATE:
            raise ValueError(
                f"Sarvam returned {sample_rate} Hz audio; "
                f"{settings.VOICE_SAMPLE_RATE} Hz is required."
            )
        if channels < 1:
            raise ValueError("Sarvam returned audio with no channels.")
        if sample_width != 2:
            raise ValueError(
                f"Sarvam returned {sample_width * 8}-bit PCM; 16-bit PCM is required."
            )

        samples = array("h")
        samples.frombytes(frames)
        if sys.byteorder != "little":
            samples.byteswap()
        if len(samples) % channels:
            raise ValueError("Sarvam returned incomplete PCM frames.")

        output = array("f")
        for offset in range(0, len(samples), channels):
            mono_sample = sum(samples[offset : offset + channels]) / channels
            output.append(max(-1.0, min(1.0, mono_sample / 32768.0)))
        return output.tobytes()

    def synthesize(
        self,
        text: str,
        language: str | None = None,
    ) -> bytes:
        if self.cancelled():
            return b""
        if not settings.SARVAM_API_KEY:
            raise RuntimeError("SARVAM_API_KEY is not configured.")
        if not text.strip():
            return b""
        if len(text) > 2500:
            raise ValueError("Sarvam TTS supports up to 2,500 characters per request.")

        language_code = normalize_language_code(
            language or settings.VOICE_TTS_LANGUAGE
        )
        if language_code == "auto":
            language_code = normalize_language_code(settings.VOICE_TTS_LANGUAGE)
        if language_code == "auto":
            language_code = "en-IN"
        response = httpx.post(
            self.BASE_URL,
            headers={
                "api-subscription-key": settings.SARVAM_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "language_code": language_code,
                "speaker": self._speaker(language_code),
                "model": settings.SARVAM_TTS_MODEL,
                "speech_sample_rate": settings.VOICE_SAMPLE_RATE,
                "output_audio_codec": "wav",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Sarvam TTS returned an invalid response.")
        audios = payload.get("audios")
        if not isinstance(audios, list) or not audios or not isinstance(audios[0], str):
            raise RuntimeError("Sarvam TTS response did not contain audio.")
        try:
            wav_data = base64.b64decode(audios[0], validate=True)
        except ValueError as exc:
            raise RuntimeError("Sarvam TTS returned invalid base64 audio.") from exc
        return wav_data

    def stream(
        self,
        text: str,
        language: str | None = None,
    ):
        wav_data = self.synthesize(text, language)
        audio = self.decode_audio(wav_data) if wav_data else b""
        if audio and not self.cancelled():
            yield audio

    def decode_audio(self, audio: bytes) -> bytes:
        return self._wav_to_float32(audio)
