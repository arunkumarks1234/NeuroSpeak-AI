"""
NeuroSpeak-AI — Audio Loader
==============================
Responsible for accepting audio from two sources:
  1. File upload  — a filesystem path to a WAV / MP3 / FLAC file.
  2. Microphone   — a (sample_rate, numpy_array) tuple from Gradio.

Returns a canonical ``AudioInput`` dataclass for downstream processing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

from utils.logger import get_logger

logger = get_logger(__name__)

# Supported inbound sample rates (will be resampled downstream)
_SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".webm"}


@dataclass
class AudioInput:
    """Raw audio loaded from any source, before preprocessing."""

    audio: np.ndarray       # shape: (num_samples,) — always 1-D (mono or mixed)
    sample_rate: int        # original sample rate, Hz
    source: str             # "file" | "microphone"
    original_path: str = ""  # populated only for file uploads


class AudioLoadError(Exception):
    """Raised when audio cannot be loaded."""


def load_from_file(path: str | Path) -> AudioInput:
    """
    Load audio from a file on disk.

    Args:
        path: Absolute or relative path to an audio file.

    Returns:
        :class:`AudioInput` with the raw audio array and sample rate.

    Raises:
        AudioLoadError: If the file does not exist, is not a supported format,
                        or is silent / zero-length.
    """
    path = Path(path)

    if not path.exists():
        raise AudioLoadError(f"Audio file not found: {path}")

    if path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
        raise AudioLoadError(
            f"Unsupported audio format '{path.suffix}'. "
            f"Supported: {', '.join(_SUPPORTED_EXTENSIONS)}"
        )

    logger.info("Loading audio from file: %s", path.name)

    try:
        audio, sr = sf.read(str(path), always_2d=False, dtype="float32")
    except Exception as exc:
        # Fallback: try librosa which handles more codecs via ffmpeg
        try:
            import librosa  # noqa: PLC0415
            audio, sr = librosa.load(str(path), sr=None, mono=False, dtype=np.float32)
            if audio.ndim == 2:
                audio = audio.T  # librosa returns (channels, samples)
        except Exception as lib_exc:
            raise AudioLoadError(
                f"Could not decode '{path.name}': {exc}; librosa: {lib_exc}"
            ) from exc

    # Collapse to mono by averaging channels if multi-channel
    if audio.ndim == 2:
        logger.debug("Converting %d-channel audio to mono.", audio.shape[1])
        audio = audio.mean(axis=1)

    if audio.size == 0:
        raise AudioLoadError(f"Audio file is empty: {path.name}")

    logger.debug(
        "Loaded: %d samples @ %d Hz (%.2f s).",
        audio.size,
        sr,
        audio.size / sr,
    )
    return AudioInput(
        audio=audio,
        sample_rate=sr,
        source="file",
        original_path=str(path),
    )


def load_from_microphone(
    sample_rate: int,
    audio_array: np.ndarray,
) -> AudioInput:
    """
    Wrap a microphone recording from Gradio into an ``AudioInput``.

    Gradio's ``gr.Audio(type="numpy")`` returns ``(sample_rate, np.ndarray)``
    where the array has dtype int16 with shape ``(samples,)`` or
    ``(samples, channels)``.

    Args:
        sample_rate:  Sample rate reported by Gradio.
        audio_array:  Raw PCM array from Gradio microphone widget.

    Returns:
        :class:`AudioInput` normalised to float32 mono.

    Raises:
        AudioLoadError: If the input array is empty.
    """
    if audio_array is None or audio_array.size == 0:
        raise AudioLoadError("Microphone recording is empty — please try again.")

    logger.info("Receiving microphone input @ %d Hz.", sample_rate)

    # Gradio returns int16; normalise to [-1, 1] float32
    if audio_array.dtype != np.float32:
        audio_array = audio_array.astype(np.float32)
        if audio_array.max() > 1.0:
            audio_array /= 32768.0  # int16 max

    # Collapse multi-channel
    if audio_array.ndim == 2:
        logger.debug("Collapsing %d-channel mic input to mono.", audio_array.shape[1])
        audio_array = audio_array.mean(axis=1)

    logger.debug(
        "Mic input: %d samples @ %d Hz (%.2f s).",
        audio_array.size,
        sample_rate,
        audio_array.size / sample_rate,
    )
    return AudioInput(audio=audio_array, sample_rate=sample_rate, source="microphone")
