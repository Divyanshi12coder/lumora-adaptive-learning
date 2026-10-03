"""Idempotent seeding: curriculum, question bank, RAG library and (optionally) a demo learner.

    python -m app.seed.run              # curriculum + RAG ingestion
    python -m app.seed.run --demo-user  # also create demo@lumora.app with SIMULATED history
"""

from __future__ import annotations

import argparse
import logging
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Course, Document, Lesson, Question, Subject, Topic
from app.rag.pipeline import ingest_document
from app.seed.curriculum import CURRICULUM

log = logging.getLogger("lumora.seed")

DEMO_EMAIL = "demo@lumora.app"
DEMO_PASSWORD = "LumoraDemo2026!"


def lesson_markdown(lesson: dict, topic_title: str) -> str:
    c = lesson.get("content", lesson)
    # No body text directly under the H1, so no near-empty "title" chunk is created;
    # the title/topic context is added to every chunk's embedding text at ingestion.
    parts = [f"# {lesson['title']} ({topic_title})", "## Key idea", c["key_idea"], "## Step by step"]
    parts += [f"{i}. {s}" for i, s in enumerate(c["steps"], start=1)]
    parts += ["## Examples", *[f"- {e}" for e in c["examples"]]]
    parts += ["## Think of it like this", c["analogy"], "## Words to know"]
    parts += [f"- {term}: {meaning}" for term, meaning in c["vocabulary"]]
    parts += ["## Summary", c["summary"], "## Fun fact", c["fun_fact"]]
    return "\n\n".join(parts)


def seed_curriculum(db: Session) -> dict[str, int]:
    created = {"subjects": 0, "topics": 0, "questions": 0, "documents": 0}
    for s_order, subj in enumerate(CURRICULUM):
        subject = db.scalar(select(Subject).where(Subject.slug == subj["slug"]))
        if not subject:
            subject = Subject(slug=subj["slug"], name=subj["name"], description=subj["description"],
                              icon=subj["icon"], sort_order=s_order)
            db.add(subject)
            db.flush()
            created["subjects"] += 1
        c = subj["course"]
        course = db.scalar(select(Course).where(Course.slug == c["slug"]))
        if not course:
            course = Course(subject_id=subject.id, slug=c["slug"], title=c["title"], description=c["description"])
            db.add(course)
            db.flush()

        prev_topic: Topic | None = None
        for t_order, t in enumerate(subj["topics"]):
            topic = db.scalar(select(Topic).where(Topic.slug == t["slug"]))
            if not topic:
                topic = Topic(course_id=course.id, slug=t["slug"], title=t["title"], summary=t["summary"],
                              icon=t["icon"], sort_order=t_order,
                              prerequisite_topic_id=prev_topic.id if prev_topic else None)
                db.add(topic)
                db.flush()
                created["topics"] += 1
                lesson_data = t["lesson"]
                content = {k: v for k, v in lesson_data.items() if k != "title"}
                db.add(Lesson(topic_id=topic.id, title=lesson_data["title"], content=content,
                              estimated_minutes=8))
                for prompt, options, correct, explanation, hint, difficulty in t["questions"]:
                    db.add(Question(topic_id=topic.id, prompt=prompt, options=options, correct_index=correct,
                                    explanation=explanation, hint=hint, difficulty=difficulty, source="seed"))
                    created["questions"] += 1
            prev_topic = topic

            if not db.scalar(select(Document).where(Document.topic_id == topic.id, Document.source == "system")):
                md = lesson_markdown(t["lesson"], t["title"])
                doc = Document(owner_id=None, topic_id=topic.id, title=t["lesson"]["title"],
                               filename=f"{t['slug']}.md", content_type="text/markdown", source="system",
                               raw_text=md, char_count=len(md))
                db.add(doc)
                db.flush()
                ingest_document(db, doc)
                created["documents"] += 1
    db.commit()
    return created


def seed_demo_user(db: Session) -> None:
    """Create a demo learner with SIMULATED practice history so the dashboard
    has something to show. The UI labels this account as demo data."""
    from app.models import User
    from app.services import auth as auth_service
    from app.services import interactions
    from app.services import quiz as quiz_service

    if db.scalar(select(User).where(User.email == DEMO_EMAIL)):
        return
    user = auth_service.register(db, DEMO_EMAIL, DEMO_PASSWORD, "Demo Learner")
    rng = random.Random(42)
    topics = db.scalars(select(Topic).order_by(Topic.id)).all()
    skill = {t.id: rng.uniform(0.35, 0.85) for t in topics}
    start = datetime.now(UTC) - timedelta(days=13)
    for day in range(14):
        if rng.random() < 0.35:
            continue  # rest days are normal
        when = start + timedelta(days=day, hours=16)
        session = interactions.start_session(db, user, at=when)
        for topic in rng.sample(topics, k=2):
            attempt = quiz_service.generate_quiz(db, user, topic.id, at=when)
            answers = []
            for i, q in enumerate(attempt["questions"]):
                p = min(0.95, skill[topic.id] + day * 0.012 - (q["difficulty"] - 2) * 0.12)
                q_obj = db.get(Question, q["id"])
                correct = rng.random() < p
                shown = q["option_map"]
                selected = shown.index(q_obj.correct_index) if correct else rng.choice(
                    [k for k in range(len(shown)) if shown[k] != q_obj.correct_index])
                answers.append({"question_id": q["id"], "selected_index": selected,
                                "response_ms": int(rng.uniform(8000, 45000)),
                                "hints_used": int(rng.random() < 1 - p), "answer_changes": 0,
                                "confidence": 3 if correct else rng.choice([1, 2])})
                when += timedelta(seconds=40 + i * 5)
            quiz_service.submit_quiz(db, user, attempt["attempt_id"], answers, session_id=session.id, at=when)
        interactions.end_session(db, user, session.id, at=when + timedelta(minutes=2))
    log.info("Demo learner created: %s (simulated history)", DEMO_EMAIL)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-user", action="store_true")
    args = parser.parse_args()
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        print("Seeded:", seed_curriculum(db))
        if args.demo_user:
            seed_demo_user(db)
            print(f"Demo learner ready: {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
