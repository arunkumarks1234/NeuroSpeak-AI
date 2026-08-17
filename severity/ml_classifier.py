"""
NeuroSpeak-AI — Logistic Regression Severity Classifier
==========================================================
Machine-learning baseline for dysarthria severity classification.

This classifier wraps a scikit-learn ``LogisticRegression`` trained on
Wav2Vec2 speech embeddings (768-D) — the modular interface allows the
baseline to be swapped for an MLP, CNN, BiLSTM, or Transformer head later
without changing callers.

Features:
- Softmax calibration provides a natural confidence score per prediction.
- ``save`` / ``load`` classmethods persist and restore trained models
  (model + label encoder + meta) via joblib.
- If a model has NOT been trained yet, the classifier falls back to the
  heuristic scorer so the application remains fully functional before
  labelled data is available.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np

from config import config
from severity.base import SeverityClassifier, SeverityLevel, SeverityResult
from severity.heuristic_classifier import HeuristicSeverityClassifier
from utils.logger import get_logger

logger = get_logger(__name__)

_LABELS = [SeverityLevel.MILD.value, SeverityLevel.MODERATE.value, SeverityLevel.SEVERE.value]


class LogisticRegressionSeverityClassifier(SeverityClassifier):
    """
    Logistic Regression baseline for severity classification.

    Usage::

        model = LogisticRegressionSeverityClassifier.load("path/to/model.joblib")
        result = model.classify(embedding, acoustic_features)
    """

    def __init__(self, model=None, label_encoder=None, meta: dict | None = None) -> None:
        self._model = model
        self._label_encoder = label_encoder
        self._meta = meta or {}
        self._fallback = HeuristicSeverityClassifier()

    # ── Interface ────────────────────────────────────────────────────────────

    def classify(
        self,
        embedding: np.ndarray,
        acoustic_features: dict,
    ) -> SeverityResult:
        """
        Classify severity from a Wav2Vec2 embedding.

        Args:
            embedding:        1-D float32 embedding vector (e.g. 768-D).
            acoustic_features: Optional dict; used only by the heuristic fallback.

        Returns:
            :class:`SeverityResult` with level, score and confidence.
        """
        if self._model is None:
            logger.warning(
                "ML severity model not trained — falling back to heuristic classifier."
            )
            return self._fallback.classify(embedding, acoustic_features)

        features = self._normalize(embedding)
        X = features.reshape(1, -1)

        probs = self._model.predict_proba(X)[0]
        pred_idx = int(self._model.predict(X)[0])

        label = self._label_encoder.inverse_transform([pred_idx])[0]  # type: ignore[attr-defined]
        confidence = float(probs[pred_idx])

        # Enforce monotonic score ordering: Mild=0.0→1 in [0,0.33], Severe=1.
        score = self._level_to_score(label)

        logger.info(
            "ML severity: %s (conf=%.3f) | fallback=%s",
            label,
            confidence,
            self._model is None,
        )

        return SeverityResult(
            level=SeverityLevel(label),
            score=round(score, 4),
            confidence=round(confidence, 4),
            feature_contributions={},
            classifier="LogisticRegressionSeverityClassifier",
        )

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize(embedding: np.ndarray) -> np.ndarray:
        """Return a norm-normalised, finite, 1-D feature vector."""
        arr = np.asarray(embedding, dtype=np.float32)
        if arr.ndim != 1:
            arr = arr.ravel()
        norm = float(np.linalg.norm(arr))
        if norm < 1e-8:
            return arr
        return arr / norm

    @staticmethod
    def _level_to_score(label: str) -> float:
        if label == SeverityLevel.MILD.value:
            return 0.1
        if label == SeverityLevel.MODERATE.value:
            return 0.5
        return 0.9

    # ── Save / Load ──────────────────────────────────────────────────────────

    def save(self, path: str | Path) -> Path:
        """Serialise the trained model, label encoder, and metadata."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "model": self._model,
            "label_encoder": self._label_encoder,
            "meta": self._meta,
        }
        joblib.dump(payload, path, compress=3)
        logger.info("Severity classifier saved to %s", path)
        return path

    @classmethod
    def load(cls, path: str | Path) -> "LogisticRegressionSeverityClassifier":
        """Load a trained classifier from disk."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Severity model not found: {path}")

        payload = joblib.load(path)
        logger.info("Severity classifier loaded from %s", path)
        return cls(
            model=payload.get("model"),
            label_encoder=payload.get("label_encoder"),
            meta=payload.get("meta") or {},
        )

    @property
    def is_trained(self) -> bool:
        """Whether the wrapped estimator has been fitted."""
        return self._model is not None