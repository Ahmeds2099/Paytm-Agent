"""Live smoke test for Sarvam realtime speech-to-text.

Usage (from ``backend/`` with the virtualenv active):

    python scripts/sarvam_stt_smoke.py --language hi-IN --sample
    python scripts/sarvam_stt_smoke.py --language kn-IN --sample
    python scripts/sarvam_stt_smoke.py --language en-IN --sample
    python scripts/sarvam_stt_smoke.py --language hi-IN --wav clip.wav

``--sample`` synthesizes a short sentence with Cartesia in the requested
language, so the test exercises both speech providers. A WAV file may be
16-bit PCM at any sample rate; it is resampled to 16 kHz mono.

The script prints the partial and final transcripts and exits non-zero if
Sarvam does not return a final transcript.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import wave
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

# Allow ``python scripts/...`` from the backend directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.services.stt.sarvam import SarvamStreamingSTT  # noqa: E402
from app.services.tts.cartesia import CartesiaProvider  # noqa: E402
from app.services.voice.language import normalize_language_code  # noqa: E402

SAMPLES = {
    "hi-IN": "मेरा पेटीएम QR कोड काम नहीं कर रहा है, कृपया मदद करें।",
    "kn-IN": "ನನ್ನ ಪೇಟಿಎಂ ಕ್ಯೂಆರ್ ಕೋಡ್ ಕೆಲಸ ಮಾಡುತ್ತಿಲ್ಲ, ದಯವಿಟ್ಟು ಸಹಾಯ ಮಾಡಿ.",
    "en-IN": "My Paytm QR code is not working, can you help me?",
    "auto": "My Paytm QR code is not working, can you help me?",
}


def load_wav(path: str) -> bytes:
    with wave.open(path, "rb") as handle:
        rate = handle.getframerate()
        channels = handle.getnchannels()
        width = handle.getsampwidth()
        frames = handle.readframes(handle.getnframes())

    if width != 2:
        raise SystemExit(
            f"{path}: expected 16-bit PCM, found {width * 8}-bit"
        )

    audio = np.frombuffer(frames, dtype="<i2")
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1).astype(np.int16)
    if rate != 16000:
        audio = resample_poly(audio, 16000, rate).astype(np.int16)

    loud = np.flatnonzero(np.abs(audio) > 300)
    if loud.size:
        audio = audio[max(0, loud[0] - 800) : loud[-1] + 800]

    return audio.tobytes()


def synthesize(text: str, language: str) -> bytes:
    provider = CartesiaProvider()
    chunks = list(provider.stream(text, language=language))
    if not chunks:
        raise SystemExit("Cartesia returned no audio")

    # ``stream`` yields raw little-endian float32 at 16 kHz.
    samples = np.frombuffer(b"".join(chunks), dtype="<f4")
    samples = np.clip(samples, -1.0, 1.0)
    return (samples * 32767.0).astype("<i2").tobytes()


async def run(pcm: bytes, language: str) -> int:
    partials: list[str] = []
    finals: list[str] = []
    errors: list[str] = []
    finished = asyncio.Event()

    async def on_transcript(event) -> None:
        if event.is_final:
            finals.append(event.text)
            print(f"FINAL  [{event.language or language}]: {event.text}")
            finished.set()
        else:
            partials.append(event.text)
            print(f"partial: {event.text}")

    async def on_error(reason: str) -> None:
        errors.append(reason)
        print(f"ERROR: {reason}")
        finished.set()

    provider = SarvamStreamingSTT(
        on_transcript=on_transcript,
        on_error=on_error,
        language_code=language,
    )

    await provider.start(language)

    chunk = 3200  # 100 ms
    try:
        for offset in range(0, len(pcm), chunk):
            await provider.send_audio(pcm[offset : offset + chunk])
            await asyncio.sleep(0.1)

        # Let Sarvam's VAD close the utterance.
        for _ in range(10):
            await provider.send_audio(b"\x00" * chunk)
            await asyncio.sleep(0.1)

        try:
            await asyncio.wait_for(finished.wait(), timeout=20)
        except asyncio.TimeoutError:
            print("ERROR: no final transcript within 20s")
            return 1
    finally:
        await provider.close()

    if errors:
        return 1
    if not finals:
        return 1

    print(f"PASS  {len(partials)} partials, {len(finals)} final(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--language",
        default=settings.VOICE_DEFAULT_LANGUAGE,
        help="auto, hi-IN, kn-IN or en-IN",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sample", action="store_true")
    source.add_argument("--text")
    source.add_argument("--wav")
    args = parser.parse_args()

    language = normalize_language_code(args.language)

    if not settings.SARVAM_API_KEY:
        print("ERROR: SARVAM_API_KEY is not configured in backend/.env")
        return 2

    if args.wav:
        print(f"Using WAV: {args.wav}")
        pcm = load_wav(args.wav)
    else:
        text = args.text or SAMPLES[language]
        print(f"Synthesizing ({language}): {text}")
        pcm = synthesize(text, language)

    print(f"Streaming {len(pcm) / 32000:.2f}s of 16 kHz audio")
    return asyncio.run(run(pcm, language))


if __name__ == "__main__":
    raise SystemExit(main())
