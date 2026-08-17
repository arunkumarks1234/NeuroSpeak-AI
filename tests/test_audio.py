from __future__ import annotations

import numpy as np

from audio.loader import AudioInput, load_from_microphone, AudioLoadError
from audio.preprocessor import preprocess, AudioPreprocessError
import pytest


def test_load_microphone_valid():
    sr = 48000
    arr = np.ones(48000, dtype=np.int16)
    audio_input = load_from_microphone(sr, arr)

    assert isinstance(audio_input, AudioInput)
    assert audio_input.source == "microphone"
    assert audio_input.sample_rate == 48000
    assert audio_input.audio.dtype == np.float32


def test_load_microphone_empty():
    sr = 48000
    arr = np.array([], dtype=np.int16)
    with pytest.raises(AudioLoadError, match="empty"):
        load_from_microphone(sr, arr)


def test_preprocess_resamples_and_extracts_info():
    # 1 second of 48kHz audio, with a simple sine wave to avoid silence
    t = np.linspace(0, 1, 48000, False)
    # Sine wave at 440 Hz
    wave = np.sin(2 * np.pi * 440 * t) * 0.5
    
    audio_input = AudioInput(
        audio=wave.astype(np.float32),
        sample_rate=48000,
        source="test",
    )

    processed = preprocess(audio_input)

    assert processed.sample_rate == 16000
    assert processed.was_resampled is True
    assert 0.8 < processed.duration_seconds <= 1.1
    
    # Check waveform info
    assert "peak_amplitude" in processed.waveform_info
    assert "rms_energy" in processed.waveform_info
    assert "zero_crossing_rate" in processed.waveform_info
    
    assert processed.waveform_info["peak_amplitude"] == pytest.approx(1.0, rel=1e-3)
    assert processed.waveform_info["rms_energy"] > 0


def test_preprocess_silent_audio():
    audio_input = AudioInput(
        audio=np.zeros(16000, dtype=np.float32),
        sample_rate=16000,
        source="test",
    )

    with pytest.raises(AudioPreprocessError, match="silent"):
        preprocess(audio_input)


def test_preprocess_too_short():
    # 0.05 seconds of audio
    wave = np.ones(800, dtype=np.float32)
    audio_input = AudioInput(
        audio=wave,
        sample_rate=16000,
        source="test",
    )

    with pytest.raises(AudioPreprocessError, match="short"):
        preprocess(audio_input)
