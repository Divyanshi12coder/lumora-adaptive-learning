from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LearningGoal, MasteryScore, Topic, User


def goal_dict(db: Session, g: LearningGoal) -> dict:
    current = None
    if g.topic_id:
        m = db.scalar(select(MasteryScore).where(MasteryScore.user_id == g.user_id, MasteryScore.topic_id == g.topic_id))
        current = round(m.p_mastery, 3) if m else 0.0
    return {"id": g.id, "title": g.title, "topic_id": g.topic_id, "target_mastery": g.target_mastery,
            "current_mastery": current, "due_date": g.due_date.isoformat() if g.due_date else None,
            "status": g.status, "created_at": g.created_at.isoformat(),
            "reached": current is not None and g.target_mastery is not None and current >= g.target_mastery}


def list_goals(db: Session, user: User) -> list[dict]:
    goals = db.scalars(select(LearningGoal).where(LearningGoal.user_id == user.id)
                       .order_by(LearningGoal.status, LearningGoal.created_at.desc())).all()
    return [goal_dict(db, g) for g in goals]


def create(db: Session, user: User, title: str, topic_id: int | None, target: float | None, due: date | None) -> dict:
    if topic_id is not None and not db.get(Topic, topic_id):
        raise HTTPException(404, "Topic not found.")
    active = db.scalars(select(LearningGoal.id).where(LearningGoal.user_id == user.id, LearningGoal.status == "active")).all()
    if len(active) >= 10:
        raise HTTPException(409, "You already have 10 goals - finish one first!")
    g = LearningGoal(user_id=user.id, title=title.strip(), topic_id=topic_id,
                     target_mastery=target if target is not None else (0.8 if topic_id else None), due_date=due)
    db.add(g)
    db.commit()
    db.refresh(g)
    return goal_dict(db, g)


def _owned(db: Session, user: User, goal_id: int) -> LearningGoal:
    g = db.get(LearningGoal, goal_id)
    if not g or g.user_id != user.id:
        raise HTTPException(404, "Goal not found.")
    return g


def update_status(db: Session, user: User, goal_id: int, status: str) -> dict:
    g = _owned(db, user, goal_id)
    g.status = status
    g.completed_at = datetime.now(UTC) if status == "completed" else None
    db.commit()
    return goal_dict(db, g)


def delete(db: Session, user: User, goal_id: int) -> None:
    db.delete(_owned(db, user, goal_id))
    db.commit()
