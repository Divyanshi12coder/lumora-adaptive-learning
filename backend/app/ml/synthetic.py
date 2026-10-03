"""SYNTHETIC learner simulator - clearly labelled, used only to bootstrap models.

Real interaction data does not exist on a fresh install, so the models are first
trained on simulated learners. The simulator follows an Item-Response-Theory-style
generative process with learning over time:

    P(correct) = guess + (1 - guess - slip) * sigmoid(1.7 * (ability_t - b_difficulty) + hint_boost)

Behaviour (hints, skips, response time, confidence, session drop-off) is generated
from latent traits so that features carry signal. Because the data comes from a
known process, metrics measured on it show the pipeline works end-to-end - they
are NOT evidence of real-world accuracy. Retrain on real data with
`python -m app.ml.train --source db` once enough interactions exist.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.ml.features import (
    EXPECTED_MS,
    PROFILE_FEATURES,
    AnswerRecord,
    SessionSnapshot,
    engagement_features,
    struggle_features,
    summarize_history,
)

DIFFICULTY_B = {1: -0.9, 2: 0.0, 3: 0.9}


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


@dataclass
class SyntheticLearner:
    ability: float
    learn_rate: float
    hint_propensity: float
    speed: float  # >1 slower
    persistence: float  # engagement trait
    caution: float  # tendency to change answers / report low confidence


def _make_learner(rng: np.random.Generator) -> SyntheticLearner:
    return SyntheticLearner(
        ability=float(rng.normal(0, 1)),
        learn_rate=float(rng.uniform(0.01, 0.06)),
        hint_propensity=float(rng.beta(2, 4)),
        speed=float(rng.lognormal(0, 0.3)),
        persistence=float(rng.beta(4, 2)),
        caution=float(rng.beta(2, 3)),
    )


def _simulate_answer(rng: np.random.Generator, lr: SyntheticLearner, t: int, difficulty: int, qid: int) -> AnswerRecord:
    ability_t = lr.ability + lr.learn_rate * t
    gap = ability_t - DIFFICULTY_B[difficulty]
    p_base = _sigmoid(1.7 * gap)
    struggling = p_base < 0.5
    hints = int(rng.random() < lr.hint_propensity * (1.6 if struggling else 0.6))
    if hints and rng.random() < 0.3:
        hints += 1
    p_skip = 0.03 + (0.12 if struggling else 0.0) * (1 - lr.persistence)
    skipped = rng.random() < p_skip
    guess, slip = 0.25, 0.08
    p_correct = guess + (1 - guess - slip) * _sigmoid(1.7 * gap + 0.45 * hints)
    correct = (not skipped) and rng.random() < p_correct
    ratio = lr.speed * (1.0 + 0.8 * (1 - p_base)) * float(rng.lognormal(0, 0.25))
    response_ms = int(EXPECTED_MS[difficulty] * (0.3 if skipped else ratio))
    changes = int(rng.random() < lr.caution * (0.8 if struggling else 0.3))
    if p_base < 0.35:
        confidence = 1 if rng.random() < 0.6 else 2
    elif p_base > 0.75:
        confidence = 3 if rng.random() < 0.7 else 2
    else:
        confidence = int(rng.integers(1, 4))
    return AnswerRecord(
        correct=bool(correct),
        skipped=bool(skipped),
        difficulty=difficulty,
        response_ms=response_ms,
        hints=hints,
        changes=changes,
        confidence=confidence,
        option_count=4,
        question_id=qid,
    )


def generate_struggle_dataset(n_learners: int = 400, seed: int = 7) -> pd.DataFrame:
    """One row per answer: features computed from history *before* the answer."""
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    for learner_id in range(n_learners):
        lr = _make_learner(rng)
        history: list[AnswerRecord] = []
        n_answers = int(rng.integers(12, 40))
        for t in range(n_answers):
            # An adaptive-ish curriculum: harder questions once things go well.
            summary = summarize_history(history)
            if summary.attempts >= 3 and summary.mastery > 0.7:
                difficulty = int(rng.choice([2, 3], p=[0.4, 0.6]))
            elif summary.attempts >= 3 and summary.mastery < 0.35:
                difficulty = int(rng.choice([1, 2], p=[0.7, 0.3]))
            else:
                difficulty = int(rng.integers(1, 4))
            feats = struggle_features(summary, difficulty)
            ans = _simulate_answer(rng, lr, t, difficulty, qid=int(rng.integers(0, 25)))
            feats["label_incorrect"] = int(not ans.correct)
            feats["learner_id"] = learner_id
            rows.append(feats)
            history.append(ans)
    return pd.DataFrame(rows)


def generate_engagement_dataset(n_learners: int = 400, seed: int = 11) -> pd.DataFrame:
    """One row per in-session checkpoint; label = learner keeps going >= 5 more minutes."""
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    for learner_id in range(n_learners):
        lr = _make_learner(rng)
        for _session in range(int(rng.integers(2, 6))):
            minute = 0.0
            events = 0
            outcomes: list[bool] = []
            hints: list[int] = []
            skips: list[bool] = []
            snapshots: list[tuple[float, dict]] = []
            alive = True
            t = 0
            while alive and minute < 60:
                step = float(rng.exponential(0.8 * lr.speed))
                minute += step
                ans = _simulate_answer(rng, lr, t, int(rng.integers(1, 4)), qid=t)
                t += 1
                events += 2 + ans.hints
                outcomes.append(ans.correct)
                hints.append(ans.hints)
                skips.append(ans.skipped)
                recent = outcomes[-6:]
                streak = 0
                for o in reversed(outcomes):
                    if o:
                        break
                    streak += 1
                snap = SessionSnapshot(
                    session_minutes=minute,
                    event_count=events,
                    recent_accuracy=sum(recent) / len(recent),
                    hint_rate=sum(hints[-6:]) / len(recent),
                    skip_rate=sum(skips[-6:]) / len(recent),
                    mistake_streak=streak,
                    idle_seconds=step * 60 * 0.4,
                )
                snapshots.append((minute, engagement_features(snap)))
                # Drop-off hazard rises with fatigue, frustration and low persistence.
                hazard = (
                    0.015
                    + 0.0025 * minute
                    + 0.05 * streak
                    + 0.06 * (1 - snap.recent_accuracy)
                    + 0.04 * snap.skip_rate
                ) * (1.6 - lr.persistence)
                if rng.random() < hazard:
                    alive = False
            end = minute
            for at, feats in snapshots:
                feats = dict(feats)
                feats["label_engaged"] = int(end - at >= 5.0)
                feats["learner_id"] = learner_id
                rows.append(feats)
    return pd.DataFrame(rows)


def generate_profile_dataset(n_learners: int = 600, seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n_learners):
        lr = _make_learner(rng)
        answers = [_simulate_answer(rng, lr, t, int(rng.integers(1, 4)), t) for t in range(25)]
        rows.append(
            {
                "accuracy": sum(a.correct for a in answers) / len(answers),
                "hint_rate": sum(a.hints for a in answers) / len(answers),
                "avg_response_ratio": float(np.mean([min(a.response_ratio, 4) for a in answers])),
                "skip_rate": sum(a.skipped for a in answers) / len(answers),
                "avg_session_minutes": float(np.clip(rng.normal(8 + 14 * lr.persistence, 4), 2, 45)),
            }
        )
    return pd.DataFrame(rows, columns=PROFILE_FEATURES)
