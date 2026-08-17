"""Unit tests for the ML severity classifier and evaluation metrics."""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

from severity.base import SeverityLevel, SeverityResult
from severity.metrics import EvaluationReport, evaluate
from severity.ml_classifier import LogisticRegressionSeverityClassifier


@pytest.fixture
def trained_classifier() -> LogisticRegressionSeverityClassifier:
    """Build and return a tiny, fitted classifier for interface tests."""
    rng = np.random.default_rng(42)

    # 30 samples, 768 features — 3 separable clusters for clean training
    X = np.vstack(
        [
            rng.normal(0.0, 0.5, (10, 768)).astype(np.float32),
            rng.normal(2.0, 0.5, (10, 768)).astype(np.float32),
            rng.normal(4.0, 0.5, (10, 768)).astype(np.float32),
        ]
    )
    y = np.array([0] * 10 + [1] * 10 + [2] * 10)

    clf = LogisticRegression(max_iter=500)
    clf.fit(X, y)
    le = LabelEncoder().fit(["Mild", "Moderate", "Severe"])

    return LogisticRegressionSeverityClassifier(model=clf, label_encoder=le)


def test_untrained_falls_back_to_heuristic():
    """An untrained ML classifier must fall back to the heuristic scorer."""
    classifier = LogisticRegressionSeverityClassifier()
    assert classifier.is_trained is False

    result = classifier.classify(np.zeros(768, dtype=np.float32), {})
    assert isinstance(result, SeverityResult)
    assert result.level in (
        SeverityLevel.MILD,
        SeverityLevel.MODERATE,
        SeverityLevel.SEVERE,
    )
    assert result.classifier == "HeuristicSeverityClassifier"


def test_trained_classify_returns_valid_result(trained_classifier):
    """A trained classifier returns a valid SeverityResult with confidence."""
    rng = np.random.default_rng(1)
    emb = rng.normal(4.0, 0.5, (768,)).astype(np.float32)  # severe cluster

    result = trained_classifier.classify(emb, {})

    assert isinstance(result, SeverityResult)
    assert result.level in (SeverityLevel.MILD, SeverityLevel.MODERATE, SeverityLevel.SEVERE)
    assert 0.0 <= result.score <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert result.classifier == "LogisticRegressionSeverityClassifier"


def test_save_and_load_roundtrip(tmp_path, trained_classifier):
    """Save/load must preserve predictions."""
    path = tmp_path / "model.joblib"
    trained_classifier.save(path)

    restored = LogisticRegressionSeverityClassifier.load(path)

    assert restored.is_trained is True
    rng = np.random.default_rng(2)
    emb = rng.normal(0.0, 0.5, (768,)).astype(np.float32)  # mild cluster

    before = trained_classifier.classify(emb, {})
    after = restored.classify(emb, {})

    assert before.level == after.level
    assert before.confidence == pytest.approx(after.confidence, abs=1e-6)


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        LogisticRegressionSeverityClassifier.load(tmp_path / "missing.joblib")


def test_evaluate_metrics_perfect():
    """A perfect classifier gets perfect scores."""
    y_true = np.array([0, 1, 2, 0, 1, 2])
    y_pred = y_true.copy()

    report = evaluate(y_true, y_pred, labels=["Mild", "Moderate", "Severe"])

    assert isinstance(report, EvaluationReport)
    assert report.accuracy == pytest.approx(1.0)
    assert report.precision == pytest.approx(1.0)
    assert report.recall == pytest.approx(1.0)
    assert report.f1 == pytest.approx(1.0)
    assert report.confusion_matrix.shape == (3, 3)
    assert np.trace(report.confusion_matrix) == 6


def test_evaluate_metrics_imperfect():
    y_true = np.array([0, 0, 1, 1, 2, 2])
    y_pred = np.array([0, 1, 1, 2, 2, 0])  # some mistakes

    report = evaluate(y_true, y_pred)

    assert 0.0 < report.accuracy < 1.0
    assert 0.0 <= report.f1 <= 1.0
    assert report.confusion_matrix.shape == (3, 3)


def test_evaluate_requires_matching_lengths():
    with pytest.raises(ValueError):
        evaluate(np.array([0, 1]), np.array([0]), labels=["Mild", "Moderate"])


def test_evaluation_report_to_dict():
    report = evaluate(
        np.array([0, 1, 2]), np.array([0, 1, 2]), labels=["Mild", "Moderate", "Severe"]
    )
    d = report.to_dict()
    assert set(d) == {"accuracy", "precision", "recall", "f1", "confusion_matrix", "labels"}
    assert d["labels"] == ["Mild", "Moderate", "Severe"]