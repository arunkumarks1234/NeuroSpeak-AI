"""
NeuroSpeak-AI — NVIDIA Riva ASR Provider (Future Stub)
========================================================
This is an architectural stub for integrating NVIDIA Riva ASR.
To use this:
  1. Deploy a Riva Server instance (e.g. via Triton Inference Server)
  2. Install the client (``pip install nvidia-riva-client``)
  3. Set ``ASR_PROVIDER=riva`` in ``.env``
  4. Set ``RIVA_URI=localhost:50051`` in ``.env``
"""

from __future__ import annotations

import numpy as np

from asr.base import ASRProvider, ASRResult
from config import config
from utils.logger import get_logger

logger = get_logger(__name__)


class RivaASRProvider(ASRProvider):
    """
    NVIDIA Riva gRPC ASR client.

    Sends audio to a remote Riva server for high-performance inference.
    """

    def __init__(self) -> None:
        self._uri = config.riva_uri
        self._use_ssl = config.riva_use_ssl
        self._auth = None
        self._service = None

        if not self._uri:
            raise ValueError("RIVA_URI must be set in .env to use RivaASRProvider.")

        logger.info(
            "RivaASRProvider initialised | uri=%s ssl=%s",
            self._uri,
            self._use_ssl,
        )

    @property
    def provider_name(self) -> str:
        return f"riva/{self._uri}"

    def warm_up(self) -> None:
        """Establish the gRPC connection."""
        self._get_service()

    def _get_service(self):
        """Lazy-load the Riva gRPC client and establish connection."""
        if self._service is None:
            try:
                import riva.client  # noqa: PLC0415
            except ImportError as exc:
                raise ImportError(
                    "nvidia-riva-client not found. Install it with: "
                    "pip install nvidia-riva-client"
                ) from exc

            logger.info("Connecting to Riva server at %s...", self._uri)
            self._auth = riva.client.Auth(uri=self._uri, use_ssl=self._use_ssl)
            self._service = riva.client.ASRService(self._auth)
            logger.info("Riva connection established.")

        return self._service

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> ASRResult:
        """
        Transcribe audio using the remote Riva server.
        """
        if sample_rate != 16_000:
            logger.warning("Riva expects 16 kHz input; got %d Hz.", sample_rate)

        service = self._get_service()
        import riva.client  # noqa: PLC0415

        # Riva expects PCM audio (int16 usually)
        # Convert float32 [-1, 1] to int16
        audio_int16 = (audio * 32767).astype(np.int16)

        config = riva.client.RecognitionConfig(
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
            sample_rate_hertz=sample_rate,
            language_code="en-US",
            max_alternatives=1,
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
        )

        logger.info("Sending %d samples to Riva...", audio_int16.size)

        raise NotImplementedError(
            "RivaASRProvider inference logic is a stub. "
            "Implement offline_recognize() here."
        )

        # Example implementation:
        # response = service.offline_recognize(audio_int16.tobytes(), config)
        # ... parse response ...

        return ASRResult(
            transcript="[Riva transcript stub]",
            language="en-US",
            confidence=-1.0,
            word_timestamps=[],
            provider=self.provider_name,
        )
