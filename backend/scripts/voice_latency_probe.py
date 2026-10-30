"""Measure where a voice turn spends its time.

Synthesizes one short merchant sentence with Cartesia, streams it to the
running backend over the real websocket, and prints the latency of each
stage. Owner-run against a live backend on port 8100.

    .venv\\Scripts\\python.exe scripts\\voice_latency_probe.py
    .venv\\Scripts\\python.exe scripts\\voice_latency_probe.py hi-IN

Notes:
* the first turn after a backend restart is regularly slower (cold model
  connection). Run it twice and read the second run as the warm number.
* the sentence is fixed English by default, so runs are comparable over time.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import websockets  # noqa: E402

from app.services.tts.cartesia import CartesiaProvider  # noqa: E402

URL = "ws://127.0.0.1:8100/ws/voice"
TEXT = "My Paytm QR code is not working, can you help me?"


def synthesize(text: str, language: str) -> bytes:
    """Render text to 16-bit 16 kHz PCM so it can be sent as mic audio."""

    chunks = list(CartesiaProvider().stream(text, language=language))
    samples = np.frombuffer(b"".join(chunks), dtype="<f4")
    samples = np.clip(samples, -1.0, 1.0)
    return (samples * 32767.0).astype("<i2").tobytes()


async def main(language: str) -> int:
    pcm = synthesize(TEXT, language)

    async with websockets.connect(URL, max_size=2**24, open_timeout=20) as ws:
        for _ in range(3):
            await asyncio.wait_for(ws.recv(), timeout=30)

        await ws.send(
            json.dumps(
                {
                    "type": "session_init",
                    "client_id": f"latency-{int(time.time())}",
                    "document_ids": [],
                    "language": language,
                }
            )
        )

        # Drain language_changed before the turn starts.
        try:
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=1.5)
                if isinstance(raw, str) and json.loads(raw).get("type") == "language_changed":
                    break
        except asyncio.TimeoutError:
            pass

        chunk = 3200
        for i in range(0, len(pcm), chunk):
            await ws.send(pcm[i : i + chunk])
            await asyncio.sleep(0.1)

        # First silent chunk is treated as end of speech.
        t_end_speech = time.perf_counter()
        for _ in range(12):
            await ws.send(b"\x00" * chunk)
            await asyncio.sleep(0.1)

        first_audio = None
        first_token = None
        deadline = time.perf_counter() + 90

        while time.perf_counter() < deadline:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=45)
            except asyncio.TimeoutError:
                break
            if isinstance(raw, (bytes, bytearray)):
                if first_audio is None:
                    first_audio = time.perf_counter()
                    print(
                        f"first audio frame: +{(first_audio - t_end_speech) * 1000:.0f} ms"
                    )
                continue
            payload = json.loads(raw)
            kind = payload.get("type")
            if kind == "transcript":
                stamp = time.perf_counter()
                print(
                    f"final transcript: +{(stamp - t_end_speech) * 1000:.0f} ms  "
                    f"{payload.get('text')!r}"
                )
            elif kind == "assistant_stream" and first_token is None:
                first_token = time.perf_counter()
                print(f"first token: +{(first_token - t_end_speech) * 1000:.0f} ms")
            elif kind == "turn_metrics":
                print("turn_metrics:", json.dumps(payload.get("data"), ensure_ascii=False))
            elif kind == "error":
                print("ERROR:", payload)
            elif kind == "assistant_audio_end":
                break

        total = time.perf_counter() - t_end_speech
        print(f"turn complete: {total * 1000:.0f} ms")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "en-IN")))
