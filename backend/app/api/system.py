import asyncio

from fastapi import APIRouter

from app.core.config import settings
from app.core.qdrant import client
from app.services.emotion import emotion_provider
from app.services.session_repository import session_repository


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
            "tts_model": settings.CARTESIA_MODEL,
        },
        "persistence": "ready" if redis_ready else "degraded",
    }


from pydantic import BaseModel

class SystemSettingsUpdate(BaseModel):
    tools_enabled: bool | None = None
    emotion_enabled: bool | None = None
    mode: str | None = None


@router.post("/settings")
async def update_settings(update: SystemSettingsUpdate):
    if update.tools_enabled is not None:
        settings.VIA_ENABLE_TOOLS = update.tools_enabled
    if update.emotion_enabled is not None:
        settings.VOICE_ENABLE_EMOTION = update.emotion_enabled
    if update.mode is not None:
        settings.ENVIRONMENT = "production" if update.mode == "lite" else "development"
    return {
        "status": "ok",
        "settings": {
            "tools_enabled": settings.VIA_ENABLE_TOOLS,
            "emotion_enabled": settings.VOICE_ENABLE_EMOTION,
            "mode": "lite" if settings.ENVIRONMENT == "production" else "local",
        },
    }



def _qdrant_ready() -> bool:
    try:
        client.get_collections()
        return True
    except Exception:
        return False
