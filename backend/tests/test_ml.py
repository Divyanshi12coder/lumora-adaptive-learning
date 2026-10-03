from app.ml import synthetic
from app.ml.bkt import update_mastery
from app.ml.features import STRUGGLE_FEATURES, AnswerRecord, summarize_history
from app.ml.registry import ModelRegistry
from app.ml.train import train_engagement, train_profiles, train_struggle
from app.ml.trend import accuracy_trend


def test_bkt_moves_in_the_right_direction():
    p = 0.3
    assert update_mastery(p, True) > p
    assert update_mastery(p, False) < p + 0.15  # only the learning transition can raise it


def test_bkt_hinted_success_is_weaker_evidence():
    assert update_mastery(0.3, True, hints_used=1) < update_mastery(0.3, True, hints_used=0)


def test_bkt_fewer_options_means_more_guessing():
    assert update_mastery(0.3, True, option_count=2) < update_mastery(0.3, True, option_count=4)


def test_trend_detection():
    assert accuracy_trend([False] * 5 + [True] * 7).direction == "improving"
    assert accuracy_trend([True] * 7 + [False] * 5).direction == "dipping"
    assert accuracy_trend([True, False]).direction == "not_enough_data"


def rec(correct, qid=None, hints=0, skipped=False):
    return AnswerRecord(correct=correct, skipped=skipped, difficulty=2, response_ms=30000, hints=hints, question_id=qid)


def test_summarize_history_features():
    hist = [rec(True, 1), rec(False, 2), rec(False, 2, hints=1), rec(False, 3), rec(False, 4, skipped=True)]
    s = summarize_history(hist)
    assert s.attempts == 5
    assert s.mistake_streak == 4
    assert s.repeated_mistakes == 1
    assert s.skip_rate == 0.2
    assert abs(s.recent_accuracy - 0.2) < 1e-9


def test_synthetic_datasets_have_expected_columns():
    df = synthetic.generate_struggle_dataset(n_learners=20)
    assert set(STRUGGLE_FEATURES) <= set(df.columns)
    assert df["label_incorrect"].nunique() == 2
    e = synthetic.generate_engagement_dataset(n_learners=20)
    assert e["label_engaged"].nunique() == 2


def test_struggle_model_beats_chance_on_held_out_learners():
    model, metrics = train_struggle(synthetic.generate_struggle_dataset(n_learners=150))
    assert metrics["roc_auc"] > 0.6
    assert metrics["brier"] < metrics["baseline_brier_constant_rate"]
    # interpretable direction: harder questions -> more likely to struggle
    assert metrics["standardized_coefficients"]["next_difficulty"] > 0


def test_engagement_model_selection_reports_candidates():
    _, metrics = train_engagement(synthetic.generate_engagement_dataset(n_learners=80))
    assert set(metrics["validation_roc_auc_by_candidate"]) == {"GradientBoostingClassifier", "LogisticRegression"}
    assert metrics["selected_by"] == "validation ROC-AUC"


def test_profile_clusters_get_unique_names():
    model, metrics = train_profiles(synthetic.generate_profile_dataset(n_learners=200))
    assert len(set(model["names"])) == 4
    assert -1 <= metrics["silhouette"] <= 1


def test_registry_falls_back_when_models_unavailable(tmp_path, monkeypatch):
    from app.ml import train as trainer

    def boom(*_a, **_k):
        raise RuntimeError("no training today")

    monkeypatch.setattr(trainer, "train_all", boom)
    reg = ModelRegistry(str(tmp_path / "missing"))
    feats = {f: 0.5 for f in STRUGGLE_FEATURES} | {"next_difficulty": 2.0}
    pred = reg.predict_struggle(feats)
    assert pred.source == "fallback"
    assert 0 < pred.value < 1


def test_procedural_questions_always_have_unique_options_and_a_valid_answer():
    import random

    from app.services.question_gen import GENERATORS

    for name, gen in GENERATORS.items():
        for difficulty in (1, 2, 3):
            rng = random.Random(difficulty)
            for _ in range(300):
                q = gen(rng, difficulty)
                assert len(set(q["options"])) == len(q["options"]) == 4, (name, q)
                assert 0 <= q["correct_index"] < 4
