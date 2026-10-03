"""Child-friendly dashboard: what to learn today, how am I doing, what did I achieve."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Answer, InteractionEvent, LearningGoal, MasteryHistory, MasteryScore, Topic, User
from app.seed.run import DEMO_EMAIL
from app.services import achievements, content, recommendations
from app.services.learner_state import build_state

JOURNEY = ["start", "discover", "practice", "understand", "master", "explore"]
EVENT_TEXT = {
    "quiz_completed": "Finished a quiz on {topic}",
    "lesson_completed": "Read the lesson on {topic}",
    "lesson_started": "Started learning {topic}",
    "explanation_requested": "Asked Divi about {topic}",
    "hint_requested": "Used a hint in {topic}",
}


def _greeting(now: datetime) -> str:
    h = now.hour
    return "Good morning" if h < 12 else "Good afternoon" if h < 18 else "Good evening"


def journey_stage(cards: list[dict], any_activity: bool) -> str:
    if not any_activity:
        return "start"
    stages = [c["stage"] for c in cards]
    if sum(s == "master" for s in stages) >= 3:
        return "explore"
    if "master" in stages:
        return "master"
    if "understand" in stages:
        return "understand"
    if "practice" in stages:
        return "practice"
    return "discover"


def friendly_insight(direction: str, accuracy: float | None, attempts: int) -> dict:
    if attempts < 3:
        return {"title": "Let's get started!", "detail": "Try a lesson or a short quiz - Divi will learn how to help you best."}
    if direction == "improving":
        return {"title": "You're getting really good at this!",
                "detail": "Your recent answers suggest you're ready for a little more challenge."}
    if direction == "dipping" or (accuracy is not None and accuracy < 0.5):
        return {"title": "Every expert was once a beginner.",
                "detail": "Some questions felt tricky lately, so Divi will give you extra examples and hints."}
    if accuracy is not None and accuracy >= 0.8:
        return {"title": "You're on a roll!", "detail": "Your answers have been strong and steady. Keep exploring!"}
    return {"title": "Nice, steady learning!", "detail": "Keep practising a little at a time - it really adds up."}


def build(db: Session, user: User) -> dict:
    now = datetime.now(UTC)
    subjects = content.list_subjects(db, user)
    cards = [t for s in subjects for t in s["topics"]]
    practiced = [c for c in cards if c["attempts"] > 0]
    any_activity = db.scalar(select(func.count(InteractionEvent.id)).where(InteractionEvent.user_id == user.id)) or 0

    answered = db.scalar(select(func.count(Answer.id)).where(Answer.user_id == user.id)) or 0
    correct = db.scalar(select(func.count(Answer.id)).where(Answer.user_id == user.id, Answer.is_correct.is_(True))) or 0

    # Gentle weekly view (Mon-Sun) - no punishing streak counters.
    week_start = (now - timedelta(days=now.weekday())).date()
    event_days = set(
        d.date() if isinstance(d, datetime) else d
        for d in db.scalars(select(InteractionEvent.created_at).where(
            InteractionEvent.user_id == user.id,
            InteractionEvent.created_at >= datetime.combine(week_start - timedelta(days=60), datetime.min.time(), UTC),
        )).all()
    )
    week = [{"date": (week_start + timedelta(days=i)).isoformat(),
             "label": (week_start + timedelta(days=i)).strftime("%a"),
             "learned": (week_start + timedelta(days=i)) in event_days} for i in range(7)]
    streak = 0
    day: date = now.date()
    if day not in event_days:
        day -= timedelta(days=1)
    while day in event_days:
        streak += 1
        day -= timedelta(days=1)

    recs = recommendations.active(db, user)
    topic_titles = dict(db.execute(select(Topic.id, Topic.title)).all())
    card_by_id = {c["id"]: c for c in cards}
    rec_list = [
        {"id": r.id, "kind": r.kind, "reason": r.reason, "topic": card_by_id.get(r.topic_id),
         "lesson_id": r.lesson_id}
        for r in recs[:3]
    ]

    events = db.scalars(
        select(InteractionEvent)
        .where(InteractionEvent.user_id == user.id, InteractionEvent.event_type.in_(list(EVENT_TEXT)))
        .order_by(InteractionEvent.created_at.desc()).limit(8)
    ).all()
    recent = [
        {"type": e.event_type, "text": EVENT_TEXT[e.event_type].format(topic=topic_titles.get(e.topic_id, "a topic")),
         "at": e.created_at.isoformat(), "score": e.payload.get("score")}
        for e in events
    ]

    goals = []
    masteries = {m.topic_id: m.p_mastery for m in db.scalars(select(MasteryScore).where(MasteryScore.user_id == user.id))}
    for g in db.scalars(select(LearningGoal).where(LearningGoal.user_id == user.id, LearningGoal.status == "active")
                        .order_by(LearningGoal.due_date.is_(None), LearningGoal.due_date)).all():
        current = masteries.get(g.topic_id, 0.0) if g.topic_id else None
        goals.append({"id": g.id, "title": g.title, "topic_id": g.topic_id, "due_date": g.due_date.isoformat() if g.due_date else None,
                      "target": g.target_mastery, "current": round(current, 3) if current is not None else None})

    # Growth line: average mastery of practised topics per day (last 14 days).
    since = now - timedelta(days=13)
    hist = db.scalars(select(MasteryHistory).where(MasteryHistory.user_id == user.id, MasteryHistory.recorded_at >= since - timedelta(days=60))
                      .order_by(MasteryHistory.recorded_at)).all()
    latest: dict[int, float] = {}
    growth = []
    idx = 0
    for i in range(14):
        d = (since + timedelta(days=i)).date()
        while idx < len(hist) and hist[idx].recorded_at.date() <= d:
            latest[hist[idx].topic_id] = hist[idx].p_mastery
            idx += 1
        growth.append({"date": d.isoformat(), "mastery": round(sum(latest.values()) / len(latest), 3) if latest else None})

    state = build_state(db, user, None)
    stage = journey_stage(cards, bool(any_activity))
    badges = achievements.compute(db, user)
    return {
        "greeting": f"{_greeting(now)}, {user.display_name}!",
        "display_name": user.display_name,
        "is_demo_account": user.email == DEMO_EMAIL,
        "today": rec_list[0] if rec_list else None,
        "recommendations": rec_list,
        "progress": {
            "topics_total": len(cards),
            "topics_practiced": len(practiced),
            "topics_mastered": sum(1 for c in cards if c["stage"] == "master"),
            "average_mastery": round(sum(c["mastery"] for c in practiced) / len(practiced), 3) if practiced else 0,
            "questions_answered": answered,
            "correct_answers": correct,
        },
        "week": week,
        "weekly_goal_days": user.profile.weekly_goal_days if user.profile else 3,
        "learning_days_in_a_row": streak,
        "subjects": [{k: s[k] for k in ("id", "slug", "name", "icon", "progress", "practiced_topics", "topic_count", "next_topic")}
                     for s in subjects],
        "topic_mastery": sorted(practiced, key=lambda c: -c["mastery"]),
        "recent_activity": recent,
        "goals": goals,
        "achievements": badges,
        "journey": {"stages": JOURNEY, "current": stage, "index": JOURNEY.index(stage)},
        "insight": friendly_insight(state.trend_direction, state.signals.recent_accuracy, state.signals.attempts),
        "growth": growth,
    }
