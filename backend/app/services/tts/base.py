from abc import ABC, abstractmethod

from app.services.conversation.response_controller import ResponseController


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
