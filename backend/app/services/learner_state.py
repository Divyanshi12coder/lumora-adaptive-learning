"""Builds the learner's current state and asks the adaptive engine for a strategy.

Pipeline:  interaction data (PostgreSQL)
             -> feature engineering (app.ml.features)
             -> ML predictions (struggle, engagement)
             -> adaptive engine (app.adaptive.engine)
             -> persisted strategy + predictions (audit / analytics)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adaptive.engine import (
    LearnerPreferenceInput,
    LearnerSignals,
    TeachingStrategy,
    decide_strategy,
    signals_to_dict,
)
from app.ml.features import AnswerRecord, SessionSnapshot, engagement_features, struggle_features, summarize_history
from app.ml.registry import Prediction, registry
from app.models import (
    AdaptiveStrategyRecord,
    Answer,
    InteractionEvent,
    LearningSession,
    MasteryScore,
    ModelPrediction,
    Question,
    QuizAttempt,
    User,
)

DIFFICULTY_NUM = {"easy": 1, "medium": 2, "hard": 3}


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def answer_history(db: Session, user_id: int, topic_id: int | None, limit: int = 60) -> list[AnswerRecord]:
    stmt = (
        select(Answer, Question.difficulty, Question.options)
        .join(Question, Question.id == Answer.question_id)
        .join(QuizAttempt, QuizAttempt.id == Answer.attempt_id)
        .where(Answer.user_id == user_id)
    )
    if topic_id is not None:
        stmt = stmt.where(QuizAttempt.topic_id == topic_id)
    rows = db.execute(stmt.order_by(Answer.created_at.desc(), Answer.id.desc()).limit(limit)).all()
    rows.reverse()
    return [
        AnswerRecord(
            correct=a.is_correct, skipped=a.skipped, difficulty=diff, response_ms=a.response_ms, hints=a.hints_used,
            changes=a.answer_changes, confidence=a.confidence, option_count=len(opts), question_id=a.question_id,
        )
        for a, diff, opts in rows
    ]


def preferences_input(user: User) -> LearnerPreferenceInput:
    p = user.preferences
    if p is None:
        return LearnerPreferenceInput()
    return LearnerPreferenceInput(
        explanation_length=p.explanation_length,  # type: ignore[arg-type]
        prefers_visuals=p.prefers_visuals,
        prefers_examples=p.prefers_examples,
        pace=p.pace,  # type: ignore[arg-type]
        length_bias=p.length_bias,
        difficulty_bias=p.difficulty_bias,
        read_aloud=p.read_aloud,
    )


@dataclass
class LearnerState:
    signals: LearnerSignals
    struggle: Prediction
    engagement: Prediction
    struggle_features: dict
    engagement_features: dict
    trend_direction: str


def session_snapshot(db: Session, user: User, recent_accuracy: float, hint_rate: float, skip_rate: float,
                     streak: int, at: datetime) -> SessionSnapshot:
    session = db.scalar(
        select(LearningSession)
        .where(LearningSession.user_id == user.id, LearningSession.ended_at.is_(None))
        .order_by(LearningSession.started_at.desc())
    )
    if session is None or at - _aware(session.last_activity_at) > timedelta(minutes=30):
        return SessionSnapshot(0.0, 0, recent_accuracy, hint_rate, skip_rate, streak, 0.0)
    return SessionSnapshot(
        session_minutes=max(0.0, (at - _aware(session.started_at)).total_seconds() / 60),
        event_count=session.event_count,
        recent_accuracy=recent_accuracy,
        hint_rate=hint_rate,
        skip_rate=skip_rate,
        mistake_streak=streak,
        idle_seconds=max(0.0, (at - _aware(session.last_activity_at)).total_seconds()),
    )


def build_state(db: Session, user: User, topic_id: int | None, at: datetime | None = None,
                next_difficulty: int = 2) -> LearnerState:
    at = at or datetime.now(UTC)
    history = answer_history(db, user.id, topic_id)
    summary = summarize_history(history)

    mastery_row = None
    if topic_id is not None:
        mastery_row = db.scalar(
            select(MasteryScore).where(MasteryScore.user_id == user.id, MasteryScore.topic_id == topic_id)
        )
    mastery = mastery_row.p_mastery if mastery_row else summary.mastery
    days_since = None
    if mastery_row and mastery_row.last_practiced_at:
        days_since = (at - _aware(mastery_row.last_practiced_at)).total_seconds() / 86400

    expl_stmt = select(func.count(InteractionEvent.id)).where(
        InteractionEvent.user_id == user.id,
        InteractionEvent.event_type == "explanation_requested",
        InteractionEvent.created_at >= at - timedelta(hours=24),
    )
    if topic_id is not None:
        expl_stmt = expl_stmt.where(InteractionEvent.topic_id == topic_id)
    explanation_requests = db.scalar(expl_stmt) or 0

    s_feats = struggle_features(summary, next_difficulty)
    s_feats["mastery"] = mastery
    struggle = registry.predict_struggle(s_feats)

    snap = session_snapshot(db, user, summary.recent_accuracy if summary.recent_accuracy is not None else 0.6,
                            summary.hint_rate, summary.skip_rate, summary.mistake_streak, at)
    e_feats = engagement_features(snap)
    engagement = registry.predict_engagement(e_feats)

    signals = LearnerSignals(
        recent_accuracy=summary.recent_accuracy,
        historical_accuracy=summary.historical_accuracy,
        mastery=mastery,
        attempts=summary.attempts,
        avg_response_ratio=summary.avg_response_ratio,
        hint_rate=summary.hint_rate,
        skip_rate=summary.skip_rate,
        mistake_streak=summary.mistake_streak,
        repeated_mistakes=summary.repeated_mistakes,
        answer_change_rate=summary.answer_change_rate,
        low_confidence_rate=summary.low_confidence_rate,
        explanation_requests=int(explanation_requests),
        session_minutes=snap.session_minutes,
        days_since_practice=days_since,
        trend_slope=summary.trend_slope,
        # Only use the struggle model once there is some topic history to condition on.
        struggle_probability=struggle.value if summary.attempts >= 3 else None,
        engagement_probability=engagement.value if snap.event_count >= 4 else None,
    )
    return LearnerState(signals, struggle, engagement, s_feats, e_feats, summary.trend_direction)


def compute_strategy(
    db: Session, user: User, topic_id: int | None, context: str, *, persist: bool = True,
    at: datetime | None = None,
) -> tuple[TeachingStrategy, LearnerState]:
    state = build_state(db, user, topic_id, at=at)
    strategy = decide_strategy(state.signals, preferences_input(user))
    if persist:
        db.add(AdaptiveStrategyRecord(
            user_id=user.id, topic_id=topic_id, context=context, support_score=strategy.support_score,
            strategy=strategy.model_dump(exclude={"factors", "rationale"}),
            signals=signals_to_dict(state.signals), created_at=at or datetime.now(UTC),
        ))
        for pred, feats in ((state.struggle, state.struggle_features), (state.engagement, state.engagement_features)):
            db.add(ModelPrediction(
                user_id=user.id, model_name=pred.model_name, model_version=pred.version,
                features={k: round(float(v), 4) for k, v in feats.items()}, prediction=round(pred.value, 4),
                label=pred.label, source=pred.source, detail=pred.detail, created_at=at or datetime.now(UTC),
            ))
        db.commit()
    return strategy, state
