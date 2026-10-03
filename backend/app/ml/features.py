"""Feature engineering shared by production inference, real-data training and the
synthetic simulator. Keeping a single implementation avoids train/serve skew.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.ml.bkt import DEFAULT_PARAMS, update_mastery
from app.ml.trend import accuracy_trend

EXPECTED_MS = {1: 20_000, 2: 30_000, 3: 42_000}


@dataclass
class AnswerRecord:
    correct: bool
    skipped: bool
    difficulty: int
    response_ms: int
    hints: int = 0
    changes: int = 0
    confidence: int | None = None  # 1 unsure .. 3 sure
    option_count: int = 4
    question_id: int | None = None

    @property
    def response_ratio(self) -> float:
        return self.response_ms / EXPECTED_MS.get(self.difficulty, 30_000)


@dataclass
class HistorySummary:
    attempts: int
    recent_accuracy: float | None
    historical_accuracy: float | None
    mastery: float
    hint_rate: float
    skip_rate: float
    mistake_streak: int
    repeated_mistakes: int
    avg_response_ratio: float
    answer_change_rate: float
    low_confidence_rate: float
    trend_slope: float
    trend_direction: str


def summarize_history(history: list[AnswerRecord], recent_window: int = 10) -> HistorySummary:
    if not history:
        return HistorySummary(0, None, None, DEFAULT_PARAMS.p_init, 0, 0, 0, 0, 1.0, 0, 0, 0.0, "not_enough_data")

    p = DEFAULT_PARAMS.p_init
    for r in history:
        if not r.skipped:
            p = update_mastery(p, r.correct, option_count=r.option_count, hints_used=r.hints)
        else:
            p = update_mastery(p, False, option_count=r.option_count)  # a skip is weak negative evidence

    recent = history[-recent_window:]
    outcomes = [r.correct and not r.skipped for r in history]
    streak = 0
    for r in reversed(history):
        if r.correct and not r.skipped:
            break
        streak += 1

    wrong_by_q: dict[int, int] = {}
    for r in history:
        if r.question_id is not None and not r.correct:
            wrong_by_q[r.question_id] = wrong_by_q.get(r.question_id, 0) + 1
    repeated = sum(1 for c in wrong_by_q.values() if c >= 2)

    conf = [r.confidence for r in recent if r.confidence is not None]
    trend = accuracy_trend(outcomes)
    return HistorySummary(
        attempts=len(history),
        recent_accuracy=sum(r.correct and not r.skipped for r in recent) / len(recent),
        historical_accuracy=sum(outcomes) / len(outcomes),
        mastery=p,
        hint_rate=sum(r.hints for r in recent) / len(recent),
        skip_rate=sum(r.skipped for r in recent) / len(recent),
        mistake_streak=streak,
        repeated_mistakes=repeated,
        avg_response_ratio=sum(min(r.response_ratio, 4.0) for r in recent) / len(recent),
        answer_change_rate=sum(min(r.changes, 3) for r in recent) / (3 * len(recent)),
        low_confidence_rate=(sum(1 for c in conf if c == 1) / len(conf)) if conf else 0.0,
        trend_slope=trend.slope,
        trend_direction=trend.direction,
    )


# ---------------------------------------------------------------------------
# Struggle model ("will the next answer be incorrect?")
# ---------------------------------------------------------------------------
STRUGGLE_FEATURES = [
    "mastery",
    "recent_accuracy",
    "hint_rate",
    "skip_rate",
    "mistake_streak",
    "avg_response_ratio",
    "low_confidence_rate",
    "next_difficulty",
    "log_attempts",
]


def struggle_features(summary: HistorySummary, next_difficulty: int) -> dict[str, float]:
    return {
        "mastery": summary.mastery,
        "recent_accuracy": summary.recent_accuracy if summary.recent_accuracy is not None else 0.5,
        "hint_rate": min(summary.hint_rate, 3.0),
        "skip_rate": summary.skip_rate,
        "mistake_streak": float(min(summary.mistake_streak, 6)),
        "avg_response_ratio": min(summary.avg_response_ratio, 4.0),
        "low_confidence_rate": summary.low_confidence_rate,
        "next_difficulty": float(next_difficulty),
        "log_attempts": math.log1p(summary.attempts),
    }


# ---------------------------------------------------------------------------
# Engagement model ("will the learner keep going for the next few minutes?")
# ---------------------------------------------------------------------------
ENGAGEMENT_FEATURES = [
    "session_minutes",
    "events_per_minute",
    "recent_accuracy",
    "hint_rate",
    "skip_rate",
    "mistake_streak",
    "idle_seconds",
]


@dataclass
class SessionSnapshot:
    session_minutes: float
    event_count: int
    recent_accuracy: float
    hint_rate: float
    skip_rate: float
    mistake_streak: int
    idle_seconds: float


def engagement_features(snap: SessionSnapshot) -> dict[str, float]:
    minutes = max(snap.session_minutes, 0.5)
    return {
        "session_minutes": min(snap.session_minutes, 90.0),
        "events_per_minute": min(snap.event_count / minutes, 20.0),
        "recent_accuracy": snap.recent_accuracy,
        "hint_rate": min(snap.hint_rate, 3.0),
        "skip_rate": snap.skip_rate,
        "mistake_streak": float(min(snap.mistake_streak, 6)),
        "idle_seconds": min(snap.idle_seconds, 900.0),
    }


# ---------------------------------------------------------------------------
# Learner-profile clustering (behavioural, descriptive only)
# ---------------------------------------------------------------------------
PROFILE_FEATURES = ["accuracy", "hint_rate", "avg_response_ratio", "skip_rate", "avg_session_minutes"]
