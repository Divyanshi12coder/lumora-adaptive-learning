"""AI tutor orchestration.

    learner message
      -> safety screen + PII redaction
      -> intent detection
      -> adaptive strategy (engine + ML)
      -> RAG retrieval (pgvector)
      -> structured prompt -> LLM provider (or demo) -> schema validation
      -> output safety screen
      -> persisted conversation (sources, strategy, provider)
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adaptive.engine import TeachingStrategy
from app.ai import llm, prompts
from app.ai.providers.base import LLMRequest
from app.ai.safety import screen_input, screen_output
from app.ai.schemas import TutorReply
from app.core.config import get_settings
from app.models import AIConversation, AIMessage, Answer, Lesson, Question, QuizAttempt, Topic, User
from app.rag import store
from app.services import interactions
from app.services.learner_state import DIFFICULTY_NUM, compute_strategy

INTENT_PATTERNS: list[tuple[str, str]] = [
    ("hint", r"\b(hint|clue|help me start|nudge)\b"),
    ("quiz", r"\b(quiz|test me|ask me a question|practice question|question for me)\b"),
    ("different", r"\b(different(ly)?|another way|other way)\b"),
    ("confused", r"(don'?t|do not) (understand|get it)|\bconfus|\bi'?m lost\b|makes no sense"),
    ("easier", r"\b(easier|simpler|simple|too hard|baby steps|like i'?m)\b"),
    ("explain", r"\b(explain|what is|what are|what's|how does|how do|why|tell me about|teach me)\b"),
]
STYLE_ROTATION = ["worked_example", "step_by_step", "guided_discovery", "concise"]
FEEDBACK_VALUES = {"helpful", "not_helpful", "too_long", "too_hard", "too_easy"}


def classify_intent(message: str) -> str:
    text = message.lower()
    for intent, pattern in INTENT_PATTERNS:
        if re.search(pattern, text):
            return intent
    return "general"


def _adjust_for_intent(strategy: TeachingStrategy, intent: str, last_style: str | None) -> TeachingStrategy:
    if intent in ("easier", "confused"):
        return strategy.model_copy(update={
            "difficulty": "easy", "explanation_style": "step_by_step", "content_density": "low",
            "hint_level": "full" if intent == "confused" else strategy.hint_level,
            "example_count": max(1, min(2, strategy.example_count)), "pacing": "slow", "tone": "gentle",
        })
    if intent == "different":
        current = last_style or strategy.explanation_style
        nxt = STYLE_ROTATION[(STYLE_ROTATION.index(current) + 1) % len(STYLE_ROTATION)]
        return strategy.model_copy(update={"explanation_style": nxt, "visual_support": "high"})
    return strategy


def _conversation(db: Session, user: User, conversation_id: int | None, topic_id: int | None, title: str):
    if conversation_id:
        conv = db.get(AIConversation, conversation_id)
        if not conv or conv.user_id != user.id:
            raise HTTPException(404, "Conversation not found.")
        return conv
    conv = AIConversation(user_id=user.id, topic_id=topic_id, title=title[:80] or "New chat")
    db.add(conv)
    db.flush()
    return conv


def _practice_question(db: Session, user: User, topic_id: int, difficulty: str) -> dict | None:
    missed = db.scalar(
        select(Question)
        .join(Answer, Answer.question_id == Question.id)
        .join(QuizAttempt, QuizAttempt.id == Answer.attempt_id)
        .where(Answer.user_id == user.id, QuizAttempt.topic_id == topic_id, Answer.is_correct.is_(False))
        .order_by(Answer.created_at.desc())
        .limit(1)
    )
    q = missed or db.scalar(
        select(Question).where(Question.topic_id == topic_id, Question.difficulty == DIFFICULTY_NUM[difficulty])
        .order_by(Question.id).limit(1)
    )
    return {"prompt": q.prompt, "options": q.options, "hint": q.hint} if q else None


def _safe_reply(text: str, follow_ups: list[str]) -> dict:
    return {"message": text, "steps": [], "examples": [], "check_question": None, "encouragement": "",
            "follow_ups": follow_ups}


def chat(
    db: Session, user: User, message: str, *, topic_id: int | None = None, conversation_id: int | None = None,
    intent: str | None = None,
) -> dict:
    now = datetime.now(UTC)
    safety = screen_input(message)
    if topic_id is not None and not db.get(Topic, topic_id):
        raise HTTPException(404, "Topic not found.")
    conv = _conversation(db, user, conversation_id, topic_id, safety.text)
    topic_id = topic_id or conv.topic_id
    user_msg = AIMessage(conversation_id=conv.id, role="user", content=safety.text, safety_flags=safety.flags,
                         created_at=now)
    db.add(user_msg)

    if safety.action != "allow":
        reply = _safe_reply(safety.message or "", ["Explain a topic", "Quiz me", "What should I learn today?"])
        msg = AIMessage(conversation_id=conv.id, role="assistant", content=reply["message"], intent="safety",
                        payload=reply, sources=[], provider="safety", is_demo=False,
                        safety_flags=[safety.category or "safety"])
        db.add(msg)
        db.commit()
        return _serialize(conv, msg, user_msg, strategy=None, notice=None)

    intent = intent if intent in prompts.INTENT_INSTRUCTIONS else classify_intent(message)
    history_rows = [m for m in conv.messages if m.id != user_msg.id and m.role in ("user", "assistant")]
    last_style = next(
        (m.strategy.get("explanation_style") for m in reversed(history_rows) if m.role == "assistant" and m.strategy),
        None,
    )

    # Ground the topic: explicit topic, conversation topic, or the best-matching document's topic.
    chunks = store.search(db, safety.text, user_id=user.id, topic_id=topic_id, k=get_settings().rag_top_k)
    if topic_id is None and chunks and chunks[0].topic_id:
        topic_id = chunks[0].topic_id
    topic = db.get(Topic, topic_id) if topic_id else None
    if topic and len(safety.text.split()) <= 6:
        # short prompts like "give me a hint" - retrieve with the topic as query context
        chunks = store.search(db, f"{safety.text} {topic.title} {topic.summary}", user_id=user.id,
                              topic_id=topic.id, k=get_settings().rag_top_k)

    strategy, _state = compute_strategy(db, user, topic_id, "tutor")
    strategy = _adjust_for_intent(strategy, intent, last_style)
    lesson = db.scalar(select(Lesson).where(Lesson.topic_id == topic_id).order_by(Lesson.sort_order)) if topic else None
    practice = _practice_question(db, user, topic.id, strategy.difficulty) if topic else None

    event = "hint_requested" if intent == "hint" else "explanation_requested"
    interactions.record_event(db, user, event, topic_id=topic_id, payload={"intent": intent}, commit=False)

    chunk_dicts = [c.__dict__ for c in chunks]
    request = LLMRequest(
        task="tutor",
        system=prompts.SYSTEM_PROMPT,
        messages=prompts.build_tutor_messages(
            strategy=strategy, intent=intent, learner_message=safety.text,
            topic_title=topic.title if topic else None, chunks=chunk_dicts,
            history=[{"role": m.role, "content": m.content} for m in history_rows],
        ),
        schema=TutorReply,
        context={
            "intent": intent, "learner_message": safety.text, "strategy": strategy.model_dump(),
            "topic_title": topic.title if topic else None, "chunks": chunk_dicts,
            "lesson": lesson.content if lesson else None, "practice_question": practice,
        },
    )
    result = llm.run(request)
    out: TutorReply = result.output  # type: ignore[assignment]

    check = screen_output(" ".join([out.message, *out.steps, *out.examples, out.check_question or ""]))
    if check.action != "allow":
        reply = _safe_reply(check.text, ["Explain a topic", "Quiz me"])
    else:
        reply = {
            "message": screen_output(out.message).text,
            "steps": out.steps[:6],
            "examples": out.examples[:4],
            "check_question": out.check_question,
            "encouragement": out.encouragement,
            "follow_ups": out.follow_ups[:4],
        }
    used = set(out.used_source_numbers)
    sources = [
        {"n": i, "document_id": c.document_id, "title": c.document_title, "section": c.section,
         "excerpt": c.text[:280], "score": c.score, "used": i in used, "source": c.source}
        for i, c in enumerate(chunks, start=1)
    ]
    notice = None
    if result.is_demo:
        notice = ("Demo mode: this answer was assembled from your learning materials without a paid AI model."
                  if not result.fallback_reason else
                  "The AI service was unavailable, so Divi answered from your learning materials (demo mode).")
    msg = AIMessage(
        conversation_id=conv.id, role="assistant", content=reply["message"], intent=intent, payload=reply,
        strategy=strategy.model_dump(exclude={"factors"}), sources=sources, provider=result.provider,
        is_demo=result.is_demo, safety_flags=check.flags,
    )
    db.add(msg)
    if topic_id and conv.topic_id is None:
        conv.topic_id = topic_id
    db.commit()
    return _serialize(conv, msg, user_msg, strategy=strategy, notice=notice)


def _serialize(conv: AIConversation, msg: AIMessage, user_msg: AIMessage, strategy: TeachingStrategy | None,
               notice: str | None) -> dict:
    return {
        "conversation_id": conv.id,
        "topic_id": conv.topic_id,
        "user_message": message_dict(user_msg),
        "message": message_dict(msg),
        "strategy": strategy.model_dump(exclude={"factors"}) if strategy else None,
        "notice": notice,
    }


def message_dict(m: AIMessage) -> dict:
    return {
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "intent": m.intent,
        "payload": m.payload or {},
        "sources": m.sources or [],
        "strategy": ({k: m.strategy.get(k) for k in ("difficulty", "explanation_style", "content_density",
                                                    "hint_level", "example_count", "band")}
                     if m.strategy else None),
        "provider": m.provider,
        "is_demo": m.is_demo,
        "feedback": m.feedback,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def give_feedback(db: Session, user: User, message_id: int, value: str) -> dict:
    if value not in FEEDBACK_VALUES:
        raise HTTPException(422, "Unknown feedback value.")
    msg = db.get(AIMessage, message_id)
    if not msg or msg.role != "assistant" or msg.conversation.user_id != user.id:
        raise HTTPException(404, "Message not found.")
    msg.feedback = value
    prefs = user.preferences

    def clip(x: float) -> float:
        return max(-1.0, min(1.0, x))

    if value == "too_long":
        prefs.length_bias = clip(prefs.length_bias + 0.25)
    elif value == "too_hard":
        prefs.difficulty_bias = clip(prefs.difficulty_bias + 0.25)
    elif value == "too_easy":
        prefs.difficulty_bias = clip(prefs.difficulty_bias - 0.25)
    elif value == "helpful":
        prefs.length_bias *= 0.9
        prefs.difficulty_bias *= 0.9
    interactions.record_event(db, user, "tutor_feedback", topic_id=msg.conversation.topic_id,
                              payload={"feedback": value}, commit=False)
    db.commit()
    return {"message_id": msg.id, "feedback": value, "length_bias": round(prefs.length_bias, 2),
            "difficulty_bias": round(prefs.difficulty_bias, 2)}


def list_conversations(db: Session, user: User) -> list[dict]:
    convs = db.scalars(
        select(AIConversation).where(AIConversation.user_id == user.id).order_by(AIConversation.updated_at.desc())
        .limit(30)
    ).all()
    return [{"id": c.id, "title": c.title, "topic_id": c.topic_id, "updated_at": c.updated_at.isoformat(),
             "message_count": len(c.messages)} for c in convs]


def conversation_messages(db: Session, user: User, conversation_id: int) -> dict:
    conv = db.get(AIConversation, conversation_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(404, "Conversation not found.")
    return {"id": conv.id, "title": conv.title, "topic_id": conv.topic_id,
            "messages": [message_dict(m) for m in conv.messages]}
