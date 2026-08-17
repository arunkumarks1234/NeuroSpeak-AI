"""
NeuroSpeak-AI — AI Coaching Engine
=====================================
Generates personalised speech rehabilitation recommendations using Qwen 2.5.

The coaching prompt template is loaded from ``config/coaching_prompt.txt``
and filled with the patient's acoustic measurements and severity level.

Falls back to pre-defined static recommendations if Ollama is unavailable.
"""

from __future__ import annotations

import re
from pathlib import Path

from config import config
from severity.base import SeverityLevel
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Static fallback recommendations (when Ollama is unavailable) ──────────────
_STATIC_RECS: dict[SeverityLevel, list[str]] = {
    SeverityLevel.MILD: [
        "Rate Control: Practice speaking at a slightly slower rate (around 120–140 wpm). "
        "Use a metronome app to pace yourself during practice sessions.",
        "Prosody Work: Read poetry or varied text aloud to practise natural intonation "
        "patterns. Record yourself and compare to a model speaker.",
        "Articulation Drills: Focus on tongue-tip sounds (/t/, /d/, /n/, /l/) with "
        "10 repetitions of word lists daily.",
        "Breath Support: Practice diaphragmatic breathing before speech tasks — "
        "inhale for 4 counts, speak on the exhale.",
    ],
    SeverityLevel.MODERATE: [
        "Phrased Breathing: Break sentences into 3–5 word phrases with deliberate "
        "breath pauses. This reduces rush breathing and improves clarity.",
        "Overarticulation: Exaggerate consonant movements during practice. "
        "Hold each consonant for a fraction longer than feels natural.",
        "Loudness Training: Practice projecting your voice to a target 5 metres away. "
        "Lee Silverman Voice Treatment (LSVT LOUD) techniques are highly recommended.",
        "Intelligibility Strategies: Use keyword emphasis — stress the most important "
        "word in each phrase to guide listeners.",
    ],
    SeverityLevel.SEVERE: [
        "Breath Support Priority: Work with a speech therapist on active breath "
        "support. Abdominal binders may help maintain consistent subglottal pressure.",
        "Maximum Intelligibility: Focus all effort on the single most important word "
        "per utterance. Quality over quantity.",
        "AAC Strategies: Consider an Augmentative and Alternative Communication (AAC) "
        "app for high-frequency messages to reduce fatigue.",
        "Pacing Board: Use a pacing board or finger tapping to slow speech rate "
        "and improve syllable-by-syllable intelligibility.",
    ],
    SeverityLevel.UNKNOWN: [
        "Please consult a certified speech-language pathologist for a full assessment.",
    ],
}


class CoachingEngine:
    """
    Generates AI-powered rehabilitation recommendations.

    If Ollama is available, uses Qwen 2.5 with the prompt template.
    Otherwise, serves static evidence-based recommendations.
    """

    def __init__(self) -> None:
        self._prompt_path = config.coaching_prompt_path
        self._n_recs = config.coaching_num_recommendations
        self._prompt_template = self._load_template()

    def _load_template(self) -> str:
        path = Path(self._prompt_path)
        if path.exists():
            return path.read_text(encoding="utf-8")
        logger.warning(
            "Coaching prompt template not found at '%s'. Will use static fallbacks.",
            path,
        )
        return ""

    def _build_prompt(
        self,
        severity_level: SeverityLevel,
        transcript: str,
        acoustic_features: dict,
    ) -> str:
        """Fill the prompt template with patient-specific values."""
        return self._prompt_template.format(
            num_recommendations=self._n_recs,
            severity_level=severity_level.value,
            transcript=transcript[:300],  # truncate very long transcripts
            avg_pitch_hz=round(acoustic_features.get("avg_pitch_hz", 0.0), 1),
            pitch_sd_hz=round(acoustic_features.get("pitch_sd_hz", 0.0), 1),
            pause_ratio=acoustic_features.get("pause_ratio", 0.0),
            spectral_centroid_hz=round(acoustic_features.get("spectral_centroid_hz", 0.0), 0),
        )

    @staticmethod
    def _parse_recommendations(raw: str) -> list[str]:
        """Parse a numbered list from LLM output into individual strings."""
        lines = raw.strip().splitlines()
        recs: list[str] = []
        current: list[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if re.match(r"^\d+[\.\)]", line):  # new numbered item
                if current:
                    recs.append(" ".join(current))
                current = [re.sub(r"^\d+[\.\)]\s*", "", line)]
            elif current:
                current.append(line)
            else:
                current = [line]

        if current:
            recs.append(" ".join(current))

        return [r for r in recs if len(r) > 10]  # filter out very short fragments

    def generate(
        self,
        severity_level: SeverityLevel,
        transcript: str,
        acoustic_features: dict,
    ) -> list[str]:
        """
        Generate rehabilitation recommendations.

        Args:
            severity_level:    Classified dysarthria severity.
            transcript:        Reconstructed/final transcript text.
            acoustic_features: Dict from AcousticExtractor.

        Returns:
            List of recommendation strings (3–5 items).
        """
        if not self._prompt_template:
            logger.info("No prompt template — using static recommendations.")
            return _STATIC_RECS.get(severity_level, _STATIC_RECS[SeverityLevel.UNKNOWN])

        prompt = self._build_prompt(severity_level, transcript, acoustic_features)

        try:
            import ollama  # noqa: PLC0415

            response = ollama.chat(
                model=config.qwen_model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.5, "top_p": 0.9, "num_predict": 500},
            )
            raw = response["message"]["content"].strip()
            recs = self._parse_recommendations(raw)

            if not recs:
                raise ValueError("LLM returned unparseable output.")

            # Pad with static recs if LLM returned fewer than expected
            static = _STATIC_RECS.get(severity_level, [])
            while len(recs) < self._n_recs and len(recs) < len(static):
                recs.append(static[len(recs)])

            logger.info("Coaching engine generated %d recommendations (LLM).", len(recs))
            return recs[: self._n_recs]

        except Exception as exc:  # noqa: BLE001
            logger.warning("CoachingEngine LLM call failed (%s) — using static.", exc)
            return _STATIC_RECS.get(severity_level, _STATIC_RECS[SeverityLevel.UNKNOWN])
