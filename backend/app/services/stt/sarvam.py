from __future__ import annotations

import asyncio
import base64
import json
from urllib.parse import urlencode

# pyrefly: ignore [missing-import]
import websockets

from app.core.config import settings
from app.services.stt.streaming import (
    ErrorHandler,
    StreamingSTTProvider,
    TranscriptEvent,
    TranscriptHandler,
)
from app.services.voice.language import normalize_language_code


class SarvamStreamingSTT(StreamingSTTProvider):
    """Sarvam realtime streaming speech-to-text (``saaras:v3-realtime``).

    Protocol reference: ``GET /speech-to-text-realtime/ws``. Audio is sent
    as base64-encoded ``audio_input`` events and the server emits
    ``transcript.partial`` / ``transcript.final`` events.
    """

    name = "sarvam"
    BASE_URL = "wss://api.sarvam.ai/speech-to-text-realtime/ws"
    KEEPALIVE_SECONDS = 20.0

    # Documented close codes for this endpoint.
    CLOSE_CODE_REASONS = {
        1003: (
            "Sarvam rejected the request: rate limit exceeded, quota "
            "exhausted, or invalid subscription key"
        ),
        1008: "Sarvam closed the stream after an inactivity timeout",
        1011: "Sarvam reported an internal server error",
        4000: (
            "Sarvam rejected a connection parameter (model, language or "
            "account access)"
        ),
    }

    def __init__(
        self,
        on_transcript: TranscriptHandler,
        on_error: ErrorHandler,
        language_code: str = "auto",
    ) -> None:
        super().__init__(on_transcript, on_error)

        self.language_code = normalize_language_code(language_code)
        self.model = settings.SARVAM_STT_MODEL
        self.stream_type = settings.SARVAM_STT_STREAM_TYPE

        self.websocket = None
        self.send_queue: asyncio.Queue[dict | None] = asyncio.Queue(
            maxsize=128,
        )
        self.sender_task: asyncio.Task | None = None
        self.receiver_task: asyncio.Task | None = None
        self.keepalive_task: asyncio.Task | None = None

        self.started = False
        self.closing = False
        self.failed = False

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def _url(self) -> str:
        params = [
            ("language_code", self.language_code),
            ("model", self.model),
            ("stream_type", self.stream_type),
            ("mode", "transcribe"),
            ("endpointing", settings.SARVAM_STT_ENDPOINTING),
            ("encoding", "linear16"),
            ("sample_rate", str(settings.VOICE_SAMPLE_RATE)),
            (
                "silence_duration_ms",
                str(settings.SARVAM_STT_SILENCE_MS),
            ),
            (
                "min_speech_duration_ms",
                str(settings.SARVAM_STT_MIN_SPEECH_MS),
            ),
            ("threshold", str(settings.SARVAM_STT_THRESHOLD)),
        ]

        if settings.SARVAM_STT_PROMPT:
            params.append(("prompt", settings.SARVAM_STT_PROMPT))

        return f"{self.BASE_URL}?{urlencode(params)}"

    async def _connect(self):
        """Connect, retrying once on transient network failures."""

        if not settings.SARVAM_API_KEY:
            raise RuntimeError("SARVAM_API_KEY is not configured")

        last_error: Exception | None = None

        for attempt in range(2):
            try:
                return await websockets.connect(
                    self._url(),
                    additional_headers={
                        "api-subscription-key": settings.SARVAM_API_KEY,
                    },
                    open_timeout=10,
                    close_timeout=3,
                    max_size=2**22,
                )
            except websockets.exceptions.InvalidStatus as exc:
                status = getattr(
                    getattr(exc, "response", None),
                    "status_code",
                    None,
                )
                # Authentication and parameter errors will not heal on
                # retry, and retrying wastes the caller's turn.
                if status in {400, 401, 403}:
                    raise
                last_error = exc
            except (OSError, asyncio.TimeoutError) as exc:
                last_error = exc

            if attempt == 0:
                await asyncio.sleep(0.5)

        assert last_error is not None
        raise last_error

    async def start(self, language_code: str = "auto") -> None:
        if self.started:
            return

        if language_code:
            self.language_code = normalize_language_code(language_code)

        self.websocket = await self._connect()
        self.started = True

        self.sender_task = asyncio.create_task(
            self._sender(),
            name="sarvam-sender",
        )
        self.receiver_task = asyncio.create_task(
            self._receiver(),
            name="sarvam-receiver",
        )
        self.keepalive_task = asyncio.create_task(
            self._keepalive(),
            name="sarvam-keepalive",
        )

    # ------------------------------------------------------------------
    # Audio / control messages
    # ------------------------------------------------------------------

    async def send_audio(self, audio: bytes) -> None:
        if not audio or not self.started or self.closing or self.failed:
            return

        payload = {
            "event": "audio_input",
            "audio": base64.b64encode(audio).decode("ascii"),
        }

        try:
            self.send_queue.put_nowait(payload)
        except asyncio.QueueFull:
            await self._fail("Sarvam audio queue overflowed")

    async def set_language(self, language_code: str) -> bool:
        """Re-arm detection or lock a language without reconnecting."""

        code = normalize_language_code(language_code)
        if code == self.language_code:
            return True

        if not self.started or self.closing or self.failed:
            self.language_code = code
            return True

        try:
            self.send_queue.put_nowait(
                {
                    "event": "config.update",
                    "language_code": code,
                }
            )
        except asyncio.QueueFull:
            return False

        self.language_code = code
        return True

    async def _sender(self) -> None:
        try:
            while not self.closing:
                payload = await self.send_queue.get()
                if payload is None:
                    return
                if self.websocket is None:
                    return
                await self.websocket.send(json.dumps(payload))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await self._fail(f"Sarvam send failed: {exc}")

    async def _receiver(self) -> None:
        try:
            if self.websocket is None:
                return

            async for raw_message in self.websocket:
                if isinstance(raw_message, bytes):
                    continue

                try:
                    message = json.loads(raw_message)
                except json.JSONDecodeError:
                    continue

                await self._handle_message(message)

            if not self.closing:
                await self._fail(
                    "Sarvam closed the transcription stream"
                )
        except asyncio.CancelledError:
            raise
        except websockets.exceptions.ConnectionClosed as exc:
            if not self.closing:
                await self._fail(self._close_reason(exc.code, exc.reason))
        except Exception as exc:
            if not self.closing:
                await self._fail(f"Sarvam stream failed: {exc}")

    @classmethod
    def _close_reason(cls, code: int | None, reason: str | None) -> str:
        known = cls.CLOSE_CODE_REASONS.get(code or 0)
        if known:
            return f"{known} (close code {code})"
        detail = (reason or "").strip()
        if detail:
            return f"Sarvam closed the stream ({code}): {detail}"
        return f"Sarvam closed the stream (close code {code})"

    # ------------------------------------------------------------------
    # Server events
    # ------------------------------------------------------------------

    async def _handle_message(self, message: dict) -> None:
        event = message.get("event") or message.get("type")

        if event == "transcript.partial":
            text = (message.get("text") or "").strip()
            if not text:
                return
            await self.on_transcript(
                TranscriptEvent(
                    text=text,
                    is_final=False,
                    provider=self.name,
                    language=self._detected_language(message),
                )
            )
            return

        if event == "transcript.final":
            text = (message.get("text") or "").strip()
            if not text:
                return
            await self.on_transcript(
                TranscriptEvent(
                    text=text,
                    is_final=True,
                    speech_final=True,
                    confidence=self._as_float(
                        message.get("language_confidence")
                    ),
                    provider=self.name,
                    language=self._detected_language(message),
                )
            )
            return

        if event == "error":
            code = message.get("code") or "unknown"
            detail = message.get("message") or "Sarvam returned an error"
            status = message.get("status_code")
            suffix = f" (status {status})" if status else ""
            reason = f"Sarvam error {code}: {detail}{suffix}"

            if message.get("is_fatal"):
                await self._fail(reason)
            else:
                print(f"[SARVAM] non-fatal: {reason}")
            return

        if event == "session.end" and not self.closing:
            duration = message.get("audio_duration_s")
            detail = f" after {duration}s of audio" if duration else ""
            await self._fail(
                f"Sarvam ended the session unexpectedly{detail}"
            )
            return

    def _detected_language(self, message: dict) -> str | None:
        detected = message.get("language")
        if detected:
            return str(detected)

        # The server only returns ``language`` in auto mode. When the
        # session is locked, echo the configured code instead.
        if self.language_code == "auto":
            return None
        return self.language_code

    @staticmethod
    def _as_float(value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    async def _keepalive(self) -> None:
        try:
            while not self.closing:
                await asyncio.sleep(self.KEEPALIVE_SECONDS)
                if self.closing:
                    return
                try:
                    self.send_queue.put_nowait({"event": "ping"})
                except asyncio.QueueFull:
                    await self._fail(
                        "Sarvam keepalive queue overflowed"
                    )
                    return
        except asyncio.CancelledError:
            raise

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------

    async def _fail(self, reason: str) -> None:
        if self.failed or self.closing:
            return
        self.failed = True
        asyncio.create_task(self.on_error(reason))

    async def close(self) -> None:
        if self.closing:
            return

        self.closing = True

        if self.websocket is not None:
            try:
                await self.websocket.send(
                    json.dumps({"event": "end"})
                )
            except Exception:
                pass

        current = asyncio.current_task()
        tasks = (
            self.sender_task,
            self.receiver_task,
            self.keepalive_task,
        )
        for task in tasks:
            if task is not None and task is not current:
                task.cancel()

        for task in tasks:
            if task is None or task is current:
                continue
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

        if self.websocket is not None:
            try:
                await self.websocket.close()
            except Exception:
                pass

        self.started = False
