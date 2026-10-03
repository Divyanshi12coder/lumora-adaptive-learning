"""Public, anonymous landing-page demos - powered by the real adaptive engine.

No account, no stored data. The tutor demo always uses the offline demo
provider so public traffic can never spend paid LLM credits.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adaptive.engine import LearnerPreferenceInput, decide_strategy, signals_for_level, signals_to_dict
from app.ai.providers.base import LLMRequest
from app.ai.providers.demo import DemoProvider
from app.ai.schemas import TutorReply
from app.models import Lesson, Question, Topic
from app.rag import store

ACTIONS = {
    "understand": (18, "Great - you understood! Divi raises the challenge a little."),
    "confused": (-22, "No problem - Divi slows down and adds more guidance."),
    "hint": (-8, "Divi offers a clue and keeps hints guided."),
    "different": (0, "Divi switches to a different explanation style."),
}
STYLES = ["worked_example", "step_by_step", "guided_discovery", "concise"]
INTENT_FOR = {"understand": "explain", "confused": "confused", "hint": "hint", "different": "different"}


def adaptive_preview(level: float, prefs: LearnerPreferenceInput) -> dict:
    signals = signals_for_level(level)
    strategy = decide_strategy(signals, prefs)
    return {"level": level, "signals": signals_to_dict(signals), "strategy": strategy.model_dump()}


def tutor_demo(db: Session, action: str, level: float, last_style: str | None) -> dict:
    delta, explanation = ACTIONS[action]
    new_level = max(0.0, min(100.0, level + delta))
    signals = signals_for_level(new_level)
    if action == "hint":
        signals.hint_rate = min(1.5, signals.hint_rate + 0.5)
    strategy = decide_strategy(signals, LearnerPreferenceInput())
    if action == "different":
        cur = last_style or strategy.explanation_style
        strategy = strategy.model_copy(update={"explanation_style": STYLES[(STYLES.index(cur) + 1) % len(STYLES)]})
    if action == "confused":
        strategy = strategy.model_copy(update={"explanation_style": "step_by_step", "content_density": "low",
                                               "tone": "gentle"})

    topic = db.scalar(select(Topic).where(Topic.slug == "fractions"))
    lesson = db.scalar(select(Lesson).where(Lesson.topic_id == topic.id)) if topic else None
    q = db.scalar(select(Question).where(Question.topic_id == topic.id, Question.difficulty == 3).limit(1)) if topic else None
    chunks = store.search(db, "compare fractions which is bigger", user_id=None, topic_id=topic.id if topic else None, k=3)
    reply: TutorReply = DemoProvider().generate(LLMRequest(  # type: ignore[assignment]
        task="tutor", system="", messages=[], schema=TutorReply,
        context={"intent": INTENT_FOR[action], "learner_message": "Which is bigger: 1/3 or 1/5?",
                 "strategy": strategy.model_dump(), "topic_title": "Fractions", "chunks": [c.__dict__ for c in chunks],
                 "lesson": lesson.content if lesson else None,
                 "practice_question": {"prompt": q.prompt, "options": q.options, "hint": q.hint} if q else None},
    ))
    return {
        "level": new_level,
        "explanation": explanation,
        "question": "Which is bigger: 1/3 or 1/5?",
        "strategy": strategy.model_dump(exclude={"factors"}),
        "reply": reply.model_dump(),
        "sources": [{"title": c.document_title, "section": c.section} for c in chunks[:2]],
        "provider": "demo",
    }
