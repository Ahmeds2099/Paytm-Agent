from abc import ABC, abstractmethod

from app.services.conversation.response_controller import ResponseController


def strip_wav(data: bytes) -> bytes:
    """Return a WAV file's data chunk, or the input unchanged."""

    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return data

    offset = 12
    while offset + 8 <= len(data):
        chunk_id = data[offset : offset + 4]
        size = int.from_bytes(data[offset + 4 : offset + 8], "little")
        start = offset + 8
        end = start + size
        if chunk_id == b"data":
            return data[start:end]
        offset = end + (size & 1)

    return data


class TextToSpeechProvider(ABC):
    """Provider-neutral streaming speech synthesis."""

    name = "unknown"

    controller: ResponseController | None = None

    def attach(
        self,
        controller: ResponseController,
    ):
        self.controller = controller

    def detach(self):
        self.controller = None

    def cancelled(self) -> bool:
        return (
            self.controller is not None
            and self.controller.cancelled
        )

    def decode_audio(self, audio: bytes) -> bytes:
        """Convert synthesized WAV audio to the browser's raw PCM format."""
        return strip_wav(audio)

    @abstractmethod
    def synthesize(
        self,
        text: str,
        language: str | None = None,
    ) -> bytes:
        """Render a complete clip."""

    @abstractmethod
    def stream(
        self,
        text: str,
        language: str | None = None,
    ):
        """Yield raw audio chunks for one sentence."""


# Backwards-compatible name used by older modules.
BaseTTSProvider = TextToSpeechProvider
