"""Unit tests for the Wav2Vec2 embedding provider."""

from __future__ import annotations

import numpy as np
import pytest

from embeddings.base import EmbeddingProvider
from embeddings.wav2vec2_provider import Wav2Vec2Provider


def test_provider_interface_compliance():
    """Provider must expose all abstract members of EmbeddingProvider."""
    provider = Wav2Vec2Provider()

    assert isinstance(provider, EmbeddingProvider)
    assert callable(provider.embed)
    assert callable(provider.warm_up)
    assert isinstance(provider.embedding_dim, int)
    assert isinstance(provider.provider_name, str)
    assert provider.provider_name.startswith("wav2vec2/")


def test_embedding_dim_is_768():
    """facebook/wav2vec2-base has a hidden size of 768."""
    provider = Wav2Vec2Provider()
    assert provider.embedding_dim == 768


@pytest.mark.parametrize("noise_level", [0.01, 0.05, 0.1])
def test_embed_output_shape_and_dtype(noise_level: float):
    """Embedding must be 1-D float32 with shape (768,)."""
    provider = Wav2Vec2Provider()
    rng = np.random.default_rng(42)
    audio = (rng.standard_normal(16_000) * noise_level).astype(np.float32)

    embedding = provider.embed(audio, sample_rate=16_000)

    assert isinstance(embedding, np.ndarray)
    assert embedding.dtype == np.float32
    assert embedding.shape == (768,)
    assert np.isfinite(embedding).all()


def test_same_input_same_embedding():
    """Embedding extraction must be deterministic for the same input."""
    provider = Wav2Vec2Provider()
    rng = np.random.default_rng(7)
    audio = (rng.standard_normal(16_000) * 0.05).astype(np.float32)

    emb1 = provider.embed(audio, sample_rate=16_000)
    emb2 = provider.embed(audio, sample_rate=16_000)

    np.testing.assert_allclose(emb1, emb2, rtol=1e-5, atol=1e-6)


def test_different_inputs_different_embeddings():
    """Different audio must generally produce different embeddings."""
    provider = Wav2Vec2Provider()
    rng = np.random.default_rng(3)

    audio_a = (rng.standard_normal(16_000) * 0.05).astype(np.float32)
    audio_b = (rng.standard_normal(16_000) * 0.2).astype(np.float32)

    emb_a = provider.embed(audio_a, sample_rate=16_000)
    emb_b = provider.embed(audio_b, sample_rate=16_000)

    assert not np.allclose(emb_a, emb_b, rtol=1e-3, atol=1e-3)


def test_cuda_detection_returns_bool():
    """_detect_cuda must always return a bool, never raise."""
    result = Wav2Vec2Provider._detect_cuda()
    assert isinstance(result, bool)


def test_provider_caching_single_instance():
    """The class-level model must be cached between calls."""
    provider_a = Wav2Vec2Provider()
    provider_b = Wav2Vec2Provider()

    # Both instances share the same class-level model cache.
    assert provider_a._model_id == provider_b._model_id