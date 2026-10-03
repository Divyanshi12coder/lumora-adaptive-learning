from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.bkt import DEFAULT_PARAMS, update_mastery
from app.models import MasteryHistory, MasteryScore


def get_or_create(db: Session, user_id: int, topic_id: int) -> MasteryScore:
    ms = db.scalar(select(MasteryScore).where(MasteryScore.user_id == user_id, MasteryScore.topic_id == topic_id))
    if not ms:
        ms = MasteryScore(user_id=user_id, topic_id=topic_id, p_mastery=DEFAULT_PARAMS.p_init, attempts=0, correct=0)
        db.add(ms)
        db.flush()
    return ms


def apply_answer(
    db: Session, user_id: int, topic_id: int, *, correct: bool, skipped: bool, option_count: int, hints: int,
    at: datetime | None = None,
) -> MasteryScore:
    ms = get_or_create(db, user_id, topic_id)
    ms.p_mastery = update_mastery(ms.p_mastery, correct and not skipped, option_count=option_count,
                                  hints_used=0 if skipped else hints)
    ms.attempts += 1
    ms.correct += int(correct and not skipped)
    ms.last_practiced_at = at or datetime.now(UTC)
    return ms


def snapshot(db: Session, user_id: int, topic_id: int, at: datetime | None = None) -> None:
    ms = get_or_create(db, user_id, topic_id)
    db.add(MasteryHistory(user_id=user_id, topic_id=topic_id, p_mastery=ms.p_mastery,
                          recorded_at=at or datetime.now(UTC)))


def stage_for(p: float, attempts: int) -> str:
    """Learning-journey stage for a topic."""
    if attempts == 0:
        return "discover"
    if p < 0.5:
        return "practice"
    if p < 0.85:
        return "understand"
    return "master"
