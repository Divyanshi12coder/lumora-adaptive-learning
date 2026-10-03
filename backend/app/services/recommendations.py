"""Recommendation ranking.

Each topic becomes a candidate (learn / practice / review / challenge) with an
interpretable linear score over: mastery gap, spaced-repetition due-ness
(forgetting curve), prerequisite readiness and interest. Factors are stored with
each recommendation so the Insights view can explain the ranking.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Course, Lesson, MasteryScore, Recommendation, Topic, User

REASONS = {
    "learn": "You haven't explored this yet - it could be your next adventure!",
    "practice": "A little more practice will make this super strong.",
    "review": "It's been a while - a quick review keeps it fresh in your memory.",
    "challenge": "You've mastered this! Ready for a bonus challenge?",
}


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def rank(db: Session, user: User, at: datetime | None = None) -> list[dict]:
    at = at or datetime.now(UTC)
    topics = db.scalars(select(Topic)).all()
    masteries = {m.topic_id: m for m in db.scalars(select(MasteryScore).where(MasteryScore.user_id == user.id))}
    fav_subject = user.profile.favorite_subject_id if user.profile else None
    subject_of = dict(db.execute(select(Topic.id, Course.subject_id).join(Course, Course.id == Topic.course_id)).all())

    out = []
    for t in topics:
        m = masteries.get(t.id)
        p = m.p_mastery if m else 0.2
        attempts = m.attempts if m else 0
        days = (at - _aware(m.last_practiced_at)).total_seconds() / 86400 if m and m.last_practiced_at else None
        prereq = masteries.get(t.prerequisite_topic_id) if t.prerequisite_topic_id else None
        readiness = 1.0 if not t.prerequisite_topic_id else min(1.0, (prereq.p_mastery if prereq else 0.2) / 0.5)
        interest = 1.0 if fav_subject and subject_of.get(t.id) == fav_subject else 0.0
        due = 1 - math.exp(-(days or 0) / 7)

        if attempts == 0:
            kind = "learn"
            score = 0.45 * readiness + 0.25 * interest + 0.2 + 0.1 * (1 - t.sort_order / 5)
        elif p < 0.85:
            kind = "review" if (days or 0) >= 5 and p >= 0.6 else "practice"
            score = 0.5 * (1 - p) + 0.25 * due + 0.15 * readiness + 0.1 * interest + 0.15
        elif (days or 0) >= 5:
            kind = "review"
            score = 0.55 * due + 0.1 * (1 - p) + 0.1 * interest + 0.1
        else:
            kind = "challenge"
            score = 0.25 + 0.15 * interest
        factors = {"mastery": round(p, 3), "days_since_practice": round(days, 1) if days is not None else None,
                   "readiness": round(readiness, 3), "interest": interest, "due": round(due, 3)}
        out.append({"topic_id": t.id, "topic_title": t.title, "kind": kind, "score": round(score, 4),
                    "reason": REASONS[kind], "factors": factors})
    out.sort(key=lambda r: r["score"], reverse=True)
    return out


def refresh(db: Session, user: User, at: datetime | None = None, top_n: int = 5) -> list[Recommendation]:
    ranked = rank(db, user, at)[:top_n]
    db.execute(
        update(Recommendation)
        .where(Recommendation.user_id == user.id, Recommendation.status == "active")
        .values(status="replaced")
    )
    recs = []
    for r in ranked:
        lesson_id = db.scalar(select(Lesson.id).where(Lesson.topic_id == r["topic_id"]).order_by(Lesson.sort_order))
        rec = Recommendation(user_id=user.id, topic_id=r["topic_id"], lesson_id=lesson_id, kind=r["kind"],
                             score=r["score"], reason=r["reason"], factors=r["factors"],
                             created_at=at or datetime.now(UTC))
        db.add(rec)
        recs.append(rec)
    db.commit()
    return recs


def active(db: Session, user: User) -> list[Recommendation]:
    recs = db.scalars(
        select(Recommendation)
        .where(Recommendation.user_id == user.id, Recommendation.status == "active")
        .order_by(Recommendation.score.desc())
    ).all()
    return list(recs) if recs else refresh(db, user)
