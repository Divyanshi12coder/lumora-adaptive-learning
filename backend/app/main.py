"""Lumora API - FastAPI application factory."""

from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, documents, insights, learning, public, tutor
from app.core.config import get_settings
from app.core.middleware import RateLimitMiddleware, RequestSizeLimitMiddleware, SecurityHeadersMiddleware

log = logging.getLogger("lumora")

DESCRIPTION = """
**Lumora** - adaptive intelligence for every learner.

An adaptive learning API that observes learning interactions, estimates mastery
(Bayesian Knowledge Tracing), predicts struggle and engagement (scikit-learn),
chooses a teaching strategy (Adaptive Teaching Engine) and delivers grounded AI
tutoring (RAG over PostgreSQL + pgvector, pluggable LLM providers).

Lumora supports learning *preferences* and accessibility needs. It does **not**
diagnose or treat any medical, psychological or learning condition.
"""


def _startup() -> None:
    from app.db.base import Base
    from app.db.session import SessionLocal, engine
    from app.ml.registry import registry
    from app.seed.run import seed_curriculum

    settings = get_settings()
    if not settings.is_postgres:
        Base.metadata.create_all(engine)  # SQLite convenience; Postgres uses Alembic migrations
    if settings.seed_on_startup:
        with SessionLocal() as db:
            created = seed_curriculum(db)
            if any(created.values()):
                log.info("Seeded curriculum: %s", created)
    # Warm (or first-time train) ML models without blocking startup.
    threading.Thread(target=registry.ensure_loaded, daemon=True).start()


@asynccontextmanager
async def lifespan(_: FastAPI):
    _startup()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = FastAPI(
        title="Lumora API",
        version="1.0.0",
        description=DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        # Friendly, non-technical messages (shown to children) + structured detail for developers.
        errors = [
            {"field": ".".join(str(p) for p in e["loc"] if p not in ("body", "query")), "message": e["msg"]}
            for e in exc.errors()
        ]
        first = errors[0]["message"].removeprefix("Value error, ") if errors else "Please check your input."
        return JSONResponse({"detail": first, "errors": errors}, status_code=422)

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception):
        log.exception("Unhandled error: %s", exc)
        return JSONResponse({"detail": "Oops! Something went wrong on our side. Please try again."}, status_code=500)

    for router in (public.router, auth.router, learning.router, tutor.router, insights.router, documents.router):
        app.include_router(router, prefix="/api")

    @app.get("/", include_in_schema=False)
    def root():
        return {"name": "Lumora API", "docs": "/docs", "health": "/api/health"}

    return app


app = create_app()
