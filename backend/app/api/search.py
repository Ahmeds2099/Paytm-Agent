from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.models.query import QueryRequest
from app.services.embedder import EmbeddingService
from app.services.qdrant_service import QdrantService

router = APIRouter(
    prefix="/search",
    tags=["Search"],
)

embedder = EmbeddingService()


@router.post("/")
def semantic_search(request: QueryRequest):
    if not settings.VOICE_ENABLE_RAG:
        raise HTTPException(
            status_code=503,
            detail="Document search is disabled for this deployment.",
        )

    vector = embedder.embed_query(request.query)

    results = QdrantService.search(
        vector,
        document_ids=request.document_ids,
    )

    return {
        "query": request.query,
        "matches": results,
    }
