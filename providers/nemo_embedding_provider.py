"""
NeuroSpeak-AI — NVIDIA NeMo Embedding Provider (Future Stub)
==============================================================
This is an architectural stub for integrating NeMo SpeakerNet models
to extract dysarthric speech embeddings instead of Wav2Vec2.
"""

from __future__ import annotations

import numpy as np

from config import config
from embeddings.base import EmbeddingProvider
from utils.logger import get_logger

logger = get_logger(__name__)


class NemoEmbeddingProvider(EmbeddingProvider):
    """
    NVIDIA NeMo SpeakerNet embedding provider.
    """

    _model = None

    def __init__(self) -> None:
        self._model_path = config.nemo_model_path
        self._device = config.device

        if not self._model_path:
            raise ValueError(
                "NEMO_MODEL_PATH must be set in .env to use NemoEmbeddingProvider."
            )
        logger.info(
            "NemoEmbeddingProvider initialised | path=%s device=%s",
            self._model_path,
            self._device,
        )

    @property
    def embedding_dim(self) -> int:
        return 192  # typical TitaNet / SpeakerNet dimension

    @property
    def provider_name(self) -> str:
        return f"nemo_embed/{self._model_path.split('/')[-1]}"

    def warm_up(self) -> None:
        self._get_model()

    def _get_model(self):
        if NemoEmbeddingProvider._model is None:
            try:
                import nemo.collections.asr as nemo_asr  # noqa: PLC0415
            except ImportError as exc:
                raise ImportError(
                    "nemo_toolkit not found. Install it with: "
                    "pip install nvidia-nemo"
                ) from exc

            logger.info("Loading NeMo SpeakerNet from %s...", self._model_path)
            NemoEmbeddingProvider._model = nemo_asr.models.EncDecSpeakerLabelModel.restore_from(
                self._model_path
            )
            NemoEmbeddingProvider._model.eval()
            if self._device == "cuda":
                NemoEmbeddingProvider._model.cuda()
            logger.info("NeMo SpeakerNet loaded.")

        return NemoEmbeddingProvider._model

    def embed(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        if sample_rate != 16_000:
            logger.warning("NeMo expects 16 kHz input; got %d Hz.", sample_rate)

        model = self._get_model()

        raise NotImplementedError(
            "NemoEmbeddingProvider inference logic is a stub. "
            "Implement forward_pass() or get_embedding() here."
        )

        return np.zeros(self.embedding_dim, dtype=np.float32)
