from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Awaitable, Callable


@dataclass(frozen=True, slots=True)
class TranscriptEvent:
    """Provider-neutral transcript event.

    ``language`` is populated when the provider detects the spoken
    language (Sarvam's ``language_code=auto`` mode).
    """

    text: str
    is_final: bool
    speech_final: bool = False
    confidence: float | None = None
    provider: str = "sarvam"
    language: str | None = None


TranscriptHandler = Callable[[TranscriptEvent], Awaitable[None]]
ErrorHandler = Callable[[str], Awaitable[None]]


class StreamingSTTProvider(ABC):
    """One live speech-to-text connection per voice session.

    Implementations must stream interim and final transcripts through
    ``on_transcript`` and report unrecoverable failures through
    ``on_error`` exactly once. ``on_error`` never carries credentials.
    """

    name: str = "unknown"

    def __init__(
        self,
        on_transcript: TranscriptHandler,
        on_error: ErrorHandler,
    ) -> None:
        self.on_transcript = on_transcript
        self.on_error = on_error

    @abstractmethod
    async def start(self, language_code: str = "auto") -> None:
        """Open the provider connection. Raise on failure."""

    @abstractmethod
    async def send_audio(self, audio: bytes) -> None:
        """Queue a mono 16-bit 16 kHz PCM chunk."""

    @abstractmethod
    async def close(self) -> None:
        """Close the connection and stop background tasks."""

    async def set_language(self, language_code: str) -> bool:
        """Reconfigure the live stream.

        Return ``True`` when the change was applied in place, ``False``
        when the caller has to reconnect.
        """

        return False
