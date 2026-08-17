"""
NeuroSpeak-AI — Llama 3.1 Critic Agent
=========================================
Receives the proposer's reconstruction and evaluates it on three dimensions:
  1. Faithfulness — does it reflect the original transcript's intent?
  2. Fluency — is the output grammatically natural?
  3. Length — is it appropriately concise?

If the proposal passes, returns "ACCEPT".
Otherwise returns a refined version of the text.
"""

from __future__ import annotations

from agents.base import Agent, AgentResponse
from config import config
from utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = """You are a quality-control reviewer for dysarthric speech reconstruction.
You will receive:
  1. The original dysarthric transcript (after phonetic correction).
  2. A proposed reconstruction from another AI model.

Your job is to evaluate the proposal on three criteria:
  - FAITHFULNESS: Does it accurately reflect the intended meaning of the original?
  - FLUENCY: Is it grammatically correct and natural-sounding?
  - LENGTH: Is it appropriately concise (not longer than necessary)?

If the proposal is acceptable on ALL three criteria, respond with exactly: ACCEPT

If it needs improvement, respond with ONLY the improved reconstruction — no explanation.
Do NOT add new information. Do NOT be verbose.
"""


def _build_critic_prompt(original: str, proposal: str, round_num: int, raw: str = "") -> str:
    raw_info = f"Raw ASR transcript (pre-correction):\n\"{raw}\"\n\n" if raw else ""
    return (
        f"[Round {round_num + 1} review]\n\n"
        f"{raw_info}"
        f"Original dysarthric transcript:\n\"{original}\"\n\n"
        f"Proposed reconstruction:\n\"{proposal}\"\n\n"
        f"Is this acceptable? If yes: ACCEPT. If not: provide your improved version only."
    )


class CriticAgent(Agent):
    """Llama 3.1 critic — reviews and optionally refines the proposer's output."""

    _ACCEPT_TOKEN = "ACCEPT"

    @property
    def role(self) -> str:
        return "critic"

    def generate(
        self,
        prompt: str,
        context: dict,
        round_num: int = 0,
    ) -> AgentResponse:
        """
        Critique the proposer's reconstruction.

        Args:
            prompt:    The proposer's output text (reconstruction to evaluate).
            context:   Dict with key ``original_transcript`` (the shield-corrected text).
            round_num: Refinement round index.

        Returns:
            :class:`AgentResponse` where ``content == "ACCEPT"`` means accepted,
            otherwise contains the critic's improved version.
        """
        original = context.get("original_transcript", prompt)
        raw = context.get("raw_transcript", "")
        user_msg = _build_critic_prompt(original, prompt, round_num, raw=raw)
        model_name = config.llama_model

        logger.info(
            "Critic (Llama 3.1) — round %d | model=%s", round_num, model_name
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
                    "temperature": 0.2,  # Conservative — only improve when clearly needed
                    "top_p": 0.85,
                    "num_predict": 150,
                },
            )
            content = response["message"]["content"].strip().strip('"\'')
            logger.debug("Critic output: %s", content[:120])

            return AgentResponse(
                content=content,
                model=model_name,
                role=self.role,
                round_num=round_num,
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("CriticAgent failed: %s", exc)
            # On failure, accept the proposal as-is
            return AgentResponse(
                content=self._ACCEPT_TOKEN,
                model=model_name,
                role=self.role,
                round_num=round_num,
                error=str(exc),
            )

    def is_accepted(self, response: AgentResponse) -> bool:
        """Return True if the critic accepted the proposal."""
        return response.content.strip().upper().startswith(self._ACCEPT_TOKEN)
