import asyncio

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Literal

from app.core.config import settings
from app.core.qdrant import client
from app.services.emotion import emotion_provider
from app.services.session_repository import session_repository
from app.services.tts.factory import TTSFactory


router = APIRouter(prefix="/system", tags=["System"])


@router.get("/status")
async def system_status():
    redis_ready, qdrant_ready = await asyncio.gather(
        asyncio.to_thread(session_repository.ping),
        asyncio.to_thread(_qdrant_ready),
    )
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "providers": {
            "sarvam": "configured" if settings.SARVAM_API_KEY else "missing",
            "deepgram": "configured" if settings.DEEPGRAM_API_KEY else "missing",
            "groq": "configured" if settings.GROQ_API_KEY else "missing",
            "cartesia": "configured" if settings.CARTESIA_API_KEY else "missing",
            "cartesia_tts": (
                "configured"
                if settings.CARTESIA_API_KEY and settings.CARTESIA_VOICE_ID
                else "missing"
            ),
            "sarvam_tts": "configured" if settings.SARVAM_API_KEY else "missing",
            "qdrant": "ready" if qdrant_ready else "unavailable",
            "redis": session_repository.status,
            "emotion": emotion_provider.status,
        },
        "settings": {
            "tools_enabled": settings.VIA_ENABLE_TOOLS,
            "emotion_enabled": settings.VOICE_ENABLE_EMOTION,
            "mode": "lite" if settings.ENVIRONMENT == "production" else "local",
            "stt_provider": settings.VOICE_STT_PROVIDER,
            "stt_model": (
                settings.SARVAM_STT_MODEL
                if settings.VOICE_STT_PROVIDER == "sarvam"
                else settings.DEEPGRAM_MODEL
            ),
            "default_language": settings.VOICE_DEFAULT_LANGUAGE,
            "tts_provider": settings.VOICE_TTS_PROVIDER,
            "tts_model": (
                settings.SARVAM_TTS_MODEL
                if settings.VOICE_TTS_PROVIDER == "sarvam"
                else settings.CARTESIA_MODEL
            ),
        },
        "persistence": "ready" if redis_ready else "degraded",
    }


class SystemSettingsUpdate(BaseModel):
    tools_enabled: bool | None = None
    emotion_enabled: bool | None = None
    mode: str | None = None
    tts_provider: Literal["cartesia", "sarvam"] | None = None


@router.post("/settings")
async def update_settings(update: SystemSettingsUpdate):
    if update.tools_enabled is not None:
        settings.VIA_ENABLE_TOOLS = update.tools_enabled
    if update.emotion_enabled is not None:
        settings.VOICE_ENABLE_EMOTION = update.emotion_enabled
    if update.mode is not None:
        settings.ENVIRONMENT = "production" if update.mode == "lite" else "development"
    if update.tts_provider is not None:
        try:
            TTSFactory.set_provider(update.tts_provider)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "status": "ok",
        "settings": {
            "tools_enabled": settings.VIA_ENABLE_TOOLS,
            "emotion_enabled": settings.VOICE_ENABLE_EMOTION,
            "mode": "lite" if settings.ENVIRONMENT == "production" else "local",
            "tts_provider": settings.VOICE_TTS_PROVIDER,
        },
    }



def _qdrant_ready() -> bool:
    try:
        client.get_collections()
        return True
    except Exception:
        return False
