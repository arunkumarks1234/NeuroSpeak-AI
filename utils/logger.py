"""
NeuroSpeak-AI — Structured Logger
===================================
Provides a rich-formatted console logger and a rotating file handler.
Import `get_logger` everywhere instead of using `logging` directly.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

try:
    from rich.logging import RichHandler
    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False

_LOG_DIR = Path("./logs")
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "neurospeak.log"

_CONFIGURED: set[str] = set()


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Return a named logger with rich console output and rotating file handler.

    Args:
        name:  Logger name, typically ``__name__`` of the calling module.
        level: Log level (default: INFO).

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)

    if name in _CONFIGURED:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # ── Console handler ──────────────────────────────────────────────────────
    if _RICH_AVAILABLE:
        console_handler: logging.Handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_path=False,
        )
        console_fmt = "%(message)s"
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_fmt = "[%(asctime)s] [%(levelname)s] %(name)s — %(message)s"

    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(console_fmt, datefmt="%H:%M:%S"))
    logger.addHandler(console_handler)

    # ── Rotating file handler ─────────────────────────────────────────────────
    file_handler = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB per file
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(file_handler)

    _CONFIGURED.add(name)
    return logger
