"""Dashboard, analytics, recommendations, goals and study planning."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.ai import llm, prompts
from app.ai.providers.base import LLMRequest
from app.ai.schemas import StudyPlan
from app.api.deps import get_current_user
from app.db.session import get_db
from app.ml.registry import registry
from app.models import User
from app.schemas import GoalCreate, GoalUpdate, StudyPlanRequest
from app.services import analytics, dashboard, goals, recommendations
from app.services.learner_state import compute_strategy

router = APIRouter()


@router.get("/dashboard", tags=["dashboard"])
def get_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return dashboard.build(db, user)


@router.get("/analytics", tags=["analytics"])
def get_analytics(days: int = Query(default=30, ge=7, le=120), user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    return analytics.build(db, user, days)


@router.get("/adaptive/strategy", tags=["adaptive engine"])
def current_strategy(topic_id: int | None = None, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """The full engine output (with factor weights) for this learner - used by the Insights view."""
    strategy, state = compute_strategy(db, user, topic_id, "lesson", persist=False)
    from app.adaptive.engine import signals_to_dict

    return {"strategy": strategy.model_dump(), "signals": signals_to_dict(state.signals)}


@router.get("/ml/model-card", tags=["analytics"])
def model_card(_: User = Depends(get_current_user)):
    """Training metadata and held-out metrics for the ML models."""
    registry.ensure_loaded()
    return registry.metrics() or {"detail": "Models not trained yet."}


@router.get("/recommendations", tags=["recommendations"])
def get_recommendations(refresh: bool = False, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recs = recommendations.refresh(db, user) if refresh else recommendations.active(db, user)
    return [{"id": r.id, "topic_id": r.topic_id, "lesson_id": r.lesson_id, "kind": r.kind, "score": r.score,
             "reason": r.reason, "factors": r.factors} for r in recs]


@router.post("/study-plan", tags=["recommendations"])
def study_plan(body: StudyPlanRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ranked = recommendations.rank(db, user)
    focus = [r["topic_title"] for r in ranked if r["kind"] in ("practice", "review", "learn")][:4]
    result = llm.run(LLMRequest(task="study_plan", system=prompts.SYSTEM_PROMPT,
                                messages=prompts.build_study_plan_messages(focus, body.minutes_per_day, body.days),
                                schema=StudyPlan,
                                context={"topics": focus, "minutes": body.minutes_per_day, "days": body.days},
                                max_tokens=900))
    return {**result.output.model_dump(), "is_demo": result.is_demo}


@router.get("/goals", tags=["goals"])
def list_goals(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return goals.list_goals(db, user)


@router.post("/goals", tags=["goals"], status_code=status.HTTP_201_CREATED)
def create_goal(body: GoalCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return goals.create(db, user, body.title, body.topic_id, body.target_mastery, body.due_date)


@router.patch("/goals/{goal_id}", tags=["goals"])
def update_goal(goal_id: int, body: GoalUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return goals.update_status(db, user, goal_id, body.status)


@router.delete("/goals/{goal_id}", tags=["goals"], status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goals.delete(db, user, goal_id)
