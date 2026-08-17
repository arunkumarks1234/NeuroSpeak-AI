"""
NeuroSpeak-AI — Abstract Severity Classifier
==============================================
All severity backends implement this ABC.
A fine-tuned Wav2Vec2 head can be dropped in by implementing ``classify``
and registering the class in ``config.py``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import numpy as np


class SeverityLevel(str, Enum):
    """Dysarthria severity classification levels."""

    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"
    UNKNOWN = "Unknown"


@dataclass
class SeverityResult:
    """Structured output from any severity classifier."""

    level: SeverityLevel
    score: float                  # Composite score in [0, 1]; higher = more severe
    confidence: float             # Classifier confidence in [0, 1]
    feature_contributions: dict   # {"pitch_sd": float, "pause_ratio": float, ...}
    classifier: str               # Name of the classifier used


class SeverityClassifier(ABC):
    """Abstract severity classifier interface."""

    @abstractmethod
    def classify(
        self,
        embedding: np.ndarray,
        acoustic_features: dict,
    ) -> SeverityResult:
        """
        Classify dysarthria severity.

        Args:
            embedding:        Speech embedding vector (e.g. Wav2Vec2 output).
            acoustic_features: Dict from :class:`~acoustics.extractor.AcousticExtractor`.

        Returns:
            :class:`SeverityResult` with level, score, and per-feature contributions.
        """
