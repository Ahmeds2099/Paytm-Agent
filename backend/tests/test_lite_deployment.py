from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

BACKEND_DIR = Path(__file__).resolve().parents[1]


class LiteDeploymentTests(unittest.TestCase):
    def test_production_defaults_boot_without_heavy_local_ml_packages(self):
        environment = os.environ.copy()
        environment.update(
            {
                "ENVIRONMENT": "production",
                "PYTHON_DOTENV_DISABLED": "1",
                "QDRANT_URL": "",
                "QDRANT_API_KEY": "",
            }
        )
        for name in (
            "VOICE_VAD_PROVIDER",
            "VOICE_ALLOW_WHISPER_FALLBACK",
            "VOICE_ENABLE_EMOTION",
            "VIA_ENABLE_TOOLS",
            "VOICE_ENABLE_RAG",
        ):
            environment.pop(name, None)

        script = """
import builtins
import sys

blocked = {
    "av",
    "fastembed",
    "faster_whisper",
    "fitz",
    "funasr",
    "numpy",
    "onnxruntime",
    "qdrant_client",
    "silero_vad",
    "torch",
}
original_import = builtins.__import__

def reject_optional_ml(name, *args, **kwargs):
    if name.split(".", 1)[0] in blocked:
        raise ModuleNotFoundError(f"optional lite dependency blocked: {name}")
    return original_import(name, *args, **kwargs)

builtins.__import__ = reject_optional_ml

from app.core.config import settings
assert settings.ENVIRONMENT == "production"
assert settings.VOICE_VAD_PROVIDER == "energy"
assert settings.VOICE_ALLOW_WHISPER_FALLBACK is False
assert settings.VOICE_ENABLE_EMOTION is False
assert settings.VIA_ENABLE_TOOLS is False
assert settings.VOICE_ENABLE_RAG is False

from app.main import app
from app.services.voice.session import VoiceSession
from fastapi.testclient import TestClient
session = VoiceSession()
assert session.vad.engine.__class__.__name__ == "EnergyEngine"
assert app is not None
with TestClient(app) as client:
    status = client.get("/system/status")
    assert status.status_code == 200
    assert status.json()["settings"]["rag_enabled"] is False
    assert status.json()["providers"]["qdrant"] == "disabled"
    assert client.post("/search/", json={"query": "demo"}).status_code == 503
    assert client.post(
        "/upload/",
        files={"file": ("sample.json", b"{}", "application/json")},
    ).status_code == 503
assert not any(module.split(".", 1)[0] in blocked for module in sys.modules)
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=BACKEND_DIR,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"Lite application import failed:\n{result.stdout}\n{result.stderr}",
        )

    def test_file_transcription_is_explicitly_unavailable_in_lite_mode(self):
        import asyncio

        from app.api.stt import transcribe_audio

        with patch("app.api.stt.settings.VOICE_ALLOW_WHISPER_FALLBACK", False):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(transcribe_audio())

        self.assertEqual(raised.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
