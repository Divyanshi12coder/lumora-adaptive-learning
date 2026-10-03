"""Question generation beyond the curated bank.

1. Procedural generators (maths) - always available, exact answers, no LLM needed.
2. LLM generation with RAG context - used when a real AI provider is configured.
   Output is schema-validated and sanity-checked before it is stored.
"""

from __future__ import annotations

import random

from sqlalchemy.orm import Session

from app.ai import llm, prompts
from app.ai.providers.base import LLMRequest
from app.ai.safety import screen_output
from app.ai.schemas import GeneratedQuiz
from app.models import Question, Topic
from app.rag import store

DIFF_LABEL = {1: "easy", 2: "medium", 3: "hard"}


def _mc(rng: random.Random, correct: int, spread: int) -> tuple[list[str], int]:
    opts = {correct}
    while len(opts) < 4:
        cand = correct + rng.randint(-spread, spread)
        if cand > 0:
            opts.add(cand)
    ordered = sorted(opts)
    rng.shuffle(ordered)
    return [str(o) for o in ordered], ordered.index(correct)


def _multiplication(rng: random.Random, difficulty: int) -> dict:
    hi = {1: 5, 2: 9, 3: 12}[difficulty]
    a, b = rng.randint(2, hi), rng.randint(2, hi)
    options, idx = _mc(rng, a * b, max(3, a))
    return {
        "prompt": f"What is {a} × {b}?",
        "options": options,
        "correct_index": idx,
        "explanation": f"{a} groups of {b} make {a * b}.",
        "hint": f"Try skip-counting by {b}, {a} times.",
    }


def _fractions(rng: random.Random, difficulty: int) -> dict:
    if difficulty == 1:
        d = rng.randint(3, 10)
        n = rng.randint(1, d - 1)
        options = [f"{n}/{d}"]
        # Common misconceptions first; dict.fromkeys de-duplicates (e.g. 2/4 vs (4-2)/4).
        for cand in dict.fromkeys([f"{d}/{n}", f"{d - n}/{d}", f"{n}/{d + 1}", f"{n + 1}/{d}", f"{n}/{d - 1}"]):
            if cand not in options and len(options) < 4:
                options.append(cand)
        order = list(range(4))
        rng.shuffle(order)
        return {
            "prompt": f"A cake is cut into {d} equal pieces. You eat {n}. What fraction did you eat?",
            "options": [options[i] for i in order],
            "correct_index": order.index(0),
            "explanation": f"{n} pieces out of {d} equal pieces is {n}/{d}.",
            "hint": "The total number of pieces goes on the bottom.",
        }
    if difficulty == 2:
        d = rng.randint(4, 12)
        a, b = rng.sample(range(1, d), 2)
        big = max(a, b)
        return {
            "prompt": f"Which fraction is bigger: {a}/{d} or {b}/{d}?",
            "options": [f"{a}/{d}", f"{b}/{d}", "They are equal", "You can't tell"],
            "correct_index": 0 if big == a else 1,
            "explanation": f"Both fractions have {d} equal parts, so the one with more parts ({big}) is bigger.",
            "hint": "The bottom numbers match - compare the tops.",
        }
    a, b = rng.sample(range(2, 11), 2)
    return {
        "prompt": f"Which is bigger: 1/{a} or 1/{b}?",
        "options": [f"1/{a}", f"1/{b}", "They are equal", "It depends"],
        "correct_index": 0 if a < b else 1,
        "explanation": f"Sharing between fewer people gives bigger pieces, so 1/{min(a, b)} is bigger.",
        "hint": "Would you rather share a pizza with fewer or more friends?",
    }


GENERATORS = {"multiplication": _multiplication, "fractions": _fractions}


def procedural(db: Session, topic: Topic, difficulty: int, count: int, seed: int) -> list[Question]:
    gen = GENERATORS.get(topic.slug)
    if not gen:
        return []
    rng = random.Random(seed)
    out: list[Question] = []
    seen_prompts: set[str] = set()
    for _ in range(count * 4):
        q = gen(rng, difficulty)
        if q["prompt"] in seen_prompts or len(set(q["options"])) != len(q["options"]):
            continue
        seen_prompts.add(q["prompt"])
        obj = Question(topic_id=topic.id, difficulty=difficulty, source="generated", **q)
        db.add(obj)
        out.append(obj)
        if len(out) >= count:
            break
    db.flush()
    return out


def _valid(q) -> bool:
    return (
        2 <= len(q.options) <= 4
        and 0 <= q.correct_index < len(q.options)
        and len(set(o.strip().lower() for o in q.options)) == len(q.options)
        and 10 <= len(q.prompt) <= 400
        and screen_output(" ".join([q.prompt, *q.options, q.explanation, q.hint])).action == "allow"
    )


def with_llm(db: Session, topic: Topic, difficulty: int, count: int, user_id: int, existing: list[str]) -> list[Question]:
    """Generate new questions with the configured LLM, grounded in retrieved material."""
    provider = llm.get_provider()
    if provider.is_demo:
        return []
    chunks = store.search(db, topic.title + " " + topic.summary, user_id=user_id, topic_id=topic.id, k=3)
    request = LLMRequest(
        task="quiz",
        system=prompts.SYSTEM_PROMPT,
        messages=prompts.build_quiz_messages(
            topic_title=topic.title, difficulty=DIFF_LABEL[difficulty], count=count, option_count=4,
            chunks=[c.__dict__ for c in chunks], avoid=existing,
        ),
        schema=GeneratedQuiz,
        context={"fallback_questions": []},
        max_tokens=1800,
    )
    result = llm.run(request)
    out: list[Question] = []
    for q in result.output.questions[:count]:  # type: ignore[attr-defined]
        if not _valid(q):
            continue
        obj = Question(topic_id=topic.id, prompt=q.prompt.strip(), options=[o.strip() for o in q.options],
                       correct_index=q.correct_index, explanation=q.explanation, hint=q.hint,
                       difficulty=difficulty, source="ai")
        db.add(obj)
        out.append(obj)
    db.flush()
    return out
