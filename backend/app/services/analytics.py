"""Learning analytics for the grown-up "Insights" view.

Everything here is computed from the learner's own stored interactions. The
technical ML/engine detail lives here, not on the child's dashboard.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.adaptive.engine import decide_strategy
from app.ml.real_data import user_profile_features
from app.ml.registry import registry
from app.ml.train import PROFILE_NAMES
from app.models import (
    AdaptiveStrategyRecord,
    AIConversation,
    AIMessage,
    Answer,
    InteractionEvent,
    LearningSession,
    MasteryHistory,
    MasteryScore,
    ModelPrediction,
    Question,
    QuizAttempt,
    Topic,
    User,
)
from app.services.learner_state import answer_history, build_state, preferences_input


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _days(n: int, now: datetime) -> list[str]:
    start = (now - timedelta(days=n - 1)).date()
    return [(start + timedelta(days=i)).isoformat() for i in range(n)]


def build(db: Session, user: User, days: int = 30) -> dict:
    now = datetime.now(UTC)
    since = now - timedelta(days=days)
    day_keys = _days(days, now)
    topic_titles = dict(db.execute(select(Topic.id, Topic.title)).all())

    # --- accuracy per day ---------------------------------------------------
    acc: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for created, ok in db.execute(select(Answer.created_at, Answer.is_correct)
                                  .where(Answer.user_id == user.id, Answer.created_at >= since)).all():
        k = _aware(created).date().isoformat()
        acc[k][0] += int(ok)
        acc[k][1] += 1
    accuracy_trend = [{"date": d, "accuracy": round(acc[d][0] / acc[d][1], 3) if acc[d][1] else None,
                       "answered": acc[d][1]} for d in day_keys]

    # --- engagement per day -------------------------------------------------
    minutes: dict[str, float] = defaultdict(float)
    sessions: dict[str, int] = defaultdict(int)
    for s in db.scalars(select(LearningSession).where(LearningSession.user_id == user.id,
                                                      LearningSession.started_at >= since)).all():
        k = _aware(s.started_at).date().isoformat()
        end = _aware(s.ended_at or s.last_activity_at)
        minutes[k] += max(0.0, (end - _aware(s.started_at)).total_seconds() / 60)
        sessions[k] += 1
    events: dict[str, int] = defaultdict(int)
    for (created,) in db.execute(select(InteractionEvent.created_at).where(
            InteractionEvent.user_id == user.id, InteractionEvent.created_at >= since)).all():
        events[_aware(created).date().isoformat()] += 1
    engagement_trend = [{"date": d, "minutes": round(minutes[d], 1), "sessions": sessions[d], "events": events[d]}
                        for d in day_keys]

    # --- mastery over time (carry-forward average of practised topics) ------
    hist = db.scalars(select(MasteryHistory).where(MasteryHistory.user_id == user.id)
                      .order_by(MasteryHistory.recorded_at)).all()
    latest: dict[int, float] = {}
    mastery_trend = []
    i = 0
    for d in day_keys:
        while i < len(hist) and _aware(hist[i].recorded_at).date().isoformat() <= d:
            latest[hist[i].topic_id] = hist[i].p_mastery
            i += 1
        mastery_trend.append({"date": d, "average_mastery": round(sum(latest.values()) / len(latest), 3) if latest else None,
                              **{f"t{tid}": round(p, 3) for tid, p in latest.items()}})

    # --- per-topic performance ---------------------------------------------
    perf = []
    rows = db.execute(
        select(QuizAttempt.topic_id, func.count(Answer.id), func.sum(case((Answer.is_correct.is_(True), 1), else_=0)),
               func.avg(Answer.response_ms), func.avg(Answer.hints_used), func.sum(case((Answer.skipped.is_(True), 1), else_=0)))
        .join(QuizAttempt, QuizAttempt.id == Answer.attempt_id)
        .where(Answer.user_id == user.id)
        .group_by(QuizAttempt.topic_id)
    ).all()
    masteries = {m.topic_id: m for m in db.scalars(select(MasteryScore).where(MasteryScore.user_id == user.id))}
    for topic_id, n, n_ok, avg_ms, avg_hints, n_skip in rows:
        m = masteries.get(topic_id)
        perf.append({
            "topic_id": topic_id, "topic": topic_titles.get(topic_id), "answered": n,
            "accuracy": round((n_ok or 0) / n, 3) if n else 0, "mastery": round(m.p_mastery, 3) if m else None,
            "avg_response_seconds": round((avg_ms or 0) / 1000, 1), "hints_per_question": round(float(avg_hints or 0), 2),
            "skip_rate": round((n_skip or 0) / n, 3) if n else 0,
        })
    perf.sort(key=lambda r: r["mastery"] or 0)

    # --- difficulty mix ------------------------------------------------------
    diff_rows = db.execute(
        select(Question.difficulty, func.count(Answer.id), func.sum(case((Answer.is_correct.is_(True), 1), else_=0)))
        .join(Question, Question.id == Answer.question_id).where(Answer.user_id == user.id).group_by(Question.difficulty)
    ).all()
    difficulty_mix = [{"difficulty": {1: "easy", 2: "medium", 3: "hard"}[d], "answered": n,
                       "accuracy": round((ok or 0) / n, 3) if n else 0} for d, n, ok in sorted(diff_rows)]

    # --- adaptive strategy history -------------------------------------------
    strategies = db.scalars(select(AdaptiveStrategyRecord).where(AdaptiveStrategyRecord.user_id == user.id)
                            .order_by(AdaptiveStrategyRecord.created_at.desc()).limit(25)).all()
    strategy_history = [
        {"at": s.created_at.isoformat(), "context": s.context, "topic": topic_titles.get(s.topic_id),
         "support_score": s.support_score, "band": s.strategy.get("band"), "difficulty": s.strategy.get("difficulty"),
         "explanation_style": s.strategy.get("explanation_style")}
        for s in reversed(strategies)
    ]

    # --- ML insight ------------------------------------------------------------
    state = build_state(db, user, None)
    current = decide_strategy(state.signals, preferences_input(user))
    history = answer_history(db, user.id, None, limit=200)
    if len(history) >= 10:
        profile_pred = registry.assign_profile(user_profile_features(db, user.id, history))
        name, desc = PROFILE_NAMES[profile_pred.label]
        profile = {"key": profile_pred.label, "name": name, "description": desc, "confidence": profile_pred.value,
                   "source": profile_pred.source, "version": profile_pred.version}
        if user.profile and user.profile.learner_cluster != profile_pred.label:
            user.profile.learner_cluster = profile_pred.label
            db.commit()
    else:
        profile = None
    pred_rows = db.scalars(select(ModelPrediction).where(ModelPrediction.user_id == user.id)
                           .order_by(ModelPrediction.created_at.desc()).limit(40)).all()
    struggle_series = [{"at": p.created_at.isoformat(), "value": p.prediction}
                       for p in reversed(pred_rows) if p.model_name.startswith("struggle")]
    metrics = registry.metrics() or {}

    safety_count = db.scalar(
        select(func.count(AIMessage.id)).join(AIConversation, AIConversation.id == AIMessage.conversation_id)
        .where(AIConversation.user_id == user.id, AIMessage.intent == "safety")
    ) or 0
    total_minutes = sum(minutes.values())
    answered = sum(v[1] for v in acc.values())
    return {
        "period_days": days,
        "summary": {
            "sessions": sum(sessions.values()),
            "minutes": round(total_minutes, 1),
            "questions_answered": answered,
            "accuracy": round(sum(v[0] for v in acc.values()) / answered, 3) if answered else None,
            "topics_practiced": len(masteries),
            "average_mastery": round(sum(m.p_mastery for m in masteries.values()) / len(masteries), 3) if masteries else None,
            "hint_rate": round(state.signals.hint_rate, 2),
            "trend": state.trend_direction,
        },
        "accuracy_trend": accuracy_trend,
        "engagement_trend": engagement_trend,
        "mastery_trend": mastery_trend,
        "mastery_topics": {f"t{tid}": topic_titles.get(tid) for tid in masteries},
        "topic_performance": perf,
        "difficulty_mix": difficulty_mix,
        "strategy_history": strategy_history,
        "current_strategy": current.model_dump(),
        "ml": {
            "struggle_probability": round(state.struggle.value, 3),
            "struggle_source": state.struggle.source,
            "struggle_version": state.struggle.version,
            "engagement_probability": round(state.engagement.value, 3),
            "engagement_source": state.engagement.source,
            "struggle_series": struggle_series,
            "learner_profile": profile,
            "model_card": {
                "data_provenance": metrics.get("data_provenance"),
                "note": metrics.get("note"),
                "struggle_roc_auc": (metrics.get("struggle_model") or {}).get("roc_auc"),
                "engagement_roc_auc": (metrics.get("engagement_model") or {}).get("roc_auc"),
                "trained_at": metrics.get("trained_at"),
            },
        },
        "safety": {"redirected_or_supported_messages": safety_count},
    }
