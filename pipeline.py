"""
NeuroSpeak-AI — Main Inference Pipeline
=========================================
Orchestrates the full end-to-end inference workflow:

  1. Audio preprocessing (16 kHz mono)
  2. ASR — Whisper Large V3
  3. Phonetic Shield corrections
  4. Multi-agent semantic reconstruction (Qwen + Llama)
  5. Wav2Vec2 speech embedding extraction
  6. Acoustic feature extraction (pitch, pauses, spectral centroid)
  7. Dysarthria severity classification
  8. AI coaching recommendations
  9. Session persistence

All components are loaded lazily and cached for efficiency.
Provider selection is driven entirely by ``config.py`` (no hard imports).
"""

from __future__ import annotations

import importlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np

from acoustics.extractor import AcousticExtractor, AcousticFeatures
from agents.orchestrator import AgentOrchestrator, OrchestrationResult
from asr.base import ASRProvider, ASRResult
from asr.phonetic_shield import PhoneticShield
from audio.loader import AudioInput
from audio.preprocessor import ProcessedAudio, preprocess
from coaching.coach import CoachingEngine
from config import config
from embeddings.base import EmbeddingProvider
from severity.base import SeverityClassifier, SeverityResult
from storage.models import SessionRecord
from storage.sqlite_repository import SQLiteSessionRepository
from utils.logger import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Result
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PipelineResult:
    """Complete result from one inference pass through the full pipeline."""

    # Audio
    duration_seconds: float
    source: str

    # ASR
    raw_transcript: str
    asr_language: str
    asr_provider: str

    # Phonetic Shield
    shield_transcript: str
    shield_changes: list[str]

    # Agents
    final_transcript: str
    agent_rounds: int
    ollama_available: bool
    guard_triggered: bool
    agent_log: list[dict]

    # Acoustics
    acoustic_features: AcousticFeatures

    # Severity
    severity: SeverityResult

    # Coaching
    coaching_recommendations: list[str]

    # Storage
    session_id: str
    timestamp: datetime

    # Timing
    elapsed_seconds: float = 0.0

    # Errors (non-fatal)
    warnings: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Provider Loading
# ─────────────────────────────────────────────────────────────────────────────

def _load_provider(registry: dict, key: str) -> object:
    """
    Dynamically import and instantiate a provider class from the registry.

    Args:
        registry: e.g. ``config.asr_registry``
        key:      e.g. ``"whisper"``

    Returns:
        Instantiated provider.

    Raises:
        ValueError: If the key is not in the registry.
        ImportError: If the module cannot be loaded.
    """
    if key not in registry:
        raise ValueError(
            f"Unknown provider '{key}'. Available: {list(registry.keys())}"
        )
    module_path, class_name = registry[key]
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    instance = cls()
    return instance  # type: ignore[no-any-return]


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Class
# ─────────────────────────────────────────────────────────────────────────────

