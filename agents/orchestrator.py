"""
NeuroSpeak-AI — Agent Orchestrator
=====================================
Manages the full proposer → critic refinement loop.

Flow:
  1. HallucinationGuard pre-checks the shield transcript length.
  2. ProposerAgent generates initial reconstruction.
  3. HallucinationGuard checks the proposal.
  4. CriticAgent reviews the proposal.
  5. If ACCEPT → done. If refine → go to step 2 with critic feedback.
  6. After MAX_REFINE_ROUNDS → take the best proposal seen.

Graceful degradation:
  - If Ollama is unavailable, returns the phonetic-shield-corrected transcript.
  - Per-step timeouts (using threading) prevent UI hangs.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from agents.base import AgentResponse
from agents.critic import CriticAgent
from agents.hallucination_guard import HallucinationGuard
from agents.proposer import ProposerAgent
from config import config
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OrchestrationResult:
    """Full result from the multi-agent pipeline."""

    final_text: str
    raw_transcript: str          # pre-shield
    shield_transcript: str       # post-phonetic-shield
    shield_changes: list[str]
    rounds_completed: int
    agent_log: list[dict] = field(default_factory=list)
    guard_triggered: bool = False
    ollama_available: bool = True

    # ── Semantic reconstruction contract (project requirement) ──
    proposed_text: str = ""      # last proposer output (best proposal seen)
    critic_verdict: str = ""     # "ACCEPT" | "REFINE" | "N/A"
    number_of_rounds: int = 0    # alias for rounds_completed


def _run_with_timeout(fn, timeout: int, fallback):
    """Run fn() in a thread; return fallback if it exceeds timeout seconds."""
    result_holder = [fallback]
    exc_holder: list[BaseException | None] = [None]

    def wrapper():
        try:
            result_holder[0] = fn()
        except Exception as exc:  # noqa: BLE001
            exc_holder[0] = exc

    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        logger.warning("Agent timed out after %d s — using fallback.", timeout)
        return fallback, True  # (result, timed_out)

    if exc_holder[0]:
        logger.error("Agent raised exception: %s", exc_holder[0])
        return fallback, False

    return result_holder[0], False


class AgentOrchestrator:
    """
    Coordinates the Qwen 2.5 proposer and Llama 3.1 critic.

    Usage::

        orch = AgentOrchestrator()
        result = orch.run(
            raw_transcript="pwease bwing me water",
            shield_transcript="please bring me water",
            shield_changes=["pwease → please", "bwing → bring"],
            duration_seconds=3.4,
            acoustic_features={"avg_pitch_hz": 142.0, ...},
        )
    """

    def __init__(self) -> None:
        self._proposer = ProposerAgent()
        self._critic = CriticAgent()
        self._guard = HallucinationGuard()
        self._max_rounds = config.max_refine_rounds
        self._timeout = config.ollama_timeout

    def run(
        self,
        raw_transcript: str,
        shield_transcript: str,
        shield_changes: list[str],
        duration_seconds: float,
        acoustic_features: dict | None = None,
    ) -> OrchestrationResult:
        """
        Execute the full proposer → critic loop.

        Args:
            raw_transcript:    Whisper output before phonetic correction.
            shield_transcript: Transcript after PhoneticShield corrections.
            shield_changes:    Human-readable list of shield substitutions made.
            duration_seconds:  Audio clip duration (for hallucination guard).
            acoustic_features: Optional dict from AcousticExtractor.

        Returns:
            :class:`OrchestrationResult` with the final reconstructed text
            and a full audit log.
        """
        agent_log: list[dict] = []
        guard_triggered = False
        ollama_available = True

        # Pre-flight: guard on the shield transcript itself
        is_valid, wc, max_wc = self._guard.check(shield_transcript, duration_seconds)
        if not is_valid:
            logger.warning(
                "Shield transcript already exceeds guard limit (%d/%d words). "
                "Truncating before agent pass.",
                wc,
                max_wc,
            )
            shield_transcript = self._guard.truncate(shield_transcript, duration_seconds)
            guard_triggered = True

        context = {
            "original_transcript": shield_transcript,
            "raw_transcript": raw_transcript,  # pass raw ASR text to both agents
            "duration_seconds": duration_seconds,
            "acoustic_features": acoustic_features or {},
        }

        current_proposal = shield_transcript
        best_proposal = shield_transcript
        critic_verdict = "N/A"

        for round_idx in range(self._max_rounds):
            # ── Proposer step ─────────────────────────────────────────────────
            proposer_fn = lambda: self._proposer.generate(  # noqa: E731
                current_proposal, context, round_num=round_idx
            )
            proposal_resp, timed_out = _run_with_timeout(
                proposer_fn,
                self._timeout,
                AgentResponse(
                    content=current_proposal,
                    model=config.qwen_model,
                    role="proposer",
                    round_num=round_idx,
                    timed_out=True,
                ),
            )

            if timed_out or proposal_resp.error:
                ollama_available = False
                logger.warning("Proposer unavailable — using shield transcript.")
                break

            proposed_text = self._guard.enforce(
                proposal_resp.content, duration_seconds
            )
            if proposed_text != proposal_resp.content:
                guard_triggered = True

            best_proposal = proposed_text

            agent_log.append(
                {
                    "round": round_idx,
                    "agent": "proposer",
                    "model": proposal_resp.model,
                    "output": proposed_text,
                }
            )

            # ── Critic step ───────────────────────────────────────────────────
            critic_context = {**context, "original_transcript": shield_transcript}
            critic_fn = lambda: self._critic.generate(  # noqa: E731
                proposed_text, critic_context, round_num=round_idx
            )
            critic_resp, timed_out = _run_with_timeout(
                critic_fn,
                self._timeout,
                AgentResponse(
                    content="ACCEPT",
                    model=config.llama_model,
                    role="critic",
                    round_num=round_idx,
                    timed_out=True,
                ),
            )

            if timed_out or critic_resp.error:
                ollama_available = False
                current_proposal = proposed_text
                critic_verdict = "ACCEPT (timeout fallback)"
                agent_log.append(
                    {
                        "round": round_idx,
                        "agent": "critic",
                        "model": config.llama_model,
                        "output": "ACCEPT (timeout fallback)",
                    }
                )
                break

            agent_log.append(
                {
                    "round": round_idx,
                    "agent": "critic",
                    "model": critic_resp.model,
                    "output": critic_resp.content,
                }
            )

            if self._critic.is_accepted(critic_resp):
                logger.info("Critic ACCEPTED proposal at round %d.", round_idx + 1)
                current_proposal = proposed_text
                critic_verdict = "ACCEPT"
                break

            # Critic provided a refinement — use it as the next proposal
            critic_verdict = "REFINE"
            refined = self._guard.enforce(critic_resp.content, duration_seconds)
            if refined != critic_resp.content:
                guard_triggered = True
            current_proposal = refined

        logger.info(
            "Orchestration complete | rounds=%d | guard=%s | ollama=%s",
            len([r for r in agent_log if r["agent"] == "proposer"]),
            guard_triggered,
            ollama_available,
        )

        rounds = len([r for r in agent_log if r["agent"] == "proposer"])
        return OrchestrationResult(
            final_text=current_proposal,
            raw_transcript=raw_transcript,
            shield_transcript=shield_transcript,
            shield_changes=shield_changes,
            rounds_completed=rounds,
            agent_log=agent_log,
            guard_triggered=guard_triggered,
            ollama_available=ollama_available,
            proposed_text=best_proposal,
            critic_verdict=critic_verdict,
            number_of_rounds=rounds,
        )
