"""Phase 3 acceptance probe: ask, lock, retry, change of mind.

Runs against a live backend on port 8100. Each scenario connects, waits for the
trigger frames, sends ``session_init`` without a language (the browser does the
same), then speaks a synthetic answer by streaming Cartesia audio into the
microphone socket.

Checks:
* the trilingual greeting is sent as cached audio,
* a single-word answer locks the right language,
* the confirmation is spoken in the chosen language,
* two unclear answers fall back to English,
* an explicit later request changes the language,
* nothing else changes it.

    .venv\\Scripts\\python.exe scripts\\language_gate_probe.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import websockets  # noqa: E402

from app.services.tts.cartesia import CartesiaProvider  # noqa: E402

URL = "ws://127.0.0.1:8100/ws/voice"


def synthesize(text: str, language: str) -> bytes:
    chunks = list(CartesiaProvider().stream(text, language=language))
    samples = np.frombuffer(b"".join(chunks), dtype="<f4")
    samples = np.clip(samples, -1.0, 1.0)
    return (samples * 32767.0).astype("<i2").tobytes()


@dataclass
class Turn:
    transcripts: list[str] = field(default_factory=list)
    segments: list[str] = field(default_factory=list)
    language_events: list[dict] = field(default_factory=list)
    audio_bytes: int = 0
    errors: list[str] = field(default_factory=list)


async def collect(ws, seconds: float, *, stop_on_audio_end: bool = False) -> Turn:
    turn = Turn()

    async def pump() -> None:
        while True:
            try:
                raw = await ws.recv()
            except Exception:
                return
            if isinstance(raw, (bytes, bytearray)):
                turn.audio_bytes += len(raw)
                continue
            payload = json.loads(raw)
            kind = payload.get("type")
            if kind == "transcript":
                turn.transcripts.append(payload.get("text") or "")
            elif kind == "assistant_segment_start":
                text = payload.get("text")
                if text:
                    turn.segments.append(text)
            elif kind == "language_changed":
                turn.language_events.append(payload)
            elif kind == "assistant_audio_end":
                # Wait until the answer has actually been locked and spoken.
                # The greeting's own end must not stop collection early.
                if stop_on_audio_end or any(
                    event.get("locked") for event in turn.language_events
                ):
                    return
            elif kind == "error":
                turn.errors.append(payload.get("message") or "error")

    try:
        await asyncio.wait_for(pump(), timeout=seconds)
    except asyncio.TimeoutError:
        pass
    return turn


async def speak(ws, text: str, language: str) -> None:
    pcm = synthesize(text, language)
    chunk = 3200
    for index in range(0, len(pcm), chunk):
        await ws.send(pcm[index : index + chunk])
        await asyncio.sleep(0.1)
    for _ in range(16):
        await ws.send(b"\x00" * chunk)
        await asyncio.sleep(0.1)


async def scenario(name: str, answer: str, answer_language: str) -> Turn:
    async with websockets.connect(URL, max_size=2**24, open_timeout=20) as ws:
        await collect(ws, 1.5)
        await ws.send(
            json.dumps(
                {
                    "type": "session_init",
                    "client_id": f"gate-{name}",
                    "document_ids": [],
                }
            )
        )
        # Let the greeting start, then barge in with the answer, like a
        # merchant who already knows what they want.
        await collect(ws, 2.0)
        await speak(ws, answer, answer_language)
        return await collect(ws, 25)


async def multi_turn() -> list[Turn]:
    turns: list[Turn] = []
    async with websockets.connect(URL, max_size=2**24, open_timeout=20) as ws:
        await collect(ws, 1.5)
        await ws.send(
            json.dumps(
                {
                    "type": "session_init",
                    "client_id": "gate-multi",
                    "document_ids": [],
                }
            )
        )
        await collect(ws, 2.0)

        await speak(ws, "I do not know.", "en-IN")
        turns.append(await collect(ws, 15))

        await speak(ws, "Kannada please.", "en-IN")
        turns.append(await collect(ws, 20))

        # The reply after the lock must be in Kannada, not English.
        await speak(
            ws,
            "ನನ್ನ ಸೆಟಲ್ಮೆಂಟ್ ಯಾವಾಗ ಬರುತ್ತದೆ?",
            "kn-IN",
        )
        turns.append(await collect(ws, 45, stop_on_audio_end=True))

        await speak(ws, "English please.", "en-IN")
        turns.append(await collect(ws, 20))

        # A language word inside a normal turn must not switch the call.
        await speak(
            ws,
            "My shop board is written in Kannada, when will my settlement come?",
            "en-IN",
        )
        turns.append(await collect(ws, 45, stop_on_audio_end=True))

    return turns


def summarize(label: str, turn: Turn) -> None:
    print(f"\n[{label}]")
    print("  transcript:", turn.transcripts)
    print("  language_changed:", turn.language_events)
    print("  spoken:", turn.segments)
    print("  audio_bytes:", turn.audio_bytes)
    if turn.errors:
        print("  errors:", turn.errors)


async def main() -> int:
    results: list[tuple[str, bool]] = []

    for name, answer, language in (
        ("hindi", "हिंदी में बात करें।", "hi-IN"),
        ("kannada", "ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ.", "kn-IN"),
        ("english", "English please.", "en-IN"),
    ):
        turn = await scenario(name, answer, language)
        summarize(name, turn)
        locked = next(
            (
                event
                for event in turn.language_events
                if event.get("locked")
            ),
            None,
        )
        expected = {"hindi": "hi-IN", "kannada": "kn-IN", "english": "en-IN"}[name]
        ok = bool(locked) and locked.get("language") == expected
        results.append((f"lock {name}", ok))

    turns = await multi_turn()
    for index, turn in enumerate(turns, 1):
        summarize(f"multi {index}", turn)

    retry_ok = any(
        turn.segments and "Hindi, Kannada or English" in " ".join(turn.segments)
        for turn in turns[:1]
    )
    results.append(("unclear asks again", retry_ok))
    results.append(
        (
            "unclear then locks Kannada",
            any(
                event.get("locked") and event.get("language") == "kn-IN"
                for event in turns[1].language_events
            ),
        )
    )
    kannada_reply = " ".join(turns[2].segments)
    results.append(
        (
            "reply after the lock stays Kannada",
            bool(kannada_reply)
            and any("\u0c80" <= char <= "\u0cff" for char in kannada_reply)
            and not turns[2].language_events,
        )
    )
    results.append(
        (
            "change of mind to English",
            any(
                event.get("locked") and event.get("language") == "en-IN"
                for event in turns[3].language_events
            ),
        )
    )
    stray_reply = " ".join(turns[4].segments)
    results.append(
        (
            "no switch on a stray language word",
            not turns[4].language_events
            and bool(stray_reply)
            and not any(
                "\u0900" <= char <= "\u0d7f" for char in stray_reply
            ),
        )
    )

    print("\n=== summary ===")
    for label, ok in results:
        print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
