"""Loads trained model artifacts and serves predictions with safe fallbacks.

If artifacts are missing (fresh clone), models are trained on the synthetic
dataset on first use (~seconds) and persisted. If anything fails, a transparent
heuristic is used and the prediction is tagged `source="fallback"`.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import joblib
import numpy as np
import pandas as pd

from app.core.config import get_settings
from app.ml import train as trainer
from app.ml.features import ENGAGEMENT_FEATURES, PROFILE_FEATURES, STRUGGLE_FEATURES

log = logging.getLogger("lumora.ml")


@dataclass
class Prediction:
    value: float
    model_name: str
    version: str
    source: str  # model | fallback
    label: str | None = None
    detail: str | None = None


class ModelRegistry:
    def __init__(self, artifact_dir: str | None = None) -> None:
        self.dir = Path(artifact_dir or get_settings().ml_artifact_dir)
        self._lock = Lock()
        self._loaded = False
        self.struggle: dict | None = None
        self.engagement: dict | None = None
        self.profiles: dict | None = None

    # -- lifecycle ---------------------------------------------------------
    def ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            try:
                if not (self.dir / trainer.STRUGGLE_FILE).exists():
                    log.info("No ML artifacts found - training on synthetic data (first run).")
                    trainer.train_all("synthetic", str(self.dir))
                self.struggle = joblib.load(self.dir / trainer.STRUGGLE_FILE)
                self.engagement = joblib.load(self.dir / trainer.ENGAGEMENT_FILE)
                self.profiles = joblib.load(self.dir / trainer.PROFILE_FILE)
            except Exception:  # pragma: no cover - defensive: never break the app
                log.exception("Could not load ML models; using heuristic fallbacks.")
            self._loaded = True

    def reload(self) -> None:
        with self._lock:
            self._loaded = False
        self.ensure_loaded()

    def metrics(self) -> dict | None:
        path = self.dir / trainer.METRICS_FILE
        return json.loads(path.read_text()) if path.exists() else None

    # -- predictions -------------------------------------------------------
    def predict_struggle(self, features: dict[str, float]) -> Prediction:
        self.ensure_loaded()
        if self.struggle:
            X = pd.DataFrame([[features[f] for f in STRUGGLE_FEATURES]], columns=STRUGGLE_FEATURES)
            p = float(self.struggle["model"].predict_proba(X)[0, 1])
            return Prediction(p, "struggle_logreg", self.struggle["version"], "model",
                              detail=f"trained on {self.struggle['data']} data")
        p = 1 - (0.6 * features["mastery"] + 0.4 * features["recent_accuracy"])
        p += 0.08 * (features["next_difficulty"] - 2)
        return Prediction(float(np.clip(p, 0.02, 0.98)), "struggle_heuristic", "fallback-1", "fallback")

    def predict_engagement(self, features: dict[str, float]) -> Prediction:
        self.ensure_loaded()
        if self.engagement:
            X = pd.DataFrame([[features[f] for f in ENGAGEMENT_FEATURES]], columns=ENGAGEMENT_FEATURES)
            p = float(self.engagement["model"].predict_proba(X)[0, 1])
            return Prediction(p, self.engagement.get("name", "engagement_model"), self.engagement["version"], "model",
                              detail=f"trained on {self.engagement['data']} data")
        p = 0.85 - 0.01 * features["session_minutes"] - 0.08 * features["mistake_streak"]
        return Prediction(float(np.clip(p, 0.05, 0.95)), "engagement_heuristic", "fallback-1", "fallback")

    def assign_profile(self, features: dict[str, float]) -> Prediction:
        self.ensure_loaded()
        if self.profiles:
            X = pd.DataFrame([[features[f] for f in PROFILE_FEATURES]], columns=PROFILE_FEATURES)
            z = self.profiles["scaler"].transform(X)
            km = self.profiles["kmeans"]
            idx = int(km.predict(z)[0])
            dists = np.linalg.norm(km.cluster_centers_ - z, axis=1)
            # soft confidence: how much closer the chosen centroid is than the runner-up
            sorted_d = np.sort(dists)
            conf = float(1 - sorted_d[0] / (sorted_d[1] + 1e-9)) if len(sorted_d) > 1 else 1.0
            key = self.profiles["names"][idx]
            return Prediction(round(conf, 3), "profile_kmeans", self.profiles["version"], "model", label=key)
        key = "confidence_builder" if features["accuracy"] < 0.5 else "careful_thinker"
        return Prediction(0.0, "profile_heuristic", "fallback-1", "fallback", label=key)


registry = ModelRegistry()
