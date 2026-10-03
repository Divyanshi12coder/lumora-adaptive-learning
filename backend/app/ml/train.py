"""Train, evaluate and persist Lumora's ML models.

Usage:
    python -m app.ml.train                 # auto: real DB data if enough, else synthetic
    python -m app.ml.train --source synthetic
    python -m app.ml.train --source db

Writes joblib artifacts and `metrics.json` to ML_ARTIFACT_DIR. Every metric is
computed on a held-out split grouped by learner (no learner appears in both
train and test), and reported next to a naive baseline so it can be judged honestly.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score, silhouette_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.core.config import get_settings
from app.ml import synthetic
from app.ml.features import ENGAGEMENT_FEATURES, PROFILE_FEATURES, STRUGGLE_FEATURES

log = logging.getLogger("lumora.ml")

STRUGGLE_FILE = "struggle_model.joblib"
ENGAGEMENT_FILE = "engagement_model.joblib"
PROFILE_FILE = "profile_clusters.joblib"
METRICS_FILE = "metrics.json"

PROFILE_NAMES = {
    "fast_focused": ("Fast & Focused", "Answers quickly and accurately - enjoys a brisk pace."),
    "careful_thinker": ("Careful Thinker", "Takes time to think things through and is usually right."),
    "hint_explorer": ("Hint Explorer", "Likes to use hints and examples to unlock ideas."),
    "confidence_builder": ("Confidence Builder", "Is building foundations - benefits from extra scaffolding."),
}


def _split(df: pd.DataFrame, seed: int = 42):
    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
    train_idx, test_idx = next(gss.split(df, groups=df["learner_id"]))
    return df.iloc[train_idx], df.iloc[test_idx]


def _binary_metrics(y_true, proba) -> dict:
    base_rate = float(np.mean(y_true))
    return {
        "roc_auc": round(float(roc_auc_score(y_true, proba)), 4),
        "brier": round(float(brier_score_loss(y_true, proba)), 4),
        "log_loss": round(float(log_loss(y_true, np.clip(proba, 1e-6, 1 - 1e-6))), 4),
        "accuracy_at_0_5": round(float(accuracy_score(y_true, proba >= 0.5)), 4),
        "baseline_brier_constant_rate": round(float(brier_score_loss(y_true, np.full(len(y_true), base_rate))), 4),
        "baseline_accuracy_majority": round(max(base_rate, 1 - base_rate), 4),
        "positive_rate": round(base_rate, 4),
    }


def train_struggle(df: pd.DataFrame) -> tuple[Pipeline, dict]:
    train, test = _split(df)
    pipe = Pipeline([("scale", StandardScaler()), ("clf", LogisticRegression(C=1.0, max_iter=2000))])
    pipe.fit(train[STRUGGLE_FEATURES], train["label_incorrect"])
    proba = pipe.predict_proba(test[STRUGGLE_FEATURES])[:, 1]
    metrics = _binary_metrics(test["label_incorrect"].to_numpy(), proba)
    coefs = pipe.named_steps["clf"].coef_[0]
    metrics["standardized_coefficients"] = {f: round(float(c), 4) for f, c in zip(STRUGGLE_FEATURES, coefs, strict=True)}
    metrics.update(n_train=len(train), n_test=len(test), model="LogisticRegression (standardized features)")
    return pipe, metrics


def _engagement_candidates() -> dict:
    return {
        "GradientBoostingClassifier": lambda: GradientBoostingClassifier(
            n_estimators=150, max_depth=3, learning_rate=0.08, subsample=0.8, random_state=0
        ),
        "LogisticRegression": lambda: Pipeline(
            [("scale", StandardScaler()), ("clf", LogisticRegression(max_iter=2000))]
        ),
    }


def train_engagement(df: pd.DataFrame) -> tuple[object, dict]:
    """Model selection on a grouped validation split carved from the training set;
    the test split is only used once, for the final report."""
    train, test = _split(df)
    sub_train, val = _split(train, seed=7)
    X, y = ENGAGEMENT_FEATURES, "label_engaged"
    val_auc = {}
    for name, make in _engagement_candidates().items():
        m = make().fit(sub_train[X], sub_train[y])
        val_auc[name] = round(float(roc_auc_score(val[y], m.predict_proba(val[X])[:, 1])), 4)
    chosen = max(val_auc, key=val_auc.get)
    model = _engagement_candidates()[chosen]().fit(train[X], train[y])
    proba = model.predict_proba(test[X])[:, 1]
    metrics = _binary_metrics(test[y].to_numpy(), proba)
    metrics["validation_roc_auc_by_candidate"] = val_auc
    if hasattr(model, "feature_importances_"):
        metrics["feature_importances"] = {
            f: round(float(v), 4) for f, v in zip(X, model.feature_importances_, strict=True)
        }
    else:
        coefs = model.named_steps["clf"].coef_[0]
        metrics["standardized_coefficients"] = {f: round(float(c), 4) for f, c in zip(X, coefs, strict=True)}
    metrics.update(n_train=len(train), n_test=len(test), model=chosen, selected_by="validation ROC-AUC")
    return model, metrics


def _name_clusters(centroids_z: np.ndarray) -> list[str]:
    idx = {f: i for i, f in enumerate(PROFILE_FEATURES)}
    keys = list(PROFILE_NAMES)
    score = np.zeros((len(centroids_z), len(keys)))
    for c, z in enumerate(centroids_z):
        acc, hint, resp = z[idx["accuracy"]], z[idx["hint_rate"]], z[idx["avg_response_ratio"]]
        score[c] = [acc - resp, acc + resp, hint, -acc]
    rows, cols = linear_sum_assignment(-score)
    names = [""] * len(centroids_z)
    for r, c in zip(rows, cols, strict=True):
        names[r] = keys[c]
    return names


def train_profiles(df: pd.DataFrame, k: int = 4) -> tuple[dict, dict]:
    scaler = StandardScaler().fit(df[PROFILE_FEATURES])
    X = scaler.transform(df[PROFILE_FEATURES])
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(X)
    names = _name_clusters(km.cluster_centers_)
    centroids = scaler.inverse_transform(km.cluster_centers_)
    metrics = {
        "model": f"KMeans (k={k}) on standardized behaviour aggregates",
        "silhouette": round(float(silhouette_score(X, km.labels_)), 4),
        "n_learners": len(df),
        "clusters": {
            names[i]: {f: round(float(v), 3) for f, v in zip(PROFILE_FEATURES, centroids[i], strict=True)}
            for i in range(k)
        },
    }
    return {"scaler": scaler, "kmeans": km, "names": names}, metrics


def _datasets(source: str):
    """Return (struggle_df, engagement_df, profile_df, provenance dict)."""
    settings = get_settings()
    provenance = {"struggle": "synthetic", "engagement": "synthetic", "profiles": "synthetic"}
    s_df = e_df = p_df = None
    if source in ("db", "auto"):
        from app.db.session import SessionLocal
        from app.ml.real_data import engagement_dataset_from_db, profile_dataset_from_db, struggle_dataset_from_db

        with SessionLocal() as db:
            real_s = struggle_dataset_from_db(db)
            real_e = engagement_dataset_from_db(db)
            real_p = profile_dataset_from_db(db)
        enough = settings.ml_min_real_samples
        if len(real_s) >= enough and real_s["label_incorrect"].nunique() == 2 and real_s["learner_id"].nunique() >= 4:
            s_df, provenance["struggle"] = real_s, "real"
        if len(real_e) >= enough and real_e["label_engaged"].nunique() == 2 and real_e["learner_id"].nunique() >= 4:
            e_df, provenance["engagement"] = real_e, "real"
        if len(real_p) >= 40:
            p_df, provenance["profiles"] = real_p, "real"
        if source == "db" and "real" not in provenance.values():
            log.warning("Not enough real interaction data yet; falling back to synthetic data.")
    if s_df is None:
        s_df = synthetic.generate_struggle_dataset()
    if e_df is None:
        e_df = synthetic.generate_engagement_dataset()
    if p_df is None:
        p_df = synthetic.generate_profile_dataset()
    return s_df, e_df, p_df, provenance


def train_all(source: str = "synthetic", artifact_dir: str | None = None) -> dict:
    out = Path(artifact_dir or get_settings().ml_artifact_dir)
    out.mkdir(parents=True, exist_ok=True)
    s_df, e_df, p_df, provenance = _datasets(source)
    version = datetime.now(UTC).strftime("%Y%m%d%H%M%S")

    s_model, s_metrics = train_struggle(s_df)
    e_model, e_metrics = train_engagement(e_df)
    p_model, p_metrics = train_profiles(p_df)

    joblib.dump({"model": s_model, "features": STRUGGLE_FEATURES, "version": f"struggle-{version}",
                 "data": provenance["struggle"]}, out / STRUGGLE_FILE)
    joblib.dump({"model": e_model, "features": ENGAGEMENT_FEATURES, "version": f"engagement-{version}",
                 "name": "engagement_" + ("gbm" if "Gradient" in e_metrics["model"] else "logreg"),
                 "data": provenance["engagement"]}, out / ENGAGEMENT_FILE)
    joblib.dump({**p_model, "features": PROFILE_FEATURES, "version": f"profiles-{version}",
                 "data": provenance["profiles"]}, out / PROFILE_FILE)

    metrics = {
        "trained_at": datetime.now(UTC).isoformat(),
        "version": version,
        "data_provenance": provenance,
        "note": "Metrics on SYNTHETIC data validate the pipeline only; they are not real-world accuracy claims.",
        "struggle_model": s_metrics,
        "engagement_model": e_metrics,
        "profile_clusters": p_metrics,
    }
    (out / METRICS_FILE).write_text(json.dumps(metrics, indent=2))
    return metrics


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Train Lumora ML models")
    parser.add_argument("--source", choices=["synthetic", "db", "auto"], default="auto")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    metrics = train_all(args.source, args.out)
    print(json.dumps({k: v for k, v in metrics.items() if k != "profile_clusters"}, indent=2))
    print("Profile clusters:", json.dumps(metrics["profile_clusters"], indent=2))


if __name__ == "__main__":
    main()
