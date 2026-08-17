"""
NeuroSpeak-AI — Wav2Vec2 Embedding Provider
=============================================
Extracts fixed-length speech embeddings using ``facebook/wav2vec2-base``
via HuggingFace Transformers.

Design:
- Model is lazily loaded and cached as a class-level singleton.
- CUDA is auto-detected; the model and input tensors are moved to GPU
  once and kept there (no per-call CPU/GPU transfers except the final
  result copy).
- Output is a single fixed-length 768-D embedding (mean-pooled over time),
  returned as a numpy float32 array suitable for the severity classifier.
- Falls back to CPU automatically when CUDA is unavailable.
"""

from __future__ import annotations

import numpy as np

from config import config
from embeddings.base import EmbeddingProvider
from utils.logger import get_logger

logger = get_logger(__name__)

_MODEL_ID = "facebook/wav2vec2-base"
_EMBEDDING_DIM = 768  # wav2vec2-base hidden size


class Wav2Vec2Provider(EmbeddingProvider):
    """
    Speech embedding extraction via Wav2Vec2-base.

    Supports CUDA (float16) and CPU (float32) inference with automatic
    device detection. The model is cached at class level to avoid
    repeated loading across instantiations.
    """

    _model = None
    _feature_extractor = None
    _device = None  # torch.device resolved once at load time

    def __init__(self, model_id: str | None = None) -> None:
        self._model_id = model_id or config.wav2vec2_model
        self._use_cuda = self._detect_cuda()
        logger.info(
            "Wav2Vec2Provider initialised | model=%s cuda=%s",
            self._model_id,
            self._use_cuda,
        )

    # ── Device detection ──────────────────────────────────────────────────────

    @staticmethod
    def _detect_cuda() -> bool:
        """Return True if a CUDA device is available."""
        try:
            import torch  # noqa: PLC0415

            return bool(torch.cuda.is_available())
        except ImportError:
            return False

    # ── Interface compliance ──────────────────────────────────────────────────

    @property
    def embedding_dim(self) -> int:
        return _EMBEDDING_DIM

    @property
    def provider_name(self) -> str:
        return f"wav2vec2/{self._model_id}"

    def warm_up(self) -> None:
        """Eagerly load the Wav2Vec2 model and feature extractor."""
        self._get_model()

    # ── Model loading & caching ───────────────────────────────────────────────

    def _get_model(self):
        """Return cached (feature_extractor, model, device) tuple.

        The model is loaded once and stored at class level. The feature
        extractor, model, and resolved torch device are returned together.
        """
        if Wav2Vec2Provider._model is None:
            import torch  # noqa: PLC0415
            from transformers import (  # noqa: PLC0415
                Wav2Vec2FeatureExtractor,
                Wav2Vec2Model,
            )

            logger.info(
                "Loading Wav2Vec2 model '%s' — this may take a moment...",
                self._model_id,
            )

            Wav2Vec2Provider._feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(
                self._model_id,
                return_attention_mask=True,
            )

            model = Wav2Vec2Model.from_pretrained(self._model_id)

            device = torch.device("cuda" if self._detect_cuda() else "cpu")
            model = model.to(device)

            if device.type == "cuda":
                model = model.half()  # float16 on GPU for speed / memory

            model.eval()
            Wav2Vec2Provider._model = model
            Wav2Vec2Provider._device = device

            logger.info(
                "Wav2Vec2 model loaded on %s (compute=%s).",
                device,
                "float16" if device.type == "cuda" else "float32",
            )

        return (
            Wav2Vec2Provider._feature_extractor,
            Wav2Vec2Provider._model,
            Wav2Vec2Provider._device,
        )

    # ── Embedding extraction ──────────────────────────────────────────────────

    def embed(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Extract a mean-pooled 768-D embedding from 16 kHz mono audio.

        Args:
            audio:       1-D float32 array at 16 kHz.
            sample_rate: Must be 16,000 Hz.

        Returns:
            numpy float32 array of shape (768,) suitable for the
            severity classifier.
        """
        import torch  # noqa: PLC0415

        feature_extractor, model, device = self._get_model()

        # Feature extraction on CPU; only the input tensor + model live on GPU.
        inputs = feature_extractor(
            audio,
            sampling_rate=sample_rate,
            return_tensors="pt",
            padding=False,
        )

        input_values = inputs["input_values"].to(device)
        if device.type == "cuda":
            input_values = input_values.half()

        with torch.no_grad():
            outputs = model(input_values)
            # last_hidden_state: (batch=1, time, hidden=768)
            hidden = outputs.last_hidden_state

        # Mean-pool over time → (768,). Transfer to CPU once at the end.
        # np.asarray gives the type checker a concrete ndarray return type.
        embedding: np.ndarray = np.asarray(
            hidden.mean(dim=1).squeeze(0).cpu().float().numpy(),
            dtype=np.float32,
        )

        logger.debug(
            "Wav2Vec2 embedding extracted | shape=%s norm=%.4f",
            embedding.shape,
            float(np.linalg.norm(embedding)),
        )
        return embedding.astype(np.float32)