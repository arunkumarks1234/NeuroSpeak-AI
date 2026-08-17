"""
NeuroSpeak-AI — Central Configuration
======================================
Reads all settings from environment variables / .env file.
This is the single source of truth for every tunable parameter.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

# Load .env from project root (if it exists)
_PROJECT_ROOT = Path(__file__).parent
load_dotenv(_PROJECT_ROOT / ".env", override=False)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _env_bool(key: str, default: bool = False) -> bool:
    return _env(key, str(default)).lower() in ("1", "true", "yes")


def _env_int(key: str, default: int = 0) -> int:
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default


def _env_float(key: str, default: float = 0.0) -> float:
    try:
        return float(_env(key, str(default)))
    except ValueError:
        return default


def _resolve_device(requested: str) -> Literal["cuda", "mps", "cpu"]:
    """Auto-detect best available compute device."""
    if requested not in ("auto", "cuda", "mps", "cpu"):
        requested = "auto"

    if requested != "auto":
        return requested  # type: ignore[return-value]

    try:
        import torch  # noqa: PLC0415

        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


def _resolve_compute_type(requested: str, device: str) -> str:
    """Select CTranslate2 compute type based on device."""
    if requested != "auto":
        return requested
    return "float16" if device == "cuda" else "int8"


# ─────────────────────────────────────────────────────────────────────────────
# Provider Registry
# ─────────────────────────────────────────────────────────────────────────────

# Maps provider string names → (module_path, class_name)
# This allows switching backends by changing a single .env value.
ASR_PROVIDER_REGISTRY: dict[str, tuple[str, str]] = {
    "whisper": ("asr.whisper_provider", "WhisperProvider"),
    "nemo":    ("providers.nemo_asr_provider", "NemoASRProvider"),
    "riva":    ("providers.riva_asr_provider", "RivaASRProvider"),
}

EMBEDDING_PROVIDER_REGISTRY: dict[str, tuple[str, str]] = {
    "wav2vec2": ("embeddings.wav2vec2_provider", "Wav2Vec2Provider"),
    "nemo":     ("providers.nemo_embedding_provider", "NemoEmbeddingProvider"),
}


# ─────────────────────────────────────────────────────────────────────────────
# Config Dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class NeuroSpeakConfig:
    # ── Compute ──
    device: Literal["cuda", "mps", "cpu"]
    compute_type: str  # float16 / int8 / float32

    # ── ASR ──
    asr_provider: str
    whisper_model: str
    wav2vec2_model: str
    embedding_provider: str

    # ── Severity classifier backend ──
    severity_classifier: str  # "heuristic" | "ml"
    severity_model_path: Path  # path to serialised ML classifier (optional)

    # ── Agents ──
    ollama_host: str
    qwen_model: str
    llama_model: str
    ollama_timeout: int
    max_refine_rounds: int
    words_per_second_limit: float
    max_expected_wps: float  # hallucination guard upper bound (default 3.5)

    # ── Storage ──
    database_url: str
    data_dir: Path

    # ── Config files ──
    phonetic_shield_path: Path
    coaching_prompt_path: Path
    coaching_num_recommendations: int

    # ── Gradio ──
    gradio_server_name: str
    gradio_server_port: int
    gradio_share: bool

    # ── Severity thresholds ──
    severity_mild_max: float
    severity_moderate_max: float

    # ── Future: NeMo / Riva ──
    nemo_model_path: str
    riva_uri: str
    riva_use_ssl: bool

    # ── Registry references (not env-sourced) ──
    asr_registry: dict[str, tuple[str, str]] = field(
        default_factory=lambda: ASR_PROVIDER_REGISTRY
    )
    embedding_registry: dict[str, tuple[str, str]] = field(
        default_factory=lambda: EMBEDDING_PROVIDER_REGISTRY
    )


def _build_config() -> NeuroSpeakConfig:
    raw_device = _env("DEVICE", "auto")
    device = _resolve_device(raw_device)
    raw_compute = _env("WHISPER_COMPUTE_TYPE", "auto")
    compute_type = _resolve_compute_type(raw_compute, device)

    data_dir = Path(_env("DATA_DIR", "./data")).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

    return NeuroSpeakConfig(
        # Compute
        device=device,
        compute_type=compute_type,
        # ASR
        asr_provider=_env("ASR_PROVIDER", "whisper"),
        whisper_model=_env("WHISPER_MODEL", "large-v3"),
        wav2vec2_model=_env("WAV2VEC2_MODEL", "facebook/wav2vec2-base"),
        embedding_provider=_env("EMBEDDING_PROVIDER", "wav2vec2"),
        # Severity classifier backend
        severity_classifier=_env("SEVERITY_CLASSIFIER", "heuristic"),
        severity_model_path=Path(
            _env("SEVERITY_MODEL_PATH", "./ml_models/severity_model.joblib")
        ),
        # Agents
        ollama_host=_env("OLLAMA_HOST", "http://localhost:11434"),
        qwen_model=_env("QWEN_MODEL", "qwen2.5"),
        llama_model=_env("LLAMA_MODEL", "llama3.1"),
        ollama_timeout=_env_int("OLLAMA_TIMEOUT", 60),
        max_refine_rounds=_env_int("MAX_REFINE_ROUNDS", 2),
        words_per_second_limit=_env_float("WORDS_PER_SECOND_LIMIT", 3.5),
        max_expected_wps=_env_float("MAX_EXPECTED_WPS", 3.5),
        # Storage
        database_url=_env("DATABASE_URL", "sqlite:///./data/sessions.db"),
        data_dir=data_dir,
        # Config files
        phonetic_shield_path=Path(
            _env("PHONETIC_SHIELD_PATH", "./config/phonetic_shield.json")
        ),
        coaching_prompt_path=Path(
            _env("COACHING_PROMPT_PATH", "./config/coaching_prompt.txt")
        ),
        coaching_num_recommendations=_env_int("COACHING_NUM_RECOMMENDATIONS", 4),
        # Gradio
        gradio_server_name=_env("GRADIO_SERVER_NAME", "0.0.0.0"),
        gradio_server_port=_env_int("GRADIO_SERVER_PORT", 7860),
        gradio_share=_env_bool("GRADIO_SHARE", False),
        # Severity
        severity_mild_max=_env_float("SEVERITY_MILD_MAX", 0.33),
        severity_moderate_max=_env_float("SEVERITY_MODERATE_MAX", 0.66),
        # Future integrations
        nemo_model_path=_env("NEMO_MODEL_PATH", ""),
        riva_uri=_env("RIVA_URI", "localhost:50051"),
        riva_use_ssl=_env_bool("RIVA_USE_SSL", False),
    )


# Module-level singleton — import this everywhere
config = _build_config()