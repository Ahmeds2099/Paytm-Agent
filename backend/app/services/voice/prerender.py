"""Pre-render fixed phrases once and reuse the audio.

The brief asks for the greeting and fixed lines to be generated once per
language and cached as files. That matters for velocity: the greeting plays the
moment the call connects, with no text-to-speech round trip, and a repeat call
in the same language starts instantly from disk.

The cache stores raw 16 kHz ``pcm_f32le`` because that is exactly what the
browser expects on the binary WebSocket frame. Cartesia returns a WAV
container, so the RIFF header is stripped before writing; the frontend does
``new Float32Array(buffer)`` and would play header bytes as noise otherwise.

Cache key = phrase text + language + model + voice id. Changing any of those
produces a new file, so a stale clip is never served after an edit.
"""

from __future__ import annotations

import hashlib
import logging
import threading
from pathlib import Path

from app.core.config import settings
from app.services.tts.base import strip_wav
from app.services.tts.factory import TTSFactory
from app.services.voice.phrases import PHRASES, phrase_text

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CACHE_DIR = _BACKEND_ROOT / ".cache" / "voice_phrases"


class PhraseCache:
    """Disk cache of pre-rendered phrase audio, keyed by content."""

    def __init__(self, directory: Path | str | None = None) -> None:
        configured = getattr(settings, "VOICE_PHRASE_CACHE_DIR", "") or ""
        if directory is not None:
            self.directory = Path(directory)
        elif configured:
            candidate = Path(configured)
            self.directory = (
                candidate if candidate.is_absolute() else _BACKEND_ROOT / candidate
            )
        else:
            self.directory = _DEFAULT_CACHE_DIR
        self._lock = threading.Lock()

    def path_for(self, phrase_id: str, language: str) -> Path:
        text = phrase_text(phrase_id, language)
        material = "|".join(
            (
                phrase_id,
                language,
                text,
                settings.VOICE_TTS_PROVIDER,
                settings.CARTESIA_MODEL,
                settings.CARTESIA_VOICE_ID,
                settings.SARVAM_TTS_MODEL,
            )
        )
        digest = hashlib.sha1(material.encode("utf-8")).hexdigest()[:20]
        return self.directory / f"{phrase_id}.{language}.{digest}.pcm"

    def get(self, phrase_id: str, language: str) -> bytes | None:
        path = self.path_for(phrase_id, language)
        try:
            if path.is_file() and path.stat().st_size > 0:
                return path.read_bytes()
        except OSError:
            return None
        return None

    def render(self, phrase_id: str, language: str) -> bytes | None:
        """Synthesize one phrase now. Returns ``None`` when TTS is unavailable."""

        text = phrase_text(phrase_id, language)
        if not text:
            return None

        try:
            provider = TTSFactory.get_provider()
            wav = provider.synthesize(text, language=language)
        except Exception as exc:  # pragma: no cover - depends on the provider
            logger.warning(
                "phrase prerender failed id=%s language=%s: %s",
                phrase_id,
                language,
                exc,
            )
            return None

        pcm = provider.decode_audio(wav)
        if not pcm:
            return None

        path = self.path_for(phrase_id, language)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_bytes(pcm)
            temporary.replace(path)
        except OSError as exc:  # pragma: no cover - disk permissions
            logger.warning("phrase cache write failed: %s", exc)

        return pcm

    def ensure(self, phrase_id: str, language: str) -> bytes | None:
        """Return cached audio, rendering once if it is missing."""

        cached = self.get(phrase_id, language)
        if cached is not None:
            return cached

        with self._lock:
            # Another task may have rendered it while we waited.
            cached = self.get(phrase_id, language)
            if cached is not None:
                return cached
            return self.render(phrase_id, language)

    def warm(self) -> int:
        """Pre-render every fixed phrase. Returns how many are ready."""

        ready = 0
        total = 0
        for phrase_id, by_language in PHRASES.items():
            for language in by_language:
                total += 1
                if self.ensure(phrase_id, language):
                    ready += 1

        logger.info("phrase cache warm: %s/%s ready in %s", ready, total, self.directory)
        return ready


_cache: PhraseCache | None = None
_cache_lock = threading.Lock()


def get_phrase_cache() -> PhraseCache:
    global _cache
    if _cache is None:
        with _cache_lock:
            if _cache is None:
                _cache = PhraseCache()
    return _cache


def phrase_audio(phrase_id: str, language: str) -> bytes | None:
    """Cached PCM for a phrase, rendering it on first use."""

    return get_phrase_cache().ensure(phrase_id, language)


def warm_phrase_cache() -> int:
    return get_phrase_cache().warm()
