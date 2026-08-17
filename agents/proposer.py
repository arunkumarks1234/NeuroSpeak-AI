"""
NeuroSpeak-AI — Qwen 2.5 Proposer Agent
==========================================
Given a phonetically corrected transcript and acoustic context, Qwen 2.5
proposes a semantically reconstructed version of what the speaker intended.

Ollama is used as the local inference server.
Falls back gracefully if Ollama is unavailable.
"""

from __future__ import annotations

from agents.base import Agent, AgentResponse
from config import config
from utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = """You are a specialist in dysarthric speech rehabilitation.
Your task is to reconstruct the INTENDED meaning of a speech transcript from a person with dysarthria.

Guidelines:
- Preserve the speaker's ORIGINAL INTENT as closely as possible.
- Fix grammatical errors caused by phoneme substitutions.
- Do NOT add information that is not implied by the original transcript.
- Do NOT make the output longer than necessary.
- Return ONLY the reconstructed sentence — no explanation, no preamble.
"""


def _build_user_prompt(transcript: str, context: dict) -> str:
    """Build the user-facing portion of the proposer prompt."""
    raw = context.get("raw_transcript", "")
    acoustic_info = ""
    if context.get("acoustic_features"):
        af = context["acoustic_features"]
        acoustic_info = (
            f"\nAcoustic context: "
            f"avg pitch={af.get('avg_pitch_hz', 'N/A')} Hz, "
            f"pause_ratio={af.get('pause_ratio', 'N/A'):.2f}, "
            f"spectral_centroid={af.get('spectral_centroid_hz', 'N/A')} Hz"
        )

    raw_info = f'Original ASR transcript:\n"{raw}"\n\n' if raw else ""

    return (
        f"{raw_info}"
        f"Dysarthric transcript (after phonetic correction):\n"
        f'"{transcript}"\n'
        f"{acoustic_info}\n\n"
        f"Reconstruct what the speaker intended to say:"
    )


class ProposerAgent(Agent):
    """Qwen 2.5 proposer — generates the initial semantic reconstruction."""

    @property
    def role(self) -> str:
        return "proposer"

    def generate(
        self,
        prompt: str,
        context: dict,
        round_num: int = 0,
    ) -> AgentResponse:
        """
        Generate a semantic reconstruction proposal using Qwen 2.5.

        Args:
            prompt:    The phonetically corrected transcript.
            context:   Dict with optional keys: ``acoustic_features``, ``duration_seconds``.
            round_num: Refinement round index.

        Returns:
            :class:`AgentResponse` with Qwen's proposal.
        """
        user_msg = _build_user_prompt(prompt, context)
        model_name = config.qwen_model

        logger.info(
            "Proposer (Qwen 2.5) — round %d | model=%s", round_num, model_name
        )

        try:
            import ollama  # noqa: PLC0415

            response = ollama.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                options={
                    "temperature": 0.3,   # Low temp for faithful reconstruction
                    "top_p": 0.9,
                    "num_predict": 200,   # Cap token output
                },
            )
            content = response["message"]["content"].strip()
            # Strip surrounding quotes if the model wraps the output
            content = content.strip('"\'')
            logger.debug("Proposer output: %s", content[:120])

            return AgentResponse(
                content=content,
                model=model_name,
                role=self.role,
                round_num=round_num,
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("ProposerAgent failed: %s", exc)
            return AgentResponse(
                content=prompt,          # fall back to the original transcript
                model=model_name,
                role=self.role,
                round_num=round_num,
                error=str(exc),
            )
