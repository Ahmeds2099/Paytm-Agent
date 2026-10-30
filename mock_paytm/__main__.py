"""Mock Paytm API — FastAPI app on port 8200.

Run with:
    python -m mock_paytm

This is a local fixture server only. It never touches a real Paytm system.
"""
from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mock_paytm.models import HealthResponse
from mock_paytm.routes.qr import router as qr_router
from mock_paytm.routes.settlement import router as settlement_router
from mock_paytm.routes.refund import router as refund_router
from mock_paytm.routes.soundbox import router as soundbox_router

app = FastAPI(
    title="Mock Paytm API",
    description="Local fixture server for Phase 4 tool testing. Not a real Paytm endpoint.",
    version="mock-1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8100", "http://localhost:8100"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(qr_router)
app.include_router(settlement_router)
app.include_router(refund_router)
app.include_router(soundbox_router)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="running", version="mock-1.0")


if __name__ == "__main__":
    uvicorn.run(
        "mock_paytm.__main__:app",
        host="127.0.0.1",
        port=8200,
        log_level="info",
    )
