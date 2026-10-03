"""Personalised quiz generation and grading."""

from __future__ import annotations

import random
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Answer, Lesson, Question, QuizAttempt, Topic, User
from app.services import interactions, mastery, question_gen, recommendations
from app.services.learner_state import DIFFICULTY_NUM, compute_strategy

CORRECT_MESSAGES = ["Great job!", "You got it!", "Spot on - nice thinking!", "Brilliant!", "Yes! Well done."]
CHILD_STRATEGY_KEYS = ("difficulty", "hint_level", "option_count", "question_count", "learner_message", "tone",
                       "read_aloud_suggested", "suggest_break")


def _last_outcomes(db: Session, user_id: int, topic_id: int) -> dict[int, bool]:
    rows = db.execute(
        select(Answer.question_id, Answer.is_correct)
        .join(QuizAttempt, QuizAttempt.id == Answer.attempt_id)
        .where(Answer.user_id == user_id, QuizAttempt.topic_id == topic_id)
        .order_by(Answer.created_at, Answer.id)
    ).all()
    last: dict[int, bool] = {}
    for qid, ok in rows:
        last[qid] = ok
    return last


def select_questions(
    db: Session, user: User, topic: Topic, target: int, n: int, review: bool, seed: int
) -> list[Question]:
    bank = db.scalars(select(Question).where(Question.topic_id == topic.id)).all()
    last = _last_outcomes(db, user.id, topic.id)
    rng = random.Random(seed)

    review_pool = [q for q in bank if last.get(q.id) is False]
    rng.shuffle(review_pool)
    n_review = min(len(review_pool), max(1, n // 3) if review else n // 4)
    chosen: list[Question] = review_pool[:n_review]

    def key(q: Question) -> tuple:
        seen = q.id in last
        return (abs(q.difficulty - target), seen, rng.random())

    for q in sorted((q for q in bank if q not in chosen), key=key):
        if len(chosen) >= n:
            break
        if abs(q.difficulty - target) <= 1:
            chosen.append(q)

    unseen_at_target = [q for q in bank if q.id not in last and q.difficulty == target]
    if len(chosen) < n or len(unseen_at_target) == 0:
        # Freshen practice: try the LLM first (if configured), then procedural generators.
        need = max(n - len(chosen), 2)
        new = question_gen.with_llm(db, topic, target, need, user.id, [q.prompt for q in bank])
        if not new:
            new = question_gen.procedural(db, topic, target, need, seed)
        # swap already-mastered repeats out for fresh questions
        for q in new:
            if len(chosen) < n:
                chosen.append(q)
            else:
                for i in range(len(chosen) - 1, -1, -1):
                    if last.get(chosen[i].id) is True:
                        chosen[i] = q
                        break
    rng.shuffle(chosen)
    return chosen[:n]


def _option_map(q: Question, option_count: int, rng: random.Random) -> list[int]:
    idx = list(range(len(q.options)))
    if option_count < len(idx):
        distractors = [i for i in idx if i != q.correct_index]
        rng.shuffle(distractors)
        idx = sorted([q.correct_index, *distractors[: option_count - 1]])
    rng.shuffle(idx)
    return idx


def generate_quiz(db: Session, user: User, topic_id: int, at: datetime | None = None) -> dict:
    topic = db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found.")
    at = at or datetime.now(UTC)
    strategy, state = compute_strategy(db, user, topic_id, "quiz", at=at)
    target = DIFFICULTY_NUM[strategy.difficulty]
    seed = int(at.timestamp() * 1000) ^ user.id
    questions = select_questions(db, user, topic, target, strategy.question_count, strategy.review_required, seed)
    rng = random.Random(seed)
    maps = {q.id: _option_map(q, strategy.option_count, rng) for q in questions}
    before = mastery.get_or_create(db, user.id, topic_id).p_mastery

    attempt = QuizAttempt(
        user_id=user.id, topic_id=topic_id, difficulty=strategy.difficulty,
        strategy={**strategy.model_dump(exclude={"factors"}), "option_maps": {str(k): v for k, v in maps.items()}},
        question_ids=[q.id for q in questions], total=len(questions), mastery_before=before, started_at=at,
    )
    db.add(attempt)
    db.flush()
    interactions.record_event(db, user, "quiz_started", topic_id=topic_id,
                              payload={"attempt_id": attempt.id, "difficulty": strategy.difficulty}, at=at)
    return {
        "attempt_id": attempt.id,
        "topic": {"id": topic.id, "title": topic.title},
        "difficulty": strategy.difficulty,
        "strategy": {k: getattr(strategy, k) for k in CHILD_STRATEGY_KEYS},
        "questions": [
            {
                "id": q.id,
                "prompt": q.prompt,
                "options": [q.options[i] for i in maps[q.id]],
                "difficulty": q.difficulty,
                "source": q.source,
                "option_map": maps[q.id],
            }
            for q in questions
        ],
    }


def get_hint(db: Session, user: User, attempt_id: int, question_id: int) -> dict:
    attempt = _owned_attempt(db, user, attempt_id)
    if question_id not in attempt.question_ids:
        raise HTTPException(404, "Question is not part of this quiz.")
    q = db.get(Question, question_id)
    interactions.record_event(db, user, "hint_requested", topic_id=attempt.topic_id, question_id=question_id)
    level = attempt.strategy.get("hint_level", "guided")
    hint = q.hint
    if level == "full":
        hint = f"{q.hint} Remember: {q.explanation.split('.')[0]}."
    return {"question_id": question_id, "hint": hint, "hint_level": level}


def _owned_attempt(db: Session, user: User, attempt_id: int) -> QuizAttempt:
    attempt = db.get(QuizAttempt, attempt_id)
    if not attempt or attempt.user_id != user.id:
        raise HTTPException(404, "Quiz not found.")
    return attempt


def submit_quiz(
    db: Session, user: User, attempt_id: int, answers: list[dict], session_id: int | None = None,
    at: datetime | None = None,
) -> dict:
    attempt = _owned_attempt(db, user, attempt_id)
    if attempt.status == "completed":
        raise HTTPException(409, "This quiz was already submitted.")
    at = at or datetime.now(UTC)
    maps = {int(k): v for k, v in attempt.strategy.get("option_maps", {}).items()}
    by_qid = {a["question_id"]: a for a in answers}
    if not set(by_qid) <= set(attempt.question_ids):
        raise HTTPException(422, "Answers include questions that are not in this quiz.")

    results = []
    correct_total = 0
    for qid in attempt.question_ids:
        q = db.get(Question, qid)
        a = by_qid.get(qid, {"question_id": qid, "selected_index": None})
        shown = maps.get(qid, list(range(len(q.options))))
        sel = a.get("selected_index")
        skipped = sel is None
        if not skipped and not (0 <= sel < len(shown)):
            raise HTTPException(422, f"Invalid answer choice for question {qid}.")
        original = None if skipped else shown[sel]
        is_correct = original == q.correct_index
        correct_total += int(is_correct)
        hints = int(a.get("hints_used", 0) or 0)
        changes = int(a.get("answer_changes", 0) or 0)
        db.add(Answer(
            attempt_id=attempt.id, question_id=qid, user_id=user.id, selected_index=original, is_correct=is_correct,
            skipped=skipped, response_ms=max(0, int(a.get("response_ms", 0) or 0)), hints_used=hints,
            answer_changes=changes, confidence=a.get("confidence"), created_at=at,
        ))
        mastery.apply_answer(db, user.id, attempt.topic_id, correct=is_correct, skipped=skipped,
                             option_count=len(shown), hints=hints, at=at)
        interactions.record_event(
            db, user, "question_skipped" if skipped else "question_answered", session_id=session_id,
            topic_id=attempt.topic_id, question_id=qid,
            payload={"correct": is_correct, "response_ms": int(a.get("response_ms", 0) or 0), "hints_used": hints},
            at=at, commit=False,
        )
        if changes:
            interactions.record_event(db, user, "answer_changed", session_id=session_id, topic_id=attempt.topic_id,
                                      question_id=qid, at=at, commit=False)
        if is_correct:
            feedback = CORRECT_MESSAGES[qid % len(CORRECT_MESSAGES)]
        elif skipped:
            feedback = "That's okay - skipping is allowed. Here's how it works:"
        else:
            feedback = "Almost! Let's look at it another way."
        results.append({
            "question_id": qid,
            "prompt": q.prompt,
            "your_answer": None if skipped else q.options[original],
            "correct_answer": q.options[q.correct_index],
            "is_correct": is_correct,
            "skipped": skipped,
            "feedback": feedback,
            "explanation": q.explanation,
        })

    ms = mastery.get_or_create(db, user.id, attempt.topic_id)
    mastery.snapshot(db, user.id, attempt.topic_id, at=at)
    attempt.status = "completed"
    attempt.completed_at = at
    attempt.correct_count = correct_total
    attempt.score = round(correct_total / max(1, attempt.total), 3)
    attempt.mastery_after = ms.p_mastery
    db.flush()
    interactions.record_event(db, user, "quiz_completed", session_id=session_id, topic_id=attempt.topic_id,
                              payload={"attempt_id": attempt.id, "score": attempt.score}, at=at, commit=False)
    db.commit()

    next_strategy, _ = compute_strategy(db, user, attempt.topic_id, "quiz", at=at)
    attempt.next_difficulty = next_strategy.difficulty
    db.commit()
    recommendations.refresh(db, user, at=at)

    topic = db.get(Topic, attempt.topic_id)
    lesson = db.scalar(select(Lesson).where(Lesson.topic_id == topic.id).order_by(Lesson.sort_order))
    mistakes = [r for r in results if not r["is_correct"]]
    score = attempt.score or 0
    if score >= 0.85:
        headline = "Amazing work! You're becoming a real expert."
    elif score >= 0.6:
        headline = "Great effort! You're getting stronger every time."
    else:
        headline = "Good try! Every question helps your brain grow. Let's review together."
    return {
        "attempt_id": attempt.id,
        "topic": {"id": topic.id, "title": topic.title},
        "score": attempt.score,
        "correct": correct_total,
        "total": attempt.total,
        "headline": headline,
        "celebrate": score >= 0.6,
        "mastery_before": round(attempt.mastery_before or 0, 3),
        "mastery_after": round(ms.p_mastery, 3),
        "stage": mastery.stage_for(ms.p_mastery, ms.attempts),
        "results": results,
        "mistakes": mistakes,
        "next_difficulty": next_strategy.difficulty,
        "next_message": next_strategy.learner_message,
        "revision": {
            "needed": bool(mistakes) or next_strategy.review_required,
            "lesson_id": lesson.id if lesson else None,
            "lesson_title": lesson.title if lesson else None,
            "tutor_prompt": f"Can you explain {topic.title.lower()} in a different way?",
            "tips": [m["explanation"] for m in mistakes[:3]],
        },
    }
