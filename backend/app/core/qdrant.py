from app.core.config import settings

if settings.VOICE_ENABLE_RAG:
    # pyrefly: ignore [missing-import]
    from qdrant_client import QdrantClient

    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )
else:
    client = None