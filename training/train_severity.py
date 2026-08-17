"""
NeuroSpeak-AI — Severity Classifier Training Script
=====================================================
Trains the Logistic Regression baseline on labelled Wav2Vec2 embeddings.

This script is intentionally kept separate from application code so the
model can be trained offline. It does NOT need to be run to use the app —
the classifier falls back to the heuristic scorer until a trained model
is available at the configured SEVERITY_MODEL_PATH.

Usage::

    python training/train_severity.py --data path/to/embeddings.npz \\
        --out ml_models/severity_model.joblib

Expected input format (``embeddings.npz``)::

    X   -> (n_samples, 768) float32 embedding matrix
    y   -> (n_samples,) int labels (0=Mild, 1=Moderate, 2=Severe)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from config import config
from severity.metrics import evaluate
from severity.ml_classifier import LogisticRegressionSeverityClassifier
from utils.logger import get_logger

logger = get_logger(__name__)

_LABELS = ["Mild", "Moderate", "Severe"]


def load_dataset(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load X (embeddings) and y (label indices) from an .npz file."""
    data = np.load(path)
    X = data["X"]
    y = data["y"]
    if X.ndim != 2:
        raise ValueError(f"X must be 2-D (n, dim); got shape {X.shape}")
    if y.ndim != 1:
        raise ValueError(f"y must be 1-D; got shape {y.shape}")
    if X.shape[0] != y.shape[0]:
        raise ValueError("X and y row counts must match.")
    logger.info("Loaded dataset: %d samples, %d features.", *X.shape)
    return X, y


def main() -> None:
    parser = argparse.ArgumentParser(description="Train severity classifier.")
    parser.add_argument(
        "--data",
        type=Path,
        required=True,
        help="Path to .npz with keys X (embeddings) and y (label indices).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=config.severity_model_path,
        help="Output path for the serialised model.",
    )
    parser.add_argument("--test-size", type=float, default=0.2, help="Held-out split.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    X, y = load_dataset(args.data)

    le = LabelEncoder()
    y_encoded = le.fit_transform(y)  # works for both str and int arrays

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=args.test_size, random_state=args.seed, stratify=y_encoded
    )

    logger.info("Train: %d | Test: %d", X_train.shape[0], X_test.shape[0])

    # ── Baseline: Logistic Regression ─────────────────────────────────────────
    clf = LogisticRegression(
        max_iter=1000,
        C=1.0,
        multi_class="multinomial",
        solver="lbfgs",
        random_state=args.seed,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    report = evaluate(y_test, y_pred, labels=[str(c) for c in le.classes_])
    print(report)

    logger.info("Saving model to %s", args.out)
    model = LogisticRegressionSeverityClassifier(
        model=clf,
        label_encoder=le,
        meta={
            "version": "0.1.0",
            "architecture": "LogisticRegression",
            "features": int(X.shape[1]),
            "train_samples": int(X_train.shape[0]),
            "test_samples": int(X_test.shape[0]),
            "accuracy": report.accuracy,
            "f1": report.f1,
        },
    )
    model.save(args.out)
    logger.info("Done.")


if __name__ == "__main__":
    main()