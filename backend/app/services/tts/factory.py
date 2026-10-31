from threading import RLock

from app.core.config import settings
from app.services.tts.base import TextToSpeechProvider
from app.services.tts.cartesia import CartesiaProvider
from app.services.tts.sarvam import SarvamProvider


class TTSFactory:
    _providers: dict[str, TextToSpeechProvider] = {}
    _lock = RLock()

    @classmethod
    def get_provider(cls, provider_name: str | None = None) -> TextToSpeechProvider:
        name = (provider_name or settings.VOICE_TTS_PROVIDER).strip().lower()
        with cls._lock:
            if name not in cls._providers:
                cls._providers[name] = cls._create_provider(name)
            return cls._providers[name]

    @classmethod
    def set_provider(cls, provider_name: str) -> TextToSpeechProvider:
        name = provider_name.strip().lower()
        with cls._lock:
            provider = cls._create_provider(name)
            cls._providers[name] = provider
            settings.VOICE_TTS_PROVIDER = name
            return provider

    @staticmethod
    def _create_provider(name: str) -> TextToSpeechProvider:
        if name == "cartesia":
            if not settings.CARTESIA_API_KEY:
                raise RuntimeError("CARTESIA_API_KEY is not configured.")
            if not settings.CARTESIA_VOICE_ID:
                raise RuntimeError("CARTESIA_VOICE_ID is not configured.")
            return CartesiaProvider()
        if name == "sarvam":
            if not settings.SARVAM_API_KEY:
                raise RuntimeError("SARVAM_API_KEY is not configured.")
            return SarvamProvider()
        raise ValueError(f"Unsupported TTS provider: {name}")