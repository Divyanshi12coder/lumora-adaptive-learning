from app.adaptive.engine import (
    COLD_START_PRIOR,
    FULL_CONFIDENCE_ATTEMPTS,
    LearnerPreferenceInput,
    LearnerSignals,
    decide_strategy,
    signals_for_level,
)


def struggling() -> LearnerSignals:
    return LearnerSignals(recent_accuracy=0.2, historical_accuracy=0.3, mastery=0.1, attempts=20,
                          avg_response_ratio=2.2, hint_rate=1.0, skip_rate=0.2, mistake_streak=3,
                          repeated_mistakes=2, low_confidence_rate=0.7, trend_slope=-0.02,
                          struggle_probability=0.85, engagement_probability=0.6)


def mastered() -> LearnerSignals:
    return LearnerSignals(recent_accuracy=0.95, historical_accuracy=0.9, mastery=0.95, attempts=30,
                          avg_response_ratio=0.8, hint_rate=0.0, skip_rate=0.0, mistake_streak=0,
                          trend_slope=0.03, struggle_probability=0.08, engagement_probability=0.9)


def test_struggling_learner_gets_more_support():
    s = decide_strategy(struggling())
    assert s.band == "high_support"
    assert s.difficulty == "easy"
    assert s.explanation_style == "step_by_step"
    assert s.hint_level == "full"
    assert s.option_count == 3  # fewer answer choices lowers cognitive load
    assert s.review_required is True
    assert s.tone == "gentle"


def test_mastered_learner_gets_challenge():
    s = decide_strategy(mastered())
    assert s.band == "stretch"
    assert s.difficulty == "hard"
    assert s.explanation_style == "concise"
    assert s.hint_level == "none"
    assert s.option_count == 4


def test_support_decreases_monotonically_with_level():
    scores = [decide_strategy(signals_for_level(level)).support_score for level in range(0, 101, 10)]
    assert all(a >= b for a, b in zip(scores, scores[1:], strict=False)), scores
    assert scores[0] - scores[-1] > 0.5


def test_cold_start_uses_supportive_prior():
    s = decide_strategy(LearnerSignals(attempts=0))
    assert s.data_confidence == 0
    assert abs(s.support_score - COLD_START_PRIOR) < 0.01
    assert any("few answers" in r for r in s.rationale)


def test_confidence_ramps_with_attempts():
    s = decide_strategy(LearnerSignals(attempts=FULL_CONFIDENCE_ATTEMPTS // 2, recent_accuracy=1, mastery=0.9))
    assert 0.4 < s.data_confidence < 0.6


def test_missing_ml_prediction_renormalises_weights():
    sig = struggling()
    sig.struggle_probability = None
    s = decide_strategy(sig)
    assert "ml_struggle" not in {f.family for f in s.factors}
    assert abs(sum(f.weight for f in s.factors) - 1.0) < 0.01


def test_short_preference_and_feedback_reduce_density():
    sig = signals_for_level(50)
    detailed = decide_strategy(sig, LearnerPreferenceInput(explanation_length="detailed"))
    short = decide_strategy(sig, LearnerPreferenceInput(explanation_length="short", length_bias=1.0))
    order = ["low", "medium", "high"]
    assert order.index(short.content_density) < order.index(detailed.content_density)


def test_too_hard_feedback_increases_support():
    sig = signals_for_level(60)
    base = decide_strategy(sig)
    harder = decide_strategy(sig, LearnerPreferenceInput(difficulty_bias=1.0))
    assert harder.support_score > base.support_score


def test_low_engagement_suggests_break_and_shorter_quiz():
    sig = signals_for_level(70)
    sig.engagement_probability = 0.2
    s = decide_strategy(sig)
    assert s.suggest_break is True
    assert s.question_count == 4


def test_long_gap_triggers_review():
    sig = signals_for_level(70)
    sig.days_since_practice = 10
    assert decide_strategy(sig).review_required is True


def test_strategy_is_deterministic_and_explained():
    a, b = decide_strategy(struggling()), decide_strategy(struggling())
    assert a == b
    assert a.rationale and a.learner_message
    assert {f.family for f in a.factors} >= {"performance", "mastery", "behaviour", "momentum"}
