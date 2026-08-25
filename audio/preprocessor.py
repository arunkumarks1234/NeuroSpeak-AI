"""
NeuroSpeak-AI — Audio Preprocessor
=====================================
Converts any AudioInput into a standardised representation:
  - Sample rate: 16,000 Hz (required by Whisper and Wav2Vec2)
  - Channels:    Mono (1-D numpy array)
  - Dtype:       float32, normalised to [-1, 1]
  - Silence:     Leading/trailing silence trimmed

Provides waveform information (peak amplitude, RMS energy, zero-crossing rate).
Supports GPU acceleration using Torchaudio for resampling where appropriate.
Returns a ``ProcessedAudio`` dataclass used by all downstream layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from audio.loader import AudioInput
from config import config
from utils.logger import get_logger

logger = get_logger(__name__)

TARGET_SAMPLE_RATE = 16_000  # Hz — required by Whisper + Wav2Vec2
_TRIM_TOP_DB = 30            # dB below peak for silence trimming


@dataclass
class ProcessedAudio:
    """Preprocessed audio ready for ASR and feature extraction."""

    audio: np.ndarray       # float32, mono, 16 kHz
    sample_rate: int        # always 16_000
    duration_seconds: float
    original_sample_rate: int
    was_resampled: bool
    source: str             # "file" | "microphone"
    waveform_info: dict = field(default_factory=dict)
    original_path: str = ""


class AudioPreprocessError(Exception):
    """Raised when preprocessing fails."""


def preprocess(audio_input: AudioInput) -> ProcessedAudio:
    """
    Preprocess an :class:`~audio.loader.AudioInput` to 16 kHz mono float32.

    Processing steps:
      1. Resample to 16 kHz (if needed) using torchaudio (if CUDA) or librosa.
      2. Normalise amplitude to [-1, 1].
      3. Trim leading/trailing silence.
      4. Guard against near-silent or too-short recordings.
      5. Calculate waveform information metrics.

    Args:
        audio_input: Raw audio from the loader.

    Returns:
        :class:`ProcessedAudio` ready for ASR.

    Raises:
        AudioPreprocessError: If audio is too short or silent after trimming.
    """
    audio = audio_input.audio.copy()
    sr = audio_input.sample_rate
    was_resampled = False

    # ── Step 1: Resample ─────────────────────────────────────────────────────
    if sr != TARGET_SAMPLE_RATE:
        logger.info("Resampling from %d Hz -> %d Hz.", sr, TARGET_SAMPLE_RATE)
        
        # Try GPU acceleration via Torchaudio if configured for CUDA
        if config.device == "cuda":
            try:
                import torch  # noqa: PLC0415
                import torchaudio.functional as F  # noqa: PLC0415
                
                device = torch.device("cuda")
                # Torchaudio resample expects shape (channels, time)
                audio_tensor = torch.from_numpy(audio).unsqueeze(0).to(device)
                audio_tensor = F.resample(audio_tensor, sr, TARGET_SAMPLE_RATE)
                audio = audio_tensor.squeeze(0).cpu().numpy()
                was_resampled = True
                logger.debug("Resampled using torchaudio on CUDA.")
            except ImportError:
                logger.debug("torchaudio not found or failed; falling back to librosa.")
        
        # Fallback to librosa CPU resampling
        if not was_resampled:
            import librosa  # noqa: PLC0415
            audio = librosa.resample(
                audio,
                orig_sr=sr,
                target_sr=TARGET_SAMPLE_RATE,
                res_type="kaiser_best",
            )
            was_resampled = True
            logger.debug("Resampled using librosa on CPU.")

        sr = TARGET_SAMPLE_RATE

    # ── Step 2: Normalise ────────────────────────────────────────────────────
    peak = np.abs(audio).max()
    if peak < 1e-6:
        raise AudioPreprocessError(
            "Audio appears to be silent (peak amplitude < 1e-6). "
            "Please check your microphone or upload a different file."
        )
    audio = audio / peak

    # ── Step 3: Trim silence ─────────────────────────────────────────────────
    import librosa  # noqa: PLC0415
    audio_trimmed, _ = librosa.effects.trim(audio, top_db=_TRIM_TOP_DB)

    if audio_trimmed.size < sr * 0.2:  # less than 0.2 seconds after trim
        logger.warning(
            "Audio is very short after trimming (%.2f s). "
            "Using untrimmed version.",
            audio_trimmed.size / sr,
        )
        audio_trimmed = audio  # fall back to untrimmed

    # ── Step 4: Final guard ──────────────────────────────────────────────────
    duration = audio_trimmed.size / sr
    if duration < 0.1:
        raise AudioPreprocessError(
            f"Audio too short ({duration:.2f} s). "
            "Minimum duration is 0.1 s."
        )

    # ── Step 5: Waveform info extraction ──────────────────────────────────────
    rms_energy = float(np.sqrt(np.mean(audio_trimmed**2)))
    zero_crossings = float(np.sum(np.abs(np.diff(np.sign(audio_trimmed)))))
    zcr = zero_crossings / audio_trimmed.size
    
    waveform_info = {
        "peak_amplitude": float(np.abs(audio_trimmed).max()),
        "rms_energy": rms_energy,
        "zero_crossing_rate": zcr,
    }

    logger.info(
        "Preprocessed audio: %.2f s @ %d Hz | resampled=%s | rms=%.4f",
        duration,
        sr,
        was_resampled,
        rms_energy,
    )

    return ProcessedAudio(
        audio=audio_trimmed.astype(np.float32),
        sample_rate=sr,
        duration_seconds=duration,
        original_sample_rate=audio_input.sample_rate,
        was_resampled=was_resampled,
        source=audio_input.source,
        waveform_info=waveform_info,
        original_path=audio_input.original_path,
    )
