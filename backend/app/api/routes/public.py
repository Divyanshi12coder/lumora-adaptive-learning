"""Unauthenticated endpoints: health check and landing-page demos."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.adaptive.engine import ENGINE_VERSION, LearnerPreferenceInput
from app.ai.llm import get_provider
from app.core.config import get_settings
from app.db.session import get_db
from app.rag.embeddings import get_embedder
from app.schemas import AdaptivePreviewRequest, TutorDemoRequest
from app.services import demo

router = APIRouter()


@router.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    s = get_settings()
    provider = get_provider()
    return {
        "status": "ok",
        "app": s.app_name,
        "environment": s.environment,
        "database": "postgresql" if s.is_postgres else "sqlite",
        "ai_provider": provider.name,
        "ai_demo_mode": provider.is_demo,
        "embedding_provider": get_embedder().name,
        "engine_version": ENGINE_VERSION,
    }


@router.post("/adaptive/preview", tags=["adaptive engine"])
def adaptive_preview(body: AdaptivePreviewRequest):
    """Landing-page slider: runs the real adaptive engine on simulated signals for a learner level 0-100."""
    prefs = LearnerPreferenceInput(explanation_length=body.explanation_length, prefers_visuals=body.prefers_visuals,
                                   prefers_examples=body.prefers_examples, pace=body.pace)
    return demo.adaptive_preview(body.level, prefs)


@router.post("/demo/tutor", tags=["adaptive engine"])
def tutor_demo(body: TutorDemoRequest, db: Session = Depends(get_db)):
    """'Watch the Tutor Adapt' - engine + RAG + offline demo provider, no account needed."""
    return demo.tutor_demo(db, body.action, body.level, body.last_style)
