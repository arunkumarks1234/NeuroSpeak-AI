"""
NeuroSpeak-AI — Acoustic Feature Extractor
============================================
Extracts three key acoustic features from a preprocessed speech signal:

  Feature                  Method              Library
  ───────────────────────  ──────────────────  ──────────
  Average pitch (F0, Hz)   Autocorrelation     parselmouth (Praat)
  Pitch standard dev. (Hz) Same as above       parselmouth
  Pause-to-speech ratio    RMS energy gate     librosa
  Spectral centroid (Hz)   Power spectrum      librosa

These features are used by:
  - HeuristicSeverityClassifier
  - CoachingEngine (context for recommendations)
  - SessionRecord (stored for longitudinal tracking)

``parselmouth`` wraps the Praat acoustic analysis engine.
Falls back gracefully to ``librosa`` pitch estimation if parselmouth is
not installed (less accurate for pathological speech).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)

_SR = 16_000  # All input expected at 16 kHz
_SILENCE_FRAME_DB = -40.0   # RMS threshold (dB) for silence detection
_PRAAT_PITCH_FLOOR = 50.0   # Hz — minimum F0 (covers low male voices)
_PRAAT_PITCH_CEILING = 600.0  # Hz — maximum F0 (covers high female/child voices)


@dataclass
class AcousticFeatures:
    """Extracted acoustic measurements for one utterance."""

    avg_pitch_hz: float          # Mean fundamental frequency (F0)
    pitch_sd_hz: float           # Standard deviation of F0 (prosodic variability)
    pause_duration_sec: float    # Total silence duration
    pause_ratio: float           # pause_duration / total_duration
    spectral_centroid_hz: float  # Mean spectral centroid (brightness measure)
    duration_sec: float          # Total utterance duration
    extraction_method: str       # "praat" | "librosa_fallback"

    def to_dict(self) -> dict:
        return {
            "avg_pitch_hz": round(self.avg_pitch_hz, 2),
            "pitch_sd_hz": round(self.pitch_sd_hz, 2),
            "pause_duration_sec": round(self.pause_duration_sec, 3),
            "pause_ratio": round(self.pause_ratio, 4),
            "spectral_centroid_hz": round(self.spectral_centroid_hz, 2),
            "duration_sec": round(self.duration_sec, 3),
            "extraction_method": self.extraction_method,
        }


class AcousticExtractor:
    """
    Extracts acoustic features from 16 kHz mono float32 audio.

    Usage::

        extractor = AcousticExtractor()
        features = extractor.extract(audio_array, sample_rate=16000)
    """

    def extract(self, audio: np.ndarray, sample_rate: int) -> AcousticFeatures:
        """
        Extract acoustic features from a mono audio array.

        Args:
            audio:       1-D float32 numpy array.
            sample_rate: Sample rate in Hz (expected: 16000).

        Returns:
            :class:`AcousticFeatures` dataclass.
        """
        duration = audio.size / sample_rate

        pitch_values = self._extract_pitch(audio, sample_rate)
        pause_duration, pause_ratio = self._extract_pauses(audio, sample_rate, duration)
        centroid = self._extract_spectral_centroid(audio, sample_rate)
        method = "praat" if self._praat_available() else "librosa_fallback"

        valid_pitches = pitch_values[pitch_values > 0]
        if valid_pitches.size == 0:
            avg_pitch = 0.0
            pitch_sd = 0.0
        else:
            avg_pitch = float(np.mean(valid_pitches))
            pitch_sd = float(np.std(valid_pitches))

        logger.info(
            "Acoustics | pitch=%.1f±%.1f Hz | pause_ratio=%.2f | centroid=%.0f Hz | dur=%.2fs",
            avg_pitch,
            pitch_sd,
            pause_ratio,
            centroid,
            duration,
        )

        return AcousticFeatures(
            avg_pitch_hz=avg_pitch,
            pitch_sd_hz=pitch_sd,
            pause_duration_sec=pause_duration,
            pause_ratio=pause_ratio,
            spectral_centroid_hz=centroid,
            duration_sec=duration,
            extraction_method=method,
        )

    # ── Private methods ───────────────────────────────────────────────────────

    @staticmethod
    def _praat_available() -> bool:
        try:
            import parselmouth  # noqa: F401, PLC0415
            return True
        except ImportError:
            return False

    def _extract_pitch(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Extract frame-level F0 values (Hz). Returns 0 for unvoiced frames."""
        if self._praat_available():
            return self._pitch_praat(audio, sr)
        return self._pitch_librosa(audio, sr)

    @staticmethod
    def _pitch_praat(audio: np.ndarray, sr: int) -> np.ndarray:
        """Use Praat (via parselmouth) for accurate pathological speech pitch."""
        import parselmouth  # noqa: PLC0415

        snd = parselmouth.Sound(audio.astype(np.float64), sampling_frequency=sr)
        pitch = snd.to_pitch(
            time_step=0.01,
            pitch_floor=_PRAAT_PITCH_FLOOR,
            pitch_ceiling=_PRAAT_PITCH_CEILING,
        )
        values = pitch.selected_array["frequency"]  # 0 = unvoiced frame
        return values.astype(np.float32)

    @staticmethod
    def _pitch_librosa(audio: np.ndarray, sr: int) -> np.ndarray:
        """Fallback pitch extraction using librosa pyin (less accurate)."""
        import librosa  # noqa: PLC0415

        f0, voiced_flag, _ = librosa.pyin(
            audio,
            fmin=_PRAAT_PITCH_FLOOR,
            fmax=_PRAAT_PITCH_CEILING,
            sr=sr,
        )
        f0 = np.nan_to_num(f0, nan=0.0)
        return f0.astype(np.float32)

    @staticmethod
    def _extract_pauses(
        audio: np.ndarray, sr: int, duration: float
    ) -> tuple[float, float]:
        """Measure total silence duration using RMS energy gating."""
        import librosa  # noqa: PLC0415

        hop_length = 512
        rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=hop_length)[0]
        rms_db = librosa.amplitude_to_db(rms, ref=np.max(rms) + 1e-9)

        silence_frames = np.sum(rms_db < _SILENCE_FRAME_DB)
        frame_duration = hop_length / sr
        pause_duration = float(silence_frames * frame_duration)
        pause_ratio = float(np.clip(pause_duration / (duration + 1e-9), 0.0, 1.0))

        return pause_duration, pause_ratio

    @staticmethod
    def _extract_spectral_centroid(audio: np.ndarray, sr: int) -> float:
        """Compute mean spectral centroid (brightness of the signal in Hz)."""
        import librosa  # noqa: PLC0415

        centroid = librosa.feature.spectral_centroid(y=audio, sr=sr, hop_length=512)
        return float(np.mean(centroid))
