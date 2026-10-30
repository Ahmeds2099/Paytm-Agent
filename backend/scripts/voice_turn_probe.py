"""End-to-end voice turn in one language, over the real socket.

Synthesizes a merchant sentence with Cartesia, streams it to the backend as
mic audio, and prints the transcript, the spoken segments and the reply. Used
to prove the reply stays in the call language and inside the sentence budget.

    .venv\\Scripts\\python.exe scripts\\voice_turn_probe.py
    .venv\\Scripts\\python.exe scripts\\voice_turn_probe.py hi-IN
    .venv\\Scripts\\python.exe scripts\\voice_turn_probe.py kn-IN
    .venv\\Scripts\\python.exe scripts\\voice_turn_probe.py en-IN
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import websockets  # noqa: E402

from app.services.tts.cartesia import CartesiaProvider  # noqa: E402
from app.services.voice.response_guard import count_sentences  # noqa: E402

URL = "ws://127.0.0.1:8100/ws/voice"

SAMPLES = {
    "hi-IN": "मेरा पेटीएम QR कोड काम नहीं कर रहा है, कृपया मदद करें।",
    "kn-IN": "ನನ್ನ ಪೇಟಿಎಂ ಕ್ಯೂಆರ್ ಕೋಡ್ ಕೆಲಸ ಮಾಡುತ್ತಿಲ್ಲ, ದಯವಿಟ್ಟು ಸಹಾಯ ಮಾಡಿ.",
    "en-IN": "My Paytm QR code is not working, can you help me?",
}


def synthesize(text: str, language: str) -> bytes:
    chunks = list(CartesiaProvider().stream(text, language=language))
    samples = np.frombuffer(b"".join(chunks), dtype="<f4")
    samples = np.clip(samples, -1.0, 1.0)
    return (samples * 32767.0).astype("<i2").tobytes()


async def main(language: str) -> int:
    pcm = synthesize(SAMPLES[language], language)
    print(f"{language}: {len(pcm) / 32000:.2f}s of synthesized speech")

    async with websockets.connect(URL, max_size=2**24, open_timeout=20) as ws:
        for _ in range(3):
            raw = await asyncio.wait_for(ws.recv(), timeout=30)
            payload = json.loads(raw)
            print("init:", payload.get("type"), payload.get("provider", ""))

        await ws.send(
            json.dumps(
                {
                    "type": "session_init",
                    "client_id": f"probe-{language}",
                    "document_ids": [],
                    "language": language,
                }
            )
        )

        chunk = 3200
        for i in range(0, len(pcm), chunk):
            await ws.send(pcm[i : i + chunk])
            await asyncio.sleep(0.1)
        for _ in range(16):
            await ws.send(b"\x00" * chunk)
            await asyncio.sleep(0.1)

        reply: list[str] = []
        deadline = asyncio.get_event_loop().time() + 90
        while asyncio.get_event_loop().time() < deadline:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=45)
            except asyncio.TimeoutError:
                break
            if isinstance(raw, (bytes, bytearray)):
                continue
            payload = json.loads(raw)
            kind = payload.get("type")
            if kind == "language_changed":
                print("language_changed:", payload.get("language"))
            elif kind == "transcript":
                print(
                    "transcript:",
                    payload.get("text"),
                    "| provider",
                    payload.get("provider"),
                )
            elif kind == "assistant_stream":
                reply.append(payload.get("token") or "")
            elif kind in {
                "assistant_segment_start",
                "assistant_stream_end",
                "voice_state",
                "interrupted",
                "turn_metrics",
            }:
                print(
                    kind,
                    {k: v for k, v in payload.items() if k not in {"type", "response_id"}},
                )
            elif kind == "error":
                print("ERROR:", payload)
            elif kind == "assistant_audio_end":
                print("audio_end; tokens:", len(reply))
                break

        text = "".join(reply).strip()
        print("reply:", text)
        print("reply_bytes:", len(text.encode("utf-8")))
        print("reply_sentences:", count_sentences(text))
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "en-IN")))
