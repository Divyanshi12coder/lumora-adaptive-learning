"""Build training datasets from real interaction data stored in PostgreSQL."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.features import (
    ENGAGEMENT_FEATURES,
    PROFILE_FEATURES,
    STRUGGLE_FEATURES,
    AnswerRecord,
    SessionSnapshot,
    engagement_features,
    struggle_features,
    summarize_history,
)
from app.models import Answer, InteractionEvent, LearningSession, Question, QuizAttempt


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _answer_rows(db: Session):
    stmt = (
        select(Answer, Question.difficulty, QuizAttempt.topic_id)
        .join(Question, Question.id == Answer.question_id)
        .join(QuizAttempt, QuizAttempt.id == Answer.attempt_id)
        .order_by(Answer.user_id, QuizAttempt.topic_id, Answer.created_at, Answer.id)
    )
    return db.execute(stmt).all()


def to_record(answer: Answer, difficulty: int, option_count: int = 4) -> AnswerRecord:
    return AnswerRecord(
        correct=answer.is_correct,
        skipped=answer.skipped,
        difficulty=difficulty,
        response_ms=answer.response_ms,
        hints=answer.hints_used,
        changes=answer.answer_changes,
        confidence=answer.confidence,
        option_count=option_count,
        question_id=answer.question_id,
    )


def struggle_dataset_from_db(db: Session) -> pd.DataFrame:
    rows: list[dict] = []
    history: dict[tuple[int, int], list[AnswerRecord]] = defaultdict(list)
    for answer, difficulty, topic_id in _answer_rows(db):
        key = (answer.user_id, topic_id)
        feats = struggle_features(summarize_history(history[key]), difficulty)
        feats["label_incorrect"] = int(not answer.is_correct)
        feats["learner_id"] = answer.user_id
        rows.append(feats)
        history[key].append(to_record(answer, difficulty))
    return pd.DataFrame(rows, columns=[*STRUGGLE_FEATURES, "label_incorrect", "learner_id"])


def engagement_dataset_from_db(db: Session) -> pd.DataFrame:
    cutoff = datetime.now(UTC) - timedelta(minutes=30)
    sessions = db.scalars(select(LearningSession)).all()
    rows: list[dict] = []
    for s in sessions:
        end = _aware(s.ended_at) if s.ended_at else _aware(s.last_activity_at)
        if not s.ended_at and end > cutoff:
            continue  # still live - label unknown
        events = db.scalars(
            select(InteractionEvent).where(InteractionEvent.session_id == s.id).order_by(InteractionEvent.created_at)
        ).all()
        start = _aware(s.started_at)
        outcomes: list[bool] = []
        hints = 0
        skips: list[bool] = []
        prev = start
        for i, ev in enumerate(events):
            at = _aware(ev.created_at)
            if ev.event_type == "hint_requested":
                hints += 1
            if ev.event_type in ("question_answered", "question_skipped"):
                skipped = ev.event_type == "question_skipped"
                outcomes.append(bool(ev.payload.get("correct")) and not skipped)
                skips.append(skipped)
                recent = outcomes[-6:]
                streak = 0
                for o in reversed(outcomes):
                    if o:
                        break
                    streak += 1
                snap = SessionSnapshot(
                    session_minutes=(at - start).total_seconds() / 60,
                    event_count=i + 1,
                    recent_accuracy=sum(recent) / len(recent),
                    hint_rate=hints / len(outcomes),
                    skip_rate=sum(skips[-6:]) / len(recent),
                    mistake_streak=streak,
                    idle_seconds=(at - prev).total_seconds(),
                )
                feats = engagement_features(snap)
                feats["label_engaged"] = int((end - at).total_seconds() >= 300)
                feats["learner_id"] = s.user_id
                rows.append(feats)
            prev = at
    return pd.DataFrame(rows, columns=[*ENGAGEMENT_FEATURES, "label_engaged", "learner_id"])


def profile_dataset_from_db(db: Session, min_answers: int = 10) -> pd.DataFrame:
    by_user: dict[int, list[AnswerRecord]] = defaultdict(list)
    for answer, difficulty, _topic in _answer_rows(db):
        by_user[answer.user_id].append(to_record(answer, difficulty))
    rows = []
    for user_id, recs in by_user.items():
        if len(recs) < min_answers:
            continue
        rows.append(user_profile_features(db, user_id, recs))
    return pd.DataFrame(rows, columns=PROFILE_FEATURES)


def user_profile_features(db: Session, user_id: int, recs: list[AnswerRecord]) -> dict[str, float]:
    sessions = db.scalars(select(LearningSession).where(LearningSession.user_id == user_id)).all()
    minutes = [
        ((_aware(s.ended_at or s.last_activity_at) - _aware(s.started_at)).total_seconds() / 60) for s in sessions
    ]
    minutes = [m for m in minutes if m > 0.2]
    n = max(1, len(recs))
    return {
        "accuracy": sum(r.correct and not r.skipped for r in recs) / n,
        "hint_rate": sum(r.hints for r in recs) / n,
        "avg_response_ratio": sum(min(r.response_ratio, 4) for r in recs) / n,
        "skip_rate": sum(r.skipped for r in recs) / n,
        "avg_session_minutes": (sum(minutes) / len(minutes)) if minutes else 10.0,
    }
