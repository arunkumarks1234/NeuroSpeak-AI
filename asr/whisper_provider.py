"""
NeuroSpeak-AI — Whisper Large V3 ASR Provider
================================================
Uses ``faster-whisper`` (CTranslate2 backend) for 4× faster inference
compared to the standard openai-whisper package.

GPU:  float16, beam_size=5
CPU:  int8,   beam_size=3  (reasonable quality, much faster)

Model is lazy-loaded on first call and cached for subsequent calls.
"""

from __future__ import annotations

import numpy as np

from asr.base import ASRProvider, ASRResult
from config import config
from utils.logger import get_logger

logger = get_logger(__name__)


class WhisperProvider(ASRProvider):
    """
    Whisper Large V3 ASR using faster-whisper.

    The model is loaded lazily on the first ``transcribe()`` call and
    held in memory for the process lifetime (singleton pattern).
    """

    _model = None  # class-level cache

    def __init__(self) -> None:
        self._model_name = config.whisper_model
        self._device = config.device
        self._compute_type = config.compute_type
        logger.info(
            "WhisperProvider initialised | model=%s device=%s compute=%s",
            self._model_name,
            self._device,
            self._compute_type,
        )

    @property
    def provider_name(self) -> str:
        return f"faster-whisper/{self._model_name}"

    def warm_up(self) -> None:
        """Eagerly load the Whisper model into memory."""
        self._get_model()

    def _get_model(self):
        """Return the cached model, loading it on first call."""
        if WhisperProvider._model is None:
            from faster_whisper import WhisperModel  # noqa: PLC0415

            logger.info(
                "Loading Whisper model '%s' on %s (%s) — this may take a moment...",
                self._model_name,
                self._device,
                self._compute_type,
            )
            WhisperProvider._model = WhisperModel(
                self._model_name,
                device=self._device,
                compute_type=self._compute_type,
                num_workers=2,
                cpu_threads=4,
            )
            logger.info("Whisper model loaded successfully.")
        return WhisperProvider._model

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> ASRResult:
        """
        Transcribe a 16 kHz mono float32 audio array via Whisper Large V3.

        Args:
            audio:       1-D float32 array at 16 kHz.
            sample_rate: Must be 16,000 Hz.

        Returns:
            :class:`ASRResult` with full word-level timestamps.
        """
        if sample_rate != 16_000:
            logger.warning(
                "WhisperProvider expects 16 kHz input; got %d Hz. "
                "Results may be degraded.",
                sample_rate,
            )

        model = self._get_model()

        # Beam size: larger = better quality but slower
        beam_size = 5 if self._device == "cuda" else 3

        logger.info("Running Whisper transcription (beam_size=%d)...", beam_size)

        segments, info = model.transcribe(
            audio,
            beam_size=beam_size,
            word_timestamps=True,
            language=None,          # auto-detect language
            vad_filter=True,        # skip silent segments (voice activity detection)
            vad_parameters={
                "min_silence_duration_ms": 300,
                "speech_pad_ms": 200,
            },
            condition_on_previous_text=True,
            no_speech_threshold=0.6,
        )

        # Consume the generator and collect results
        full_text_parts: list[str] = []
        word_timestamps: list[dict] = []

        for segment in segments:
            full_text_parts.append(segment.text.strip())
            if segment.words:
                for word in segment.words:
                    word_timestamps.append(
                        {
                            "word": word.word.strip(),
                            "start": round(word.start, 3),
                            "end": round(word.end, 3),
                            "probability": round(word.probability, 4),
                        }
                    )

        transcript = " ".join(full_text_parts).strip()
        language = info.language if info.language else "en"
        language_prob = round(info.language_probability, 4) if info.language_probability else -1.0

        logger.info(
            "Transcription complete | lang=%s (%.1f%%) | words=%d",
            language,
            language_prob * 100,
            len(word_timestamps),
        )

        return ASRResult(
            transcript=transcript,
            language=language,
            confidence=language_prob,
            word_timestamps=word_timestamps,
            provider=self.provider_name,
        )
