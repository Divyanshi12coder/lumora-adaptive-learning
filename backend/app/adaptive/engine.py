"""Lumora Adaptive Teaching Engine.

A pure, deterministic domain service: it receives a snapshot of learner signals
(behaviour, performance, mastery, ML predictions, preferences) and returns a
`TeachingStrategy` plus an explanation of *why*.

Design
------
1.  Each signal family is converted into a "support need" in [0, 1]
    (0 = ready for challenge, 1 = needs a lot of guidance).
2.  Families are combined with documented weights into a single `support_score`.
    Missing families (e.g. no ML prediction yet) are dropped and the remaining
    weights re-normalised - so the engine degrades gracefully.
3.  The score is shrunk toward a gently-supportive prior when we have little data
    (cold start), then nudged by feedback-derived preference biases.
4.  A policy maps the score + preferences to concrete presentation decisions.

The engine never infers or labels medical conditions. It only reasons about
observable learning behaviour and stated preferences.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

ENGINE_VERSION = "1.2.0"

# Weights for each signal family. Sum = 1.0. Kept explicit for interpretability.
FAMILY_WEIGHTS: dict[str, float] = {
    "performance": 0.30,
    "mastery": 0.25,
    "ml_struggle": 0.20,
    "behaviour": 0.15,
    "momentum": 0.10,
}

COLD_START_PRIOR = 0.58  # new learners start with slightly more scaffolding
FULL_CONFIDENCE_ATTEMPTS = 12

Difficulty = Literal["easy", "medium", "hard"]
ExplanationStyle = Literal["step_by_step", "worked_example", "guided_discovery", "concise"]
Level = Literal["low", "medium", "high"]
HintLevel = Literal["none", "light", "guided", "full"]
Pacing = Literal["slow", "steady", "brisk"]


@dataclass
class LearnerSignals:
    """Observable signals. Every field is optional-friendly so cold start works."""

    recent_accuracy: float | None = None  # last ~10 answers, 0..1
    historical_accuracy: float | None = None  # all answers on this topic, 0..1
    mastery: float = 0.2  # Bayesian Knowledge Tracing P(known)
    attempts: int = 0  # answers recorded for this topic
    avg_response_ratio: float = 1.0  # response time / expected time for the difficulty
    hint_rate: float = 0.0  # hints per question (recent)
    skip_rate: float = 0.0
    mistake_streak: int = 0  # consecutive incorrect answers
    repeated_mistakes: int = 0  # questions answered wrong more than once
    answer_change_rate: float = 0.0
    low_confidence_rate: float = 0.0  # share of answers marked "not sure"
    explanation_requests: int = 0  # recent "explain again" requests
    session_minutes: float = 0.0
    days_since_practice: float | None = None
    trend_slope: float = 0.0  # accuracy change per attempt (from trend model)
    struggle_probability: float | None = None  # ML: P(next answer incorrect)
    engagement_probability: float | None = None  # ML: P(learner stays engaged)


@dataclass
class LearnerPreferenceInput:
    explanation_length: Literal["short", "medium", "detailed"] = "medium"
    prefers_visuals: bool = True
    prefers_examples: bool = True
    pace: Literal["relaxed", "steady", "quick"] = "steady"
    length_bias: float = 0.0  # >0 learner said "too long" -> shorter
    difficulty_bias: float = 0.0  # >0 learner said "too hard" -> more support
    read_aloud: bool = False


class FactorContribution(BaseModel):
    family: str
    need: float = Field(ge=0, le=1)
    weight: float
    note: str


class TeachingStrategy(BaseModel):
    difficulty: Difficulty
    explanation_style: ExplanationStyle
    content_density: Level
    hint_level: HintLevel
    example_count: int = Field(ge=0, le=4)
    review_required: bool
    pacing: Pacing
    visual_support: Level
    option_count: int = Field(ge=2, le=4, description="answer choices per question")
    question_count: int = Field(ge=3, le=8)
    suggest_break: bool
    read_aloud_suggested: bool
    tone: Literal["gentle", "warm", "celebratory"]
    support_score: float = Field(ge=0, le=1)
    data_confidence: float = Field(ge=0, le=1)
    band: Literal["high_support", "guided", "balanced", "stretch"]
    rationale: list[str]
    learner_message: str
    factors: list[FactorContribution]
    engine_version: str = ENGINE_VERSION


@dataclass
class _Scored:
    support: float
    confidence: float
    factors: list[FactorContribution] = field(default_factory=list)


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _score(signals: LearnerSignals, prefs: LearnerPreferenceInput) -> _Scored:
    needs: dict[str, tuple[float, str]] = {}

    # Performance: recency-weighted accuracy.
    if signals.recent_accuracy is not None or signals.historical_accuracy is not None:
        recent = signals.recent_accuracy if signals.recent_accuracy is not None else signals.historical_accuracy
        hist = signals.historical_accuracy if signals.historical_accuracy is not None else recent
        acc = 0.65 * float(recent) + 0.35 * float(hist)
        needs["performance"] = (1 - acc, f"recent accuracy {recent:.0%}, overall {hist:.0%}")

    needs["mastery"] = (1 - _clip(signals.mastery), f"estimated mastery {signals.mastery:.0%}")

    if signals.struggle_probability is not None:
        needs["ml_struggle"] = (
            _clip(signals.struggle_probability),
            f"model predicts {signals.struggle_probability:.0%} chance the next question is tricky",
        )

    slow = _clip((signals.avg_response_ratio - 1.0) / 1.5)
    behaviour = (
        0.25 * _clip(signals.hint_rate)
        + 0.20 * _clip(signals.mistake_streak / 3)
        + 0.15 * _clip(signals.skip_rate * 2)
        + 0.15 * slow
        + 0.10 * _clip(signals.low_confidence_rate)
        + 0.08 * _clip(signals.answer_change_rate)
        + 0.07 * _clip(signals.explanation_requests / 3)
    )
    needs["behaviour"] = (
        _clip(behaviour),
        f"hints {signals.hint_rate:.1f}/question, mistake streak {signals.mistake_streak}, "
        f"skips {signals.skip_rate:.0%}, pace x{signals.avg_response_ratio:.1f}",
    )

    # Momentum: a slope of +0.05 accuracy/attempt is strong improvement.
    needs["momentum"] = (_clip(0.5 - signals.trend_slope * 10), f"accuracy trend {signals.trend_slope:+.3f}/attempt")

    total_w = sum(FAMILY_WEIGHTS[k] for k in needs)
    factors = [
        FactorContribution(family=k, need=round(v, 3), weight=round(FAMILY_WEIGHTS[k] / total_w, 3), note=note)
        for k, (v, note) in needs.items()
    ]
    raw = sum(f.need * f.weight for f in factors)

    confidence = _clip(signals.attempts / FULL_CONFIDENCE_ATTEMPTS)
    support = confidence * raw + (1 - confidence) * COLD_START_PRIOR
    support += 0.12 * _clip(prefs.difficulty_bias, -1, 1)
    return _Scored(support=_clip(support), confidence=confidence, factors=factors)


def decide_strategy(signals: LearnerSignals, prefs: LearnerPreferenceInput | None = None) -> TeachingStrategy:
    prefs = prefs or LearnerPreferenceInput()
    scored = _score(signals, prefs)
    s = scored.support

    # --- band & difficulty ----------------------------------------------------
    if s >= 0.68:
        band, difficulty, style = "high_support", "easy", "step_by_step"
    elif s >= 0.52:
        band, difficulty, style = "guided", "easy" if signals.mastery < 0.35 else "medium", "worked_example"
    elif s >= 0.36:
        band, difficulty, style = "balanced", "medium", "guided_discovery"
    else:
        band, difficulty, style = "stretch", "hard", "concise"

    # --- density: support, stated preference and feedback all matter ---------
    density_score = 1 - s  # more support -> lighter pages
    density_score += {"short": -0.25, "medium": 0.0, "detailed": 0.2}[prefs.explanation_length]
    density_score -= 0.2 * _clip(prefs.length_bias, -1, 1)
    if signals.engagement_probability is not None and signals.engagement_probability < 0.4:
        density_score -= 0.2
    density: Level = "low" if density_score < 0.42 else ("medium" if density_score < 0.7 else "high")
    if density == "high" and prefs.explanation_length == "short":
        density = "medium"

    hint_level: HintLevel = "full" if s >= 0.72 else "guided" if s >= 0.52 else "light" if s >= 0.33 else "none"

    examples = 3 if s >= 0.68 else 2 if s >= 0.45 else 1
    if prefs.prefers_examples:
        examples = min(4, examples + 1)
    if density == "low":
        examples = min(examples, 2)

    review_required = (
        (signals.mastery < 0.4 and signals.attempts >= 4)
        or signals.repeated_mistakes >= 2
        or (signals.days_since_practice is not None and signals.days_since_practice > 7 and signals.mastery < 0.85)
    )

    if s >= 0.6 or prefs.pace == "relaxed":
        pacing: Pacing = "slow"
    elif s < 0.36 and prefs.pace == "quick" or s < 0.3:
        pacing = "brisk"
    else:
        pacing = "steady"

    visual: Level = "high" if (prefs.prefers_visuals or s >= 0.7) else ("medium" if s >= 0.4 else "low")

    option_count = 3 if s >= 0.68 else 4
    low_engagement = signals.engagement_probability is not None and signals.engagement_probability < 0.4
    question_count = 4 if (s >= 0.68 or low_engagement) else 6 if band == "stretch" else 5

    suggest_break = low_engagement or signals.session_minutes >= 25
    read_aloud = prefs.read_aloud or (signals.avg_response_ratio > 1.8 and s >= 0.6)

    if signals.mistake_streak >= 2 or s >= 0.68:
        tone = "gentle"
    elif signals.trend_slope > 0.02 or (signals.recent_accuracy or 0) >= 0.85:
        tone = "celebratory"
    else:
        tone = "warm"

    rationale = _rationale(signals, scored, band, review_required, suggest_break)
    return TeachingStrategy(
        difficulty=difficulty,
        explanation_style=style,
        content_density=density,
        hint_level=hint_level,
        example_count=examples,
        review_required=review_required,
        pacing=pacing,
        visual_support=visual,
        option_count=option_count,
        question_count=question_count,
        suggest_break=suggest_break,
        read_aloud_suggested=read_aloud,
        tone=tone,
        support_score=round(s, 3),
        data_confidence=round(scored.confidence, 3),
        band=band,
        rationale=rationale,
        learner_message=_learner_message(band, tone, review_required),
        factors=scored.factors,
    )


def _rationale(
    signals: LearnerSignals, scored: _Scored, band: str, review: bool, brk: bool
) -> list[str]:
    out: list[str] = []
    if scored.confidence < 0.35:
        out.append("Only a few answers so far, so we start with friendly scaffolding while we learn together.")
    top = sorted(scored.factors, key=lambda f: f.need * f.weight, reverse=True)[:2]
    for f in top:
        out.append(f"Main factor - {f.family.replace('_', ' ')}: {f.note}.")
    if review:
        out.append("A short review is scheduled because some ideas need another look.")
    if brk:
        out.append("A brain break is suggested to keep learning comfortable.")
    if band == "stretch":
        out.append("Strong, steady results - ready for a bigger challenge.")
    return out


def _learner_message(band: str, tone: str, review: bool) -> str:
    if band == "high_support":
        msg = "Let's take this one small step at a time. You've got this!"
    elif band == "guided":
        msg = "You're building great understanding. We'll practise with a few helpful examples."
    elif band == "balanced":
        msg = "You're getting really good at this! Let's try thinking it through together."
    else:
        msg = "Wow, you're ready for a little more challenge!"
    if review:
        msg += " We'll also do a quick review to keep ideas fresh."
    return msg


def signals_for_level(level: float) -> LearnerSignals:
    """Map a 0-100 "how is the learner doing" slider to plausible signals.

    Used by the public landing-page demo so visitors see the *real* engine react,
    without any personal data. 0 = struggling, 100 = mastered.
    """
    t = _clip(level / 100.0)
    return LearnerSignals(
        recent_accuracy=0.2 + 0.78 * t,
        historical_accuracy=0.3 + 0.6 * t,
        mastery=0.08 + 0.88 * t,
        attempts=FULL_CONFIDENCE_ATTEMPTS,
        avg_response_ratio=2.2 - 1.5 * t,
        hint_rate=_clip(1.2 - 1.3 * t),
        skip_rate=_clip(0.3 - 0.35 * t),
        mistake_streak=int(round(3 * (1 - t) ** 2)),
        repeated_mistakes=2 if t < 0.25 else 0,
        low_confidence_rate=_clip(0.7 - 0.8 * t),
        trend_slope=-0.02 + 0.05 * t,
        struggle_probability=_clip(0.85 - 0.8 * t),
        engagement_probability=0.55 + 0.4 * t,
        session_minutes=10,
        days_since_practice=1,
    )


def signals_to_dict(signals: LearnerSignals) -> dict:
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in asdict(signals).items()}
