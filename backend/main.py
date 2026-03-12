"""
FastAPI Application Entry Point.

AI Operations Automation — Agentic Workflow System for Business Reporting.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.utils.logger import setup_logging, get_logger
from backend.utils.error_handler import (
    AgentExecutionError,
    DataValidationError,
    global_exception_handler,
    agent_exception_handler,
    validation_exception_handler,
)

from backend.api import (
    workflows_router,
    reports_router,
    approvals_router,
    dashboard_router,
)

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("=" * 60)
    logger.info("  AI Operations Automation -- Starting")
    logger.info(f"  Environment: {settings.app_env}")
    logger.info(f"  Debug: {settings.app_debug}")
    logger.info("=" * 60)
    yield
    logger.info("AI Operations Automation -- Shutting down")


# ── Create FastAPI app ────────────────────────────────────────

app = FastAPI(
    title="AI Operations Automation",
    description=(
        "AI-powered operational automation platform that converts "
        "manual ERP reporting workflows into autonomous AI agent pipelines."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS Middleware ───────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception Handlers ───────────────────────────────────────

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(AgentExecutionError, agent_exception_handler)
app.add_exception_handler(DataValidationError, validation_exception_handler)

# ── Routers ──────────────────────────────────────────────────

app.include_router(workflows_router)
app.include_router(reports_router)
app.include_router(approvals_router)
app.include_router(dashboard_router)


# ── Health Check ─────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-operations-automation",
        "version": "0.1.0",
    }


@app.get("/", tags=["System"])
async def root():
    """API root — service info."""
    return {
        "name": "AI Operations Automation",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
