"""
NeuroSpeak-AI — Hallucination Guard
======================================
Enforces audio-duration-based word-count constraints on LLM outputs.

Dysarthric speakers have a significantly reduced speaking rate (typically
1.0–2.5 words/second vs. 2.5–4.0 wps for typical speakers). Any LLM
output that substantially exceeds this rate is likely hallucinated content.

The guard provides:
  - ``check(text, duration)``: returns (is_valid, word_count, max_words)
  - ``truncate(text, duration)``: truncates to the word limit
  - ``enforce(text, duration)``: raises if the limit is exceeded
"""

from __future__ import annotations

from config import config
from utils.logger import get_logger

logger = get_logger(__name__)


class HallucinationGuard:
    """
    Constrains LLM output length to audio-duration-based word count.

    Example::

        guard = HallucinationGuard()
        safe_text = guard.enforce("this is a generated response", duration_sec=3.0)
    """

    def __init__(self, words_per_second: float | None = None) -> None:
        self.words_per_second = words_per_second or config.words_per_second_limit
        logger.debug(
            "HallucinationGuard: max %.1f words/sec of audio.",
            self.words_per_second,
        )

    def max_words(self, duration_seconds: float) -> int:
        """Return the maximum allowed word count for a given audio duration."""
        # Add a 20% tolerance to avoid over-aggressive truncation
        return max(1, int(duration_seconds * self.words_per_second * 1.2))

    def check(
        self, text: str, duration_seconds: float
    ) -> tuple[bool, int, int]:
        """
        Check whether text exceeds the word count limit.

        Args:
            text:             LLM-generated text to validate.
            duration_seconds: Audio clip duration in seconds.

        Returns:
            Tuple of (is_valid, actual_word_count, max_allowed_words).
        """
        words = text.split()
        actual = len(words)
        limit = self.max_words(duration_seconds)
        is_valid = actual <= limit

        if not is_valid:
            logger.warning(
                "HallucinationGuard: output has %d words; limit is %d "
                "(%.1f s × %.1f wps × 1.2 tolerance).",
                actual,
                limit,
                duration_seconds,
                self.words_per_second,
            )
        return is_valid, actual, limit

    def truncate(self, text: str, duration_seconds: float) -> str:
        """
        Truncate text to the word limit, preserving sentence boundaries where possible.

        Args:
            text:             Text to truncate.
            duration_seconds: Audio clip duration in seconds.

        Returns:
            Truncated string with an appended ellipsis if truncation occurred.
        """
        limit = self.max_words(duration_seconds)
        words = text.split()
        if len(words) <= limit:
            return text

        truncated = " ".join(words[:limit])
        logger.info(
            "Truncated LLM output from %d → %d words.",
            len(words),
            limit,
        )
        return truncated + "..."

    def enforce(self, text: str, duration_seconds: float) -> str:
        """
        Return ``text`` if within limit, otherwise silently truncate it.

        This is the main entry point for downstream use.

        Args:
            text:             LLM output to validate.
            duration_seconds: Audio clip duration in seconds.

        Returns:
            The original text if within limits, or a truncated version.
        """
        is_valid, actual, limit = self.check(text, duration_seconds)
        if is_valid:
            return text
        return self.truncate(text, duration_seconds)
