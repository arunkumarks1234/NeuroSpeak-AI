"""
NeuroSpeak-AI — Abstract Agent Interface
==========================================
All LLM agents (Qwen proposer, Llama critic, coaching) implement this ABC.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AgentResponse:
    """Structured response from any agent."""

    content: str           # The text output
    model: str             # Model name used
    role: str              # "proposer" | "critic" | "coach"
    round_num: int         # Which refinement round (0 = first)
    timed_out: bool = False
    error: str = ""


class Agent(ABC):
    """Abstract LLM agent. Override ``generate`` in each concrete agent."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        context: dict,
        round_num: int = 0,
    ) -> AgentResponse:
        """
        Generate a text response.

        Args:
            prompt:    The main instruction prompt.
            context:   Additional context dict (transcript, acoustics, etc.).
            round_num: Current refinement iteration (0-indexed).

        Returns:
            :class:`AgentResponse` with generated content.
        """

    @property
    @abstractmethod
    def role(self) -> str:
        """Agent role identifier string."""
