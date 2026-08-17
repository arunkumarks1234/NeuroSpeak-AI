from __future__ import annotations

import numpy as np

from severity.base import SeverityLevel
from severity.heuristic_classifier import HeuristicSeverityClassifier


def test_heuristic_classifier_mild():
    classifier = HeuristicSeverityClassifier()
    # Healthy baseline values
    features = {
        "pitch_sd_hz": 20.0,
        "pause_ratio": 0.15,
        "spectral_centroid_hz": 2500.0,
    }
    dummy_embedding = np.zeros(10)

    result = classifier.classify(dummy_embedding, features)
    assert result.level == SeverityLevel.MILD
    assert result.score == 0.0


def test_heuristic_classifier_severe():
    classifier = HeuristicSeverityClassifier()
    # Pathological values maxing out the heuristic
    features = {
        "pitch_sd_hz": 80.0,
        "pause_ratio": 0.80,
        "spectral_centroid_hz": 500.0,
    }
    dummy_embedding = np.zeros(10)

    result = classifier.classify(dummy_embedding, features)
    assert result.level == SeverityLevel.SEVERE
    # With new weights: Pitch (0.6*1.0) + Pause (0.3*1.0) + Centroid (0.1*0.0) = 0.9
    # The test requires the score to be decisively in the "severe" range.
    assert result.score > 0.8
