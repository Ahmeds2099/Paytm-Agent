# pyrefly: ignore [missing-import]
from groq import Groq
import json
import time

from app.core.config import settings


class LLMService:
    """Groq client for reply generation and small classification calls.

    One model serves both paths. Calls carry a timeout and one retry, and
    failures are reported as exceptions so the voice handler can speak an
    apology instead of going silent.
    """

    def __init__(self):

        self.client = Groq(
            api_key=settings.GROQ_API_KEY,
            timeout=settings.LLM_TIMEOUT_SECONDS,
            max_retries=0,
        )

    def _with_retry(self, call):
        attempts = max(1, settings.LLM_MAX_RETRIES + 1)
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                return call()
            except Exception as exc:  # network, timeout, rate limit
                last_error = exc
                if attempt + 1 < attempts:
                    time.sleep(0.4)

        assert last_error is not None
        raise last_error

    def generate(
        self,
        messages: list[dict],
    ) -> str:

        response = self._with_retry(
            lambda: self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                temperature=0.2,
                reasoning_effort=settings.LLM_REASONING_EFFORT,
                messages=messages,
            )
        )

        return response.choices[0].message.content or ""

    def stream(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
    ):

        request = {
            "model": settings.LLM_MODEL,
            "temperature": 0.2,
            "reasoning_effort": settings.LLM_REASONING_EFFORT,
            "messages": messages,
            "stream": True,
        }

        if max_tokens is not None:
            request["max_tokens"] = max_tokens

        # Retry only the connection. Once tokens arrive, a mid-stream
        # failure is surfaced to the caller.
        stream = self._with_retry(
            lambda: self.client.chat.completions.create(**request)
        )

        for chunk in stream:

            delta = chunk.choices[0].delta.content

            if delta:
                yield delta

    def complete_json(
        self,
        system: str,
        user: str,
        max_tokens: int = 200,
    ) -> dict | None:
        """Small JSON-only classification call."""

        response = self._with_retry(
            lambda: self.client.chat.completions.create(
                model=settings.LLM_CLASSIFIER_MODEL,
                temperature=0,
                reasoning_effort=settings.LLM_REASONING_EFFORT,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        )

        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    def classify_interruption(self, transcript: str) -> dict | None:
        """Return a small JSON interruption decision for ambiguous turns."""
        return self.complete_json(
            system=(
                "Classify a voice interruption. Return JSON only with "
                "intent and resume_policy. intent must be one of "
                "stop, backchannel, clarification, side_question, "
                "topic_switch, resume, decline, other. "
                "resume_policy must be discard, automatic, confirm, "
                "keep_paused, or none. Stop means cancel and discard. "
                "A distinct question is side_question. A request to "
                "explain the current answer is clarification."
            ),
            user=transcript,
            max_tokens=80,
        )
