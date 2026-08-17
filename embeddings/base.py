"""
NeuroSpeak-AI — Abstract Embedding Provider
=============================================
Wav2Vec2, NeMo SpeakerNet, or any future provider implements this ABC.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class EmbeddingProvider(ABC):
    """Abstract interface for speech embedding extraction."""

    @abstractmethod
    def embed(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Extract a fixed-length embedding vector from a mono 16 kHz audio array.

        Args:
            audio:       1-D float32 array at 16 kHz.
            sample_rate: Must be 16,000 Hz.

        Returns:
            1-D float32 numpy array (embedding vector).
        """

    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Dimensionality of the output embedding vector."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable backend identifier."""

    def warm_up(self) -> None:
        """Optional: eagerly load model weights before first call."""
