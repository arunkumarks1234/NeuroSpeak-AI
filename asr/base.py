"""
NeuroSpeak-AI — Abstract ASR Provider
========================================
All ASR backends (Whisper, NeMo, Riva) implement this interface.
Switch the active backend by changing ``ASR_PROVIDER`` in ``.env``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class ASRResult:
    """Structured result from any ASR provider."""

    transcript: str                  # raw transcription text
    language: str                    # detected or declared language code
    confidence: float                # 0.0–1.0; -1 if provider doesn't support
    word_timestamps: list[dict]      # [{"word": str, "start": float, "end": float}]
    provider: str                    # name of the backend used


class ASRProvider(ABC):
    """Abstract base class for all ASR backends."""

    @abstractmethod
    def transcribe(self, audio: np.ndarray, sample_rate: int) -> ASRResult:
        """
        Transcribe a mono float32 audio array.

        Args:
            audio:        1-D float32 numpy array, 16 kHz mono.
            sample_rate:  Must be 16,000 Hz.

        Returns:
            :class:`ASRResult` containing transcript and metadata.
        """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable backend identifier."""

    def warm_up(self) -> None:
        """
        Optional: preload model weights before first inference call.
        Override in providers that benefit from eager loading.
        """
