"""
Agent Control Room — FastAPI Application Entry Point

Reliability Layer for Autonomous AI Agents.
"""

import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import init_db, close_db, async_session
from app.models.org import Organization


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # ── Startup ──────────────────────────────────────
    await init_db()
    await _ensure_default_org()
    yield
    # ── Shutdown ─────────────────────────────────────
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Reliability Layer for Autonomous AI Agents. "
        "Full agent tracing, session recording & replay, "
        "cost intelligence, quality evaluation, and guardrails."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API Routers ─────────────────────────────
from app.api.ingest import router as ingest_router
from app.api.runs import router as runs_router
from app.api.costs import router as costs_router
from app.api.evaluations import router as eval_router
from app.api.guardrails import router as guardrails_router
from app.api.patterns import router as patterns_router

app.include_router(ingest_router, prefix="/api/v1")
app.include_router(runs_router, prefix="/api/v1")
app.include_router(costs_router, prefix="/api/v1")
app.include_router(eval_router, prefix="/api/v1")
app.include_router(guardrails_router, prefix="/api/v1")
app.include_router(patterns_router, prefix="/api/v1")


# ── Health Check ─────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"])
async def root():
    """Application root."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# ── Dev Helpers ──────────────────────────────────────

async def _ensure_default_org():
    """Create a default organization for development."""
    async with async_session() as session:
        result = await session.execute(
            select(Organization).where(Organization.name == "Default")
        )
        org = result.scalar_one_or_none()
        if org is None:
            org = Organization(
                name="Default",
                api_key="acr-dev-" + secrets.token_hex(16),
            )
            session.add(org)
            await session.commit()
            print(f"\n{'='*60}")
            print(f"  Default Organization Created")
            print(f"  API Key: {org.api_key}")
            print(f"  Use this key in the X-API-Key header.")
            print(f"{'='*60}\n")
        else:
            print(f"\n  Default org API Key: {org.api_key}\n")
