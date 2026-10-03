"""Offline demo provider - no API key required.

It does not pretend to be an LLM. It builds deterministic, *grounded* answers
by extracting the most relevant sentences from the retrieved RAG passages and
the structured lesson, then shaping them with the same teaching strategy a real
model receives. Every response is flagged `is_demo=True` and labelled in the UI.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

from app.ai.providers.base import LLMProvider, LLMRequest
from app.ai.schemas import DocumentSummary, GeneratedQuestion, GeneratedQuiz, StudyPlan, StudyPlanItem, TutorReply
from app.rag.embeddings import tokenize

SENTENCE = re.compile(r"(?<=[.!?])\s+")

ENCOURAGEMENT = {
    "gentle": "Take your time - every step you try helps your brain grow.",
    "warm": "Nice thinking! You're doing great.",
    "celebratory": "Brilliant work - you're really getting the hang of this!",
}


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE.split(text.replace("\n", " ")) if len(s.strip()) > 12]


def _rank_sentences(query: str, chunks: list[dict], limit: int) -> tuple[list[str], list[int]]:
    q = set(tokenize(query))
    scored: list[tuple[float, int, int, str]] = []
    for ci, chunk in enumerate(chunks):
        for si, sent in enumerate(_sentences(chunk["text"])):
            toks = set(tokenize(sent))
            overlap = len(q & toks) / (1 + len(q)) if q else 0
            # earlier chunks are more relevant (already ranked by retrieval)
            scored.append((overlap + 0.15 / (1 + ci) + 0.02 / (1 + si), ci, si, sent))
    top = sorted(scored, key=lambda x: x[0], reverse=True)[:limit]
    top.sort(key=lambda x: (x[1], x[2]))  # keep reading order
    return [t[3] for t in top], sorted({t[1] + 1 for t in top})


class DemoProvider(LLMProvider):
    name = "demo"
    model = "lumora-demo-1"
    is_demo = True

    def generate(self, request: LLMRequest) -> BaseModel:
        if request.task == "tutor":
            return self._tutor(request.context)
        if request.task == "quiz":
            return self._quiz(request.context)
        if request.task == "summary":
            return self._summary(request.context)
        if request.task == "study_plan":
            return self._plan(request.context)
        raise ValueError(f"Demo provider does not support task {request.task!r}")

    # ------------------------------------------------------------------
    def _tutor(self, ctx: dict) -> TutorReply:
        strategy = ctx["strategy"]
        intent = ctx.get("intent", "general")
        lesson = ctx.get("lesson") or {}
        chunks = ctx.get("chunks") or []
        topic = ctx.get("topic_title") or "this topic"
        style = strategy["explanation_style"]
        density = strategy["content_density"]
        n_examples = strategy["example_count"]
        tone = strategy["tone"]
        query = f"{ctx.get('learner_message', '')} {topic}"

        sentence_budget = {"low": 2, "medium": 3, "high": 5}[density]
        picked, used = _rank_sentences(query, chunks, sentence_budget + 2)
        examples = list(lesson.get("examples") or [])[:n_examples]
        steps_src = list(lesson.get("steps") or [])
        key_idea = lesson.get("key_idea") or (picked[0] if picked else "")
        practice = ctx.get("practice_question")
        follow = ["Give me an easier example", "Quiz me", "Explain it differently"]

        if not chunks and not lesson:
            return TutorReply(
                message=(
                    "I couldn't find that in your learning materials yet. Try picking a topic first, or ask me about "
                    "maths, science, reading or history - I'd love to help!"
                ),
                steps=[], examples=[], check_question=None, encouragement=ENCOURAGEMENT["warm"],
                follow_ups=["What can I learn today?", "Quiz me"], used_source_numbers=[],
            )

        if intent == "hint":
            hint = (practice or {}).get("hint") or (steps_src[0] if steps_src else key_idea)
            return TutorReply(
                message=f"Here's a clue that might help: {hint}",
                steps=steps_src[:1] if strategy["hint_level"] in ("guided", "full") else [],
                examples=[], check_question=(practice or {}).get("prompt"),
                encouragement="You're so close - give it another go!",
                follow_ups=["Give me another hint", "Explain the idea", "Show me an example"],
                used_source_numbers=used[:1],
            )

        if intent == "quiz":
            q = practice or {}
            opts = q.get("options") or []
            letters = "ABCD"
            question = q.get("prompt", f"What is the most important idea about {topic}?")
            if opts:
                question += "  " + "  ".join(f"{letters[i]}) {o}" for i, o in enumerate(opts))
            return TutorReply(
                message="Let's see what you remember! Have a think, then answer in the quiz or tell me your choice.",
                steps=[], examples=[], check_question=question, encouragement=ENCOURAGEMENT[tone],
                follow_ups=["Give me a hint", "Start a full quiz", "Explain the idea first"],
                used_source_numbers=[],
            )

        if intent in ("easier", "confused"):
            opener = (
                "No worries at all - lots of people find this tricky at first. Let's go slowly."
                if intent == "confused" else "Let's make it simpler."
            )
            analogy = lesson.get("analogy")
            message = f"{opener} {key_idea}" + (f" Think of it like this: {analogy}" if analogy else "")
            return TutorReply(
                message=message,
                steps=steps_src[:3],
                examples=examples[:max(1, min(2, n_examples))],
                check_question=(practice or {}).get("prompt"),
                encouragement=ENCOURAGEMENT["gentle"],
                follow_ups=["Give me a hint", "Quiz me", "Explain it differently"],
                used_source_numbers=used[:2],
            )

        if intent == "different":
            analogy = lesson.get("analogy") or key_idea
            fun = lesson.get("fun_fact")
            return TutorReply(
                message=f"Here's another way to picture it: {analogy}" + (f" Fun fact: {fun}" if fun else ""),
                steps=[], examples=examples[-max(1, n_examples):],
                check_question=None, encouragement=ENCOURAGEMENT[tone],
                follow_ups=follow, used_source_numbers=used[:2],
            )

        # explain / general
        body = " ".join(picked[:sentence_budget]) or key_idea
        if style == "step_by_step":
            steps = steps_src[:5] or picked[:4]
            message = f"Let's learn about {topic} one step at a time. {key_idea}"
        elif style == "worked_example":
            steps = steps_src[:4]
            message = f"{body}"
        elif style == "guided_discovery":
            steps = steps_src[:2]
            message = f"{body} What do you notice? Try the first step yourself before peeking at the next one."
        else:  # concise
            steps = []
            message = " ".join(picked[:2]) or key_idea
            follow = ["Give me a challenge question", "Quiz me", "Tell me a fun fact"]
        return TutorReply(
            message=message,
            steps=steps,
            examples=examples,
            check_question=(practice or {}).get("prompt") if style != "concise" else None,
            encouragement=ENCOURAGEMENT[tone],
            follow_ups=follow,
            used_source_numbers=used,
        )

    def _quiz(self, ctx: dict) -> GeneratedQuiz:
        """Demo mode only uses curated / procedurally generated questions (see quiz service)."""
        bank = ctx.get("fallback_questions") or []
        return GeneratedQuiz(questions=[GeneratedQuestion(**q) for q in bank])

    def _summary(self, ctx: dict) -> DocumentSummary:
        text = ctx.get("text", "")
        sents = _sentences(text)
        q = " ".join(sents[:3])
        picked, _ = _rank_sentences(q, [{"text": text}], 5)
        return DocumentSummary(summary=" ".join(sents[:3])[:600], key_points=picked[:5])

    def _plan(self, ctx: dict) -> StudyPlan:
        topics = ctx.get("topics") or ["Review your favourite topic"]
        minutes = int(ctx.get("minutes", 15))
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][: int(ctx.get("days", 5))]
        activities = ["Read the lesson and try 3 practice questions", "Ask Divi to explain one tricky part",
                      "Take a short quiz", "Review mistakes with hints", "Teach it back to a grown-up"]
        items = [
            StudyPlanItem(day=d, focus=topics[i % len(topics)], activity=activities[i % len(activities)], minutes=minutes)
            for i, d in enumerate(days)
        ]
        return StudyPlan(title="Your gentle study plan", items=items,
                         note="Rest days are part of learning too. Skip a day whenever you need - no pressure!")
