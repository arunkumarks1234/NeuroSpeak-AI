"""
NeuroSpeak-AI — Heuristic Severity Classifier
================================================
Classifies dysarthria as Mild / Moderate / Severe using a weighted composite
score derived from three acoustic signals extracted by AcousticExtractor:

  Signal                   Weight   Direction
  ───────────────────────  ──────   ─────────
  Pitch SD (Hz)             0.40    High SD → higher severity
  Pause-to-speech ratio     0.35    High ratio → higher severity
  Spectral centroid dev.    0.25    High deviation → higher severity

Each signal is min-max normalised against typical healthy speech baselines
(derived from literature; tunable via config thresholds).

Score thresholds (from config):
  0.00 – MILD_MAX   → Mild
  MILD_MAX – MOD_MAX → Moderate
  MOD_MAX – 1.00    → Severe

This classifier is intentionally simple and transparent. It is designed to
be replaced by a fine-tuned Wav2Vec2 head (inheriting SeverityClassifier)
when labelled training data is available.
"""

from __future__ import annotations

import numpy as np

from config import config
from severity.base import SeverityClassifier, SeverityLevel, SeverityResult
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Healthy speech baselines (literature-derived) ─────────────────────────────
# These are used for normalisation. Tweak to calibrate for your population.
_HEALTHY_PITCH_SD_HZ = 20.0      # typical pitch SD for healthy speakers
_HEALTHY_PAUSE_RATIO = 0.15      # 15% silence/speech ratio (healthy)
_HEALTHY_CENTROID_HZ = 2500.0    # spectral centroid for clear speech (Hz)

_MAX_PITCH_SD_HZ = 80.0          # upper bound for clipping
_MAX_PAUSE_RATIO = 0.80          # upper bound for clipping
_MAX_CENTROID_DEV_HZ = 2000.0    # upper bound for spectral centroid deviation

# Signal weights (must sum to 1.0)
_W_PITCH = 0.40
_W_PAUSE = 0.35
_W_CENTROID = 0.25

assert abs(_W_PITCH + _W_PAUSE + _W_CENTROID - 1.0) < 1e-6, "Weights must sum to 1.0"


def _clip_normalise(value: float, baseline: float, maximum: float) -> float:
    """
    Normalise ``value`` relative to a healthy baseline.

    Returns 0.0 for healthy speech, 1.0 for the worst-case value.
    """
    deviation = abs(value - baseline)
    normalised = deviation / (maximum - baseline + 1e-9)
    return float(np.clip(normalised, 0.0, 1.0))


class HeuristicSeverityClassifier(SeverityClassifier):
    """
    Rule-based dysarthria severity classifier.

    Uses three acoustic features with configurable thresholds.
    The Wav2Vec2 embedding is accepted for API compatibility but is not
    used in this implementation (reserved for a future fine-tuned head).
    """

    def __init__(self) -> None:
        self._mild_max = config.severity_mild_max
        self._moderate_max = config.severity_moderate_max
        logger.info(
            "HeuristicSeverityClassifier | mild<%.2f | moderate<%.2f",
            self._mild_max,
            self._moderate_max,
        )

    def classify(
        self,
        embedding: np.ndarray,
        acoustic_features: dict,
    ) -> SeverityResult:
        """
        Classify severity from acoustic features.

        Args:
            embedding:        Unused in this implementation (interface compatibility).
            acoustic_features: Dict from AcousticExtractor with keys:
                               ``avg_pitch_hz``, ``pitch_sd_hz``,
                               ``pause_ratio``, ``spectral_centroid_hz``.

        Returns:
            :class:`SeverityResult` with level and per-signal contributions.
        """
        pitch_sd = float(acoustic_features.get("pitch_sd_hz", _HEALTHY_PITCH_SD_HZ))
        pause_ratio = float(acoustic_features.get("pause_ratio", _HEALTHY_PAUSE_RATIO))
        centroid = float(acoustic_features.get("spectral_centroid_hz", _HEALTHY_CENTROID_HZ))

        # ── Normalise each signal to [0, 1] ───────────────────────────────────
        pitch_score = _clip_normalise(pitch_sd, _HEALTHY_PITCH_SD_HZ, _MAX_PITCH_SD_HZ)
        pause_score = _clip_normalise(pause_ratio, _HEALTHY_PAUSE_RATIO, _MAX_PAUSE_RATIO)
        centroid_score = _clip_normalise(centroid, _HEALTHY_CENTROID_HZ, _MAX_CENTROID_DEV_HZ)

        # ── Weighted composite ────────────────────────────────────────────────
        composite = (
            _W_PITCH * pitch_score
            + _W_PAUSE * pause_score
            + _W_CENTROID * centroid_score
        )
        composite = float(np.clip(composite, 0.0, 1.0))

        # ── Threshold classification ──────────────────────────────────────────
        if composite < self._mild_max:
            level = SeverityLevel.MILD
        elif composite < self._moderate_max:
            level = SeverityLevel.MODERATE
        else:
            level = SeverityLevel.SEVERE

        # Approximate confidence as distance from nearest threshold
        if level == SeverityLevel.MILD:
            confidence = 1.0 - (composite / self._mild_max)
        elif level == SeverityLevel.MODERATE:
            mid = (self._mild_max + self._moderate_max) / 2
            confidence = 1.0 - abs(composite - mid) / (
                (self._moderate_max - self._mild_max) / 2
            )
        else:
            confidence = (composite - self._moderate_max) / (1.0 - self._moderate_max)

        confidence = float(np.clip(confidence, 0.0, 1.0))

        logger.info(
            "Severity: %s (score=%.3f, confidence=%.2f) | "
            "pitch=%.2f pause=%.2f centroid=%.2f",
            level.value,
            composite,
            confidence,
            pitch_score,
            pause_score,
            centroid_score,
        )

        return SeverityResult(
            level=level,
            score=composite,
            confidence=confidence,
            feature_contributions={
                "pitch_sd_contribution": round(pitch_score * _W_PITCH, 4),
                "pause_contribution": round(pause_score * _W_PAUSE, 4),
                "centroid_contribution": round(centroid_score * _W_CENTROID, 4),
                "pitch_sd_hz": pitch_sd,
                "pause_ratio": pause_ratio,
                "spectral_centroid_hz": centroid,
            },
            classifier="HeuristicSeverityClassifier",
        )
