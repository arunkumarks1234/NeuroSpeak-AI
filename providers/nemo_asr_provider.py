"""
NeuroSpeak-AI — NVIDIA NeMo ASR Provider (Future Stub)
========================================================
This is an architectural stub for integrating NVIDIA NeMo ASR.
To use this:
  1. Install NeMo (``pip install nemo_toolkit[asr]``)
  2. Download a `.nemo` model checkpoint (e.g. Conformer-CTC)
  3. Set ``ASR_PROVIDER=nemo`` in ``.env``
  4. Set ``NEMO_MODEL_PATH=/path/to/model.nemo`` in ``.env``
"""

from __future__ import annotations

import numpy as np

from asr.base import ASRProvider, ASRResult
from config import config
from utils.logger import get_logger

logger = get_logger(__name__)


class NemoASRProvider(ASRProvider):
    """
    NVIDIA NeMo ASR backend.

    Requires ``nvidia-nemo`` to be installed and a GPU for inference.
    """

    _model = None

    def __init__(self) -> None:
        self._model_path = config.nemo_model_path
        self._device = config.device

        if not self._model_path:
            raise ValueError(
                "NEMO_MODEL_PATH must be set in .env to use NemoASRProvider."
            )
        if self._device != "cuda":
            logger.warning(
                "NemoASRProvider typically requires a CUDA GPU. Device is '%s'.",
                self._device,
            )

        logger.info(
            "NemoASRProvider initialised | path=%s device=%s",
            self._model_path,
            self._device,
        )

    @property
    def provider_name(self) -> str:
        return f"nemo/{self._model_path.split('/')[-1]}"

    def warm_up(self) -> None:
        self._get_model()

    def _get_model(self):
        if NemoASRProvider._model is None:
            try:
                import nemo.collections.asr as nemo_asr  # noqa: PLC0415
            except ImportError as exc:
                raise ImportError(
                    "nemo_toolkit not found. Install it with: "
                    "pip install nvidia-nemo (requires Linux/GPU)."
                ) from exc

            logger.info("Loading NeMo ASR model from %s...", self._model_path)
            NemoASRProvider._model = nemo_asr.models.EncDecCTCModel.restore_from(
                self._model_path
            )
            # Switch to inference mode and map to device
            NemoASRProvider._model.eval()
            if self._device == "cuda":
                NemoASRProvider._model.cuda()
            logger.info("NeMo ASR model loaded.")

        return NemoASRProvider._model

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> ASRResult:
        """
        Transcribe audio using the NeMo model.
        """
        if sample_rate != 16_000:
            logger.warning("NeMo expects 16 kHz input; got %d Hz.", sample_rate)

        model = self._get_model()

        # NeMo models typically expect a batched PyTorch tensor
        # In a real implementation, you'd write a temporary WAV or use the DataLoader API
        # For this stub, we demonstrate the direct inference API:
        # transcriptions = model.transcribe(paths2audio_files=["temp.wav"], batch_size=1)

        raise NotImplementedError(
            "NemoASRProvider inference logic is a stub. "
            "Implement batched PyTorch tensor decoding here."
        )

        return ASRResult(
            transcript="[NeMo transcript stub]",
            language="en",
            confidence=-1.0,
            word_timestamps=[],
            provider=self.provider_name,
        )
