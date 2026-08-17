"""
NeuroSpeak-AI — Device Detection Utility
==========================================
Centralises CUDA / MPS / CPU detection and device-placement helpers.
"""

from __future__ import annotations

from typing import Literal

from utils.logger import get_logger

logger = get_logger(__name__)


def get_torch_device() -> "torch.device":  # noqa: F821
    """Return the best available ``torch.device``."""
    import torch  # noqa: PLC0415

    if torch.cuda.is_available():
        dev = torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        dev = torch.device("mps")
    else:
        dev = torch.device("cpu")

    logger.debug("Torch device selected: %s", dev)
    return dev


def get_device_string() -> Literal["cuda", "mps", "cpu"]:
    """Return device as a plain string, matching the config convention."""
    try:
        dev = get_torch_device()
        return dev.type  # type: ignore[return-value]
    except ImportError:
        logger.warning("PyTorch not found — defaulting to CPU.")
        return "cpu"


def cuda_info() -> dict[str, object]:
    """Return a dict of CUDA device info for logging / UI display."""
    try:
        import torch  # noqa: PLC0415

        if not torch.cuda.is_available():
            return {"available": False}
        return {
            "available": True,
            "device_count": torch.cuda.device_count(),
            "current_device": torch.cuda.current_device(),
            "device_name": torch.cuda.get_device_name(0),
            "total_memory_gb": round(
                torch.cuda.get_device_properties(0).total_memory / 1e9, 2
            ),
        }
    except ImportError:
        return {"available": False, "error": "torch not installed"}