class NeuroSpeakPipeline:
    """
    Main NeuroSpeak-AI inference pipeline.

    Lazy-loads all ML components on first use; subsequent calls are fast.

    Usage::

        pipeline = NeuroSpeakPipeline()
        result = pipeline.run(audio_input)
    """

    def __init__(self) -> None:
        self._asr: ASRProvider | None = None
        self._embedding: EmbeddingProvider | None = None
        self._shield = PhoneticShield()
        self._orchestrator = AgentOrchestrator()
        self._acoustic_extractor = AcousticExtractor()
        self._severity_classifier: SeverityClassifier | None = None
        self._coaching_engine = CoachingEngine()
        self._repository = SQLiteSessionRepository()

        logger.info(
            "NeuroSpeakPipeline ready | ASR=%s | Embedding=%s | Device=%s",
            config.asr_provider,
            config.embedding_provider,
            config.device,
        )

    # ── Lazy loaders ────────────────────────────────────────────────────────

    def _get_asr(self) -> ASRProvider:
        if self._asr is None:
            logger.info("Loading ASR provider: %s", config.asr_provider)
            self._asr = _load_provider(  # type: ignore[assignment]
                config.asr_registry, config.asr_provider
            )
        assert self._asr is not None
        return self._asr

    def _get_embedding(self) -> EmbeddingProvider:
        if self._embedding is None:
            logger.info("Loading embedding provider: %s", config.embedding_provider)
            self._embedding = _load_provider(  # type: ignore[assignment]
                config.embedding_registry, config.embedding_provider
            )
        assert self._embedding is not None
        return self._embedding

    def _get_severity_classifier(self) -> SeverityClassifier:
        if self._severity_classifier is None:
            backend = config.severity_classifier
            if backend == "ml":
                from severity.ml_classifier import (  # noqa: PLC0415
                    LogisticRegressionSeverityClassifier,
                )
                # If a trained model exists, load it; otherwise the wrapper
                # falls back to the heuristic scorer.
                if config.severity_model_path.exists():
                    self._severity_classifier = LogisticRegressionSeverityClassifier.load(
                        config.severity_model_path
                    )
                else:
                    logger.warning(
                        "SEVERITY_CLASSIFIER=ml but no model at %s. "
                        "Using untrained ML wrapper (heuristic fallback).",
                        config.severity_model_path,
                    )
                    self._severity_classifier = LogisticRegressionSeverityClassifier()
            else:
                from severity.heuristic_classifier import (  # noqa: PLC0415
                    HeuristicSeverityClassifier,
                )
                self._severity_classifier = HeuristicSeverityClassifier()
        return self._severity_classifier

    # ── Main run ────────────────────────────────────────────────────────────

    def run(self, audio_input: AudioInput) -> PipelineResult:
        """
        Run the complete NeuroSpeak-AI pipeline on one audio input.

        Args:
            audio_input: :class:`~audio.loader.AudioInput` from loader.

        Returns:
            :class:`PipelineResult` with all inference outputs.
        """
        t_start = time.perf_counter()
        warnings: list[str] = []
        timestamp = datetime.now(timezone.utc)

        # ── Step 1: Preprocess ───────────────────────────────────────────────
        logger.info("=== Pipeline Start: source=%s ===", audio_input.source)
        processed: ProcessedAudio = preprocess(audio_input)
        audio = processed.audio
        sr = processed.sample_rate
        duration = processed.duration_seconds

        # ── Step 2: ASR ──────────────────────────────────────────────────────
        asr_result: ASRResult = self._get_asr().transcribe(audio, sr)
        raw_transcript = asr_result.transcript
        if not raw_transcript:
            raw_transcript = "[No speech detected]"
            warnings.append("ASR returned an empty transcript.")

        # ── Step 3: Phonetic Shield ──────────────────────────────────────────
        shield_transcript, shield_changes = self._shield.apply(raw_transcript)

        # ── Step 4: Multi-agent reconstruction ──────────────────────────────
        acoustic_feat_dict: dict = {}  # populated in step 6, passed to agents later
        orch_result: OrchestrationResult = self._orchestrator.run(
            raw_transcript=raw_transcript,
            shield_transcript=shield_transcript,
            shield_changes=shield_changes,
            duration_seconds=duration,
            acoustic_features=acoustic_feat_dict,
        )

        # ── Step 5: Wav2Vec2 embedding ───────────────────────────────────────
        try:
            embedding: np.ndarray = self._get_embedding().embed(audio, sr)
        except Exception as exc:  # noqa: BLE001
            logger.error("Embedding extraction failed: %s", exc)
            # facebook/wav2vec2-base has a 768-D hidden state.
            embedding = np.zeros(768, dtype=np.float32)
            warnings.append(f"Embedding extraction failed: {exc}")

        # ── Step 6: Acoustic features ────────────────────────────────────────
        try:
            acoustic_features: AcousticFeatures = self._acoustic_extractor.extract(audio, sr)
            acoustic_feat_dict = acoustic_features.to_dict()
        except Exception as exc:  # noqa: BLE001
            logger.error("Acoustic feature extraction failed: %s", exc)
            from acoustics.extractor import AcousticFeatures  # noqa: PLC0415
            acoustic_features = AcousticFeatures(
                avg_pitch_hz=0.0, pitch_sd_hz=0.0,
                pause_duration_sec=0.0, pause_ratio=0.0,
                spectral_centroid_hz=0.0, duration_sec=duration,
                extraction_method="failed",
            )
            acoustic_feat_dict = acoustic_features.to_dict()
            warnings.append(f"Acoustic extraction failed: {exc}")

        # ── Step 7: Severity classification ──────────────────────────────────
        try:
            severity: SeverityResult = self._get_severity_classifier().classify(
                embedding, acoustic_feat_dict
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Severity classification failed: %s", exc)
            from severity.base import SeverityLevel  # noqa: PLC0415
            severity = SeverityResult(
                level=SeverityLevel.UNKNOWN,
                score=0.0, confidence=0.0,
                feature_contributions={},
                classifier="failed",
            )
            warnings.append(f"Severity classification failed: {exc}")

        # ── Step 8: Coaching ─────────────────────────────────────────────────
        try:
            coaching = self._coaching_engine.generate(
                severity_level=severity.level,
                transcript=orch_result.final_text,
                acoustic_features=acoustic_feat_dict,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Coaching engine failed: %s", exc)
            coaching = ["Coaching recommendations unavailable — please try again."]
            warnings.append(f"Coaching failed: {exc}")

        # ── Step 9: Save session ─────────────────────────────────────────────
        import uuid  # noqa: PLC0415
        session_id = str(uuid.uuid4())
        try:
            record = SessionRecord(
                id=session_id,
                timestamp=timestamp,
                source=audio_input.source,
                duration_seconds=duration,
                original_path=audio_input.original_path,
                raw_transcript=raw_transcript,
                shield_transcript=shield_transcript,
                shield_changes=shield_changes,
                final_transcript=orch_result.final_text,
                asr_language=asr_result.language,
                asr_provider=asr_result.provider,
                agent_rounds=orch_result.rounds_completed,
                ollama_available=orch_result.ollama_available,
                guard_triggered=orch_result.guard_triggered,
                severity_level=severity.level.value,
                severity_score=severity.score,
                severity_confidence=severity.confidence,
                severity_classifier=severity.classifier,
                acoustic_features=acoustic_feat_dict,
                coaching_recommendations=coaching,
            )
            self._repository.save(record)
        except Exception as exc:  # noqa: BLE001
            logger.error("Session save failed: %s", exc)
            warnings.append(f"Session not saved: {exc}")

        elapsed = round(time.perf_counter() - t_start, 2)
        logger.info("=== Pipeline Complete: %.2f s ===", elapsed)

        return PipelineResult(
            duration_seconds=duration,
            source=audio_input.source,
            raw_transcript=raw_transcript,
            asr_language=asr_result.language,
            asr_provider=asr_result.provider,
            shield_transcript=shield_transcript,
            shield_changes=shield_changes,
            final_transcript=orch_result.final_text,
            agent_rounds=orch_result.rounds_completed,
            ollama_available=orch_result.ollama_available,
            guard_triggered=orch_result.guard_triggered,
            agent_log=orch_result.agent_log,
            acoustic_features=acoustic_features,
            severity=severity,
            coaching_recommendations=coaching,
            session_id=session_id,
            timestamp=timestamp,
            elapsed_seconds=elapsed,
            warnings=warnings,
        )

    def get_history(self, limit: int = 50) -> list[SessionRecord]:
        """Return recent session records from storage."""
        return self._repository.get_all(limit=limit)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        return self._repository.delete(session_id)
