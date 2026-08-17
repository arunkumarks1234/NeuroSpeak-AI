"""
NeuroSpeak-AI — Phonetic Shield
=================================
Post-ASR correction layer designed specifically for dysarthric speech.

Two-pass approach:
  Pass 1 — Word-level dictionary lookup (O(n) per word, case-insensitive)
  Pass 2 — Regex pattern substitutions (stutter removal, whitespace, etc.)

The substitution dictionary is loaded from ``config/phonetic_shield.json``
and can be extended without modifying any Python code.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from config import config
from utils.logger import get_logger

logger = get_logger(__name__)


class PhoneticShield:
    """
    Applies dysarthric-specific phonetic corrections to a raw ASR transcript.

    Usage::

        shield = PhoneticShield()
        corrected = shield.apply("pwease bwing the stwong dwink")
        # → "please bring the strong drink"
    """

    def __init__(self, shield_path: Path | None = None) -> None:
        self._path = shield_path or config.phonetic_shield_path
        self._word_map: dict[str, str] = {}
        self._regex_patterns: list[tuple[re.Pattern, str]] = []
        self._load()

    def _load(self) -> None:
        """Load substitution rules from the JSON dictionary."""
        path = Path(self._path)
        if not path.exists():
            logger.warning(
                "Phonetic shield dictionary not found at '%s'. "
                "No corrections will be applied.",
                path,
            )
            return

        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        # Flatten all category dicts into a single word map
        substitutions = data.get("substitutions", {})
        for category, pairs in substitutions.items():
            if category.startswith("_"):
                continue
            if isinstance(pairs, dict):
                for wrong, correct in pairs.items():
                    if not wrong.startswith("_"):
                        self._word_map[wrong.lower()] = correct

        # Compile regex patterns
        for entry in data.get("regex_patterns", []):
            flags = 0
            for flag_name in entry.get("flags", []):
                flags |= getattr(re, flag_name, 0)
            try:
                pattern = re.compile(entry["pattern"], flags)
                self._regex_patterns.append((pattern, entry["replacement"]))
            except re.error as exc:
                logger.error("Invalid regex in shield config: %s — %s", entry["pattern"], exc)

        logger.info(
            "PhoneticShield loaded: %d word substitutions, %d regex patterns.",
            len(self._word_map),
            len(self._regex_patterns),
        )

    def apply(self, text: str) -> tuple[str, list[str]]:
        """
        Apply phonetic corrections to a transcript.

        Args:
            text: Raw transcript string from ASR.

        Returns:
            Tuple of:
              - corrected transcript string
              - list of human-readable change descriptions (for audit/UI display)
        """
        if not text:
            return text, []

        changes: list[str] = []

        # ── Pass 1: Word-level substitution ───────────────────────────────────
        tokens = text.split()
        corrected_tokens: list[str] = []
        for token in tokens:
            # Strip leading/trailing punctuation for lookup
            stripped = token.strip(".,!?;:\"'()-")
            lower = stripped.lower()
            if lower in self._word_map:
                replacement = self._word_map[lower]
                # Preserve surrounding punctuation
                new_token = token.replace(stripped, replacement, 1)
                corrected_tokens.append(new_token)
                if stripped.lower() != replacement.lower():
                    changes.append(f"'{stripped}' → '{replacement}'")
            else:
                corrected_tokens.append(token)

        text = " ".join(corrected_tokens)

        # ── Pass 2: Regex patterns ─────────────────────────────────────────────
        for pattern, replacement in self._regex_patterns:
            new_text = pattern.sub(replacement, text)
            if new_text != text:
                changes.append(f"regex[{pattern.pattern[:30]}]")
                text = new_text

        text = text.strip()

        if changes:
            logger.debug(
                "PhoneticShield applied %d correction(s): %s",
                len(changes),
                ", ".join(changes[:5]) + (" ..." if len(changes) > 5 else ""),
            )
        else:
            logger.debug("PhoneticShield: no corrections applied.")

        return text, changes
