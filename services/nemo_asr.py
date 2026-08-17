"""
NeuroSpeak-AI — NVIDIA NeMo ASR Service (Experimental)
=========================================================
Loads a pretrained NeMo ASR model, detects CUDA, provides transcription
inference, and measures inference time. This is an EXPERIMENTAL module —
Whisper remains the default ASR provider.

The service implements the same :class:`~asr.base.ASRProvider` interface
so it can be selected via ``ASR_PROVIDER=nemo`` in ``.env`` while keeping
Whisper untouched.

NeMo models are loaded from a ``.nemo`` checkpoint (e.g. Conformer-CTC).
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from asr.base import ASRProvider, ASRResult
from config import config
from utils.logger import get_logger

logger = get_logger(__name__)


def cuda_available() -> bool:
    """Detect NVIDIA CUDA availability."""
    try:
        import torch  # noqa: PLC0415

        return bool(torch.cuda.is_available())
    except ImportError:
        return False


class NemoASRService(ASRProvider):
    """
    NVIDIA NeMo ASR backend (experimental).

    Usage::

        svc = NemoASRService(model_path="path/to/model.nemo")
        result = svc.transcribe(audio, sample_rate=16_000)
    """

    _model = None
    _model_path = ""

    def __init__(self, model_path: str | Path | None = None) -> None:
        self._model_path = str(model_path or config.nemo_model_path)
        if not self._model_path:
            raise ValueError(
                "NemoASRService requires a model path. Set NEMO_MODEL_PATH in .env "
                "or pass model_path= to the constructor."
            )

        self._use_cuda = cuda_available()
        if not self._use_cuda:
            logger.warning(
                "CUDA not detected — NeMo ASR will likely be very slow or fail. "
                "NeMo is designed for NVIDIA GPUs."
            )

        logger.info(
            "NemoASRService initialised | model=%s cuda=%s",
            Path(self._model_path).name,
            self._use_cuda,
        )

    # ── ASRProvider interface ────────────────────────────────────────────────

    @property
    def provider_name(self) -> str:
        return f"nemo/{Path(self._model_path).name}"

    def warm_up(self) -> None:
        """Eagerly load the NeMo model."""
        self._get_model()

    def _get_model(self):
        """Load and cache the NeMo model at class level."""
        if NemoASRService._model is None or NemoASRService._model_path != self._model_path:
            try:
                import nemo.collections.asr as nemo_asr  # noqa: PLC0415
            except ImportError as exc:
                raise ImportError(
                    "nemo_toolkit not installed. "
                    "Install with: pip install nvidia-nemo (requires Linux/GPU)."
                ) from exc

            logger.info("Loading NeMo ASR model from %s...", self._model_path)
            model = nemo_asr.models.EncDecCTCModel.restore_from(self._model_path)
            model.eval()

            if self._use_cuda:
                model.cuda()

            NemoASRService._model = model
            NemoASRService._model_path = self._model_path
            logger.info("NeMo ASR model loaded (cuda=%s).", self._use_cuda)

        return NemoASRService._model

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> ASRResult:
        """
        Transcribe 16 kHz mono audio using the NeMo model.

        Args:
            audio:       1-D float32 array at 16 kHz.
            sample_rate: Must be 16,000 Hz.

        Returns:
            :class:`ASRResult` with transcript and timing info.

        Raises:
            RuntimeError: If NeMo inference fails.
        """
        if sample_rate != 16_000:
            logger.warning("NeMo expects 16 kHz input; got %d Hz.", sample_rate)

        model = self._get_model()

        import torch  # noqa: PLC0415

        t0 = time.perf_counter()

        # NeMo expects a batch of (samples,) float tensors.
        audio_tensor = torch.from_numpy(np.asarray(audio, dtype=np.float32)).unsqueeze(0)
        if self._use_cuda:
            audio_tensor = audio_tensor.cuda()

        with torch.no_grad():
            logits = model(input_signal=audio_tensor, input_signal_length=None)
            transcriptions = model.decoding.decode(logits)

        elapsed = round(time.perf_counter() - t0, 3)

        text = ""
        if transcriptions and transcriptions[0]:
            text = transcriptions[0]
        text = text.strip()

        logger.info(
            "NeMo transcription complete | chars=%d | time=%.3fs",
            len(text),
            elapsed,
        )

        return ASRResult(
            transcript=text,
            language="en",  # NeMo models are typically English-only
            confidence=-1.0,  # CTC models do not expose a native confidence
            word_timestamps=[],
            provider=self.provider_name,
        )