"""Learning sessions and interaction event tracking."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InteractionEvent, LearningSession, User
from app.models.learning import EVENT_TYPES

SESSION_IDLE_TIMEOUT = timedelta(minutes=30)
ALLOWED_PAYLOAD_KEYS = {
    "correct", "response_ms", "progress", "section", "seconds", "feedback", "difficulty",
    "score", "intent", "from_index", "to_index", "attempt_id", "reason", "hints_used",
}


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def start_session(db: Session, user: User, at: datetime | None = None) -> LearningSession:
    at = at or datetime.now(UTC)
    s = LearningSession(user_id=user.id, started_at=at, last_activity_at=at)
    db.add(s)
    db.flush()
    db.add(InteractionEvent(user_id=user.id, session_id=s.id, event_type="session_started", payload={}, created_at=at))
    s.event_count = 1
    db.commit()
    return s


def end_session(db: Session, user: User, session_id: int, at: datetime | None = None) -> LearningSession:
    s = db.get(LearningSession, session_id)
    if not s or s.user_id != user.id:
        raise HTTPException(404, "Session not found.")
    if s.ended_at is None:
        at = at or datetime.now(UTC)
        s.ended_at = at
        s.last_activity_at = at
        db.add(InteractionEvent(user_id=user.id, session_id=s.id, event_type="session_ended", payload={}, created_at=at))
        s.event_count += 1
        db.commit()
    return s


def active_session(db: Session, user: User, create: bool = True, at: datetime | None = None) -> LearningSession | None:
    at = at or datetime.now(UTC)
    s = db.scalar(
        select(LearningSession)
        .where(LearningSession.user_id == user.id, LearningSession.ended_at.is_(None))
        .order_by(LearningSession.started_at.desc())
    )
    if s and at - _aware(s.last_activity_at) > SESSION_IDLE_TIMEOUT:
        s.ended_at = s.last_activity_at  # close stale session at its last activity
        db.commit()
        s = None
    if s is None and create:
        s = start_session(db, user, at=at)
    return s


def record_event(
    db: Session,
    user: User,
    event_type: str,
    *,
    session_id: int | None = None,
    topic_id: int | None = None,
    lesson_id: int | None = None,
    question_id: int | None = None,
    payload: dict | None = None,
    at: datetime | None = None,
    commit: bool = True,
) -> InteractionEvent:
    if event_type not in EVENT_TYPES:
        raise HTTPException(422, f"Unknown event type '{event_type}'.")
    at = at or datetime.now(UTC)
    if session_id is not None:
        session = db.get(LearningSession, session_id)
        if not session or session.user_id != user.id:
            raise HTTPException(404, "Session not found.")
    else:
        session = active_session(db, user, at=at)
    # Data minimisation: keep only known, non-identifying payload keys with primitive values.
    clean = {
        k: v for k, v in (payload or {}).items()
        if k in ALLOWED_PAYLOAD_KEYS and isinstance(v, int | float | bool | str) and len(str(v)) <= 60
    }
    ev = InteractionEvent(
        user_id=user.id, session_id=session.id if session else None, event_type=event_type, topic_id=topic_id,
        lesson_id=lesson_id, question_id=question_id, payload=clean, created_at=at,
    )
    db.add(ev)
    if session:
        session.last_activity_at = at
        session.event_count += 1
    if commit:
        db.commit()
    return ev
