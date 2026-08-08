"""
DocIntel AI — FastAPI Application Entry Point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup: initialize database
    await init_db()
    yield
    # Shutdown: cleanup

app = FastAPI(
    title="DocIntel AI",
    description="Multi-Agent Document Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from app.api.documents import router as documents_router  # noqa: E402
from app.api.query import router as query_router  # noqa: E402
from app.api.extract import router as extract_router  # noqa: E402
from app.api.ws import router as ws_router  # noqa: E402

app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(query_router, prefix="/api", tags=["Query"])
app.include_router(extract_router, prefix="/api", tags=["Extraction"])
app.include_router(ws_router, prefix="/api", tags=["WebSocket"])

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "docintel-ai"}
