"""Subjects, topics and adaptively-presented lessons."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adaptive.engine import TeachingStrategy
from app.models import Course, Lesson, MasteryScore, Subject, Topic, User
from app.services import interactions
from app.services.learner_state import compute_strategy
from app.services.mastery import stage_for


def _masteries(db: Session, user: User) -> dict[int, MasteryScore]:
    return {m.topic_id: m for m in db.scalars(select(MasteryScore).where(MasteryScore.user_id == user.id))}


def topic_card(t: Topic, m: MasteryScore | None, subject: Subject) -> dict:
    p = m.p_mastery if m else 0.0
    attempts = m.attempts if m else 0
    lesson = t.lessons[0] if t.lessons else None
    return {
        "id": t.id, "slug": t.slug, "title": t.title, "summary": t.summary, "icon": t.icon,
        "subject": {"id": subject.id, "slug": subject.slug, "name": subject.name, "icon": subject.icon},
        "mastery": round(p, 3), "attempts": attempts, "stage": stage_for(p, attempts),
        "lesson_id": lesson.id if lesson else None, "lesson_title": lesson.title if lesson else None,
        "prerequisite_topic_id": t.prerequisite_topic_id,
    }


def list_subjects(db: Session, user: User) -> list[dict]:
    masteries = _masteries(db, user)
    out = []
    for s in db.scalars(select(Subject).order_by(Subject.sort_order)).all():
        topics = [t for c in s.courses for t in c.topics]
        cards = [topic_card(t, masteries.get(t.id), s) for t in topics]
        practiced = [c for c in cards if c["attempts"] > 0]
        next_topic = next((c for c in cards if c["stage"] != "master"), cards[0] if cards else None)
        out.append({
            "id": s.id, "slug": s.slug, "name": s.name, "description": s.description, "icon": s.icon,
            "topic_count": len(cards),
            "progress": round(sum(c["mastery"] for c in cards) / len(cards), 3) if cards else 0,
            "practiced_topics": len(practiced),
            "next_topic": next_topic,
            "topics": cards,
        })
    return out


def list_courses(db: Session) -> list[dict]:
    return [
        {"id": c.id, "slug": c.slug, "title": c.title, "description": c.description, "level": c.level,
         "subject_id": c.subject_id, "topic_ids": [t.id for t in c.topics]}
        for c in db.scalars(select(Course).order_by(Course.subject_id, Course.sort_order)).all()
    ]


def list_topics(db: Session, user: User, subject_slug: str | None = None) -> list[dict]:
    masteries = _masteries(db, user)
    stmt = select(Topic, Subject).join(Course, Course.id == Topic.course_id).join(Subject, Subject.id == Course.subject_id)
    if subject_slug:
        stmt = stmt.where(Subject.slug == subject_slug)
    return [topic_card(t, masteries.get(t.id), s) for t, s in db.execute(stmt.order_by(Subject.sort_order, Topic.sort_order)).all()]


def _sections(lesson: Lesson, strategy: TeachingStrategy) -> list[dict]:
    c = lesson.content
    high_support = strategy.band in ("high_support", "guided")
    examples = c.get("examples", [])
    n = max(1, strategy.example_count)
    sections = [
        {"key": "key_idea", "title": "The big idea", "kind": "text", "content": c["key_idea"], "shown": True},
        {"key": "steps", "title": "Step by step", "kind": "steps", "content": c["steps"],
         "shown": strategy.explanation_style in ("step_by_step", "worked_example") or high_support},
        {"key": "analogy", "title": "Think of it like this", "kind": "text", "content": c["analogy"],
         "shown": strategy.visual_support == "high" or high_support},
        {"key": "examples", "title": "Examples", "kind": "list", "content": examples[:n], "shown": True},
    ]
    if len(examples) > n:
        sections.append({"key": "more_examples", "title": "More examples", "kind": "list", "content": examples[n:],
                         "shown": False})
    sections += [
        {"key": "vocabulary", "title": "Words to know", "kind": "vocabulary",
         "content": [{"term": a, "meaning": b} for a, b in c.get("vocabulary", [])],
         "shown": strategy.content_density != "low" or high_support},
        {"key": "summary", "title": "Quick recap", "kind": "text", "content": c["summary"], "shown": True},
        {"key": "fun_fact", "title": "Fun fact", "kind": "text", "content": c["fun_fact"],
         "shown": strategy.content_density == "high"},
    ]
    return sections


def lesson_view(db: Session, user: User, lesson_id: int, start: bool = False) -> dict:
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found.")
    topic = lesson.topic
    strategy, _ = compute_strategy(db, user, topic.id, "lesson", persist=start)
    if start:
        interactions.record_event(db, user, "lesson_started", topic_id=topic.id, lesson_id=lesson.id)
    subject = topic.course.subject
    m = db.scalar(select(MasteryScore).where(MasteryScore.user_id == user.id, MasteryScore.topic_id == topic.id))
    return {
        "id": lesson.id,
        "title": lesson.title,
        "estimated_minutes": lesson.estimated_minutes,
        "topic": topic_card(topic, m, subject),
        "sections": _sections(lesson, strategy),
        "strategy": {
            "difficulty": strategy.difficulty, "explanation_style": strategy.explanation_style,
            "content_density": strategy.content_density, "pacing": strategy.pacing,
            "visual_support": strategy.visual_support, "read_aloud_suggested": strategy.read_aloud_suggested,
            "suggest_break": strategy.suggest_break, "learner_message": strategy.learner_message,
            "band": strategy.band,
        },
    }


def complete_lesson(db: Session, user: User, lesson_id: int, seconds: int, progress: float) -> dict:
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found.")
    interactions.record_event(db, user, "lesson_completed", topic_id=lesson.topic_id, lesson_id=lesson.id,
                              payload={"seconds": max(0, min(seconds, 7200)), "progress": max(0.0, min(progress, 1.0))})
    return {"lesson_id": lesson.id, "topic_id": lesson.topic_id, "message": "Lesson complete - fantastic reading!"}
