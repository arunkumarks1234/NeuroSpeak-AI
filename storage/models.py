"""
NeuroSpeak-AI — Session Data Models
=====================================
Pydantic models for validation + SQLAlchemy ORM mappings for persistence.
The ``SessionRecord`` table stores every inference result for longitudinal
analysis and future model fine-tuning.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ─────────────────────────────────────────────────────────────────────────────
# SQLAlchemy ORM
# ─────────────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


class SessionRecordORM(Base):
    """SQLAlchemy ORM model for the ``sessions`` table."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # "file" | "microphone"
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    original_path: Mapped[str] = mapped_column(String(512), nullable=True)

    # Transcription
    raw_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    shield_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    shield_changes_json: Mapped[str] = mapped_column(Text, nullable=True)
    final_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    asr_language: Mapped[str] = mapped_column(String(10), nullable=True)
    asr_provider: Mapped[str] = mapped_column(String(64), nullable=True)

    # Agents
    agent_rounds: Mapped[int] = mapped_column(Integer, nullable=True)
    ollama_available: Mapped[int] = mapped_column(Integer, nullable=True)  # 0/1
    guard_triggered: Mapped[int] = mapped_column(Integer, nullable=True)   # 0/1

    # Severity
    severity_level: Mapped[str] = mapped_column(String(20), nullable=True)
    severity_score: Mapped[float] = mapped_column(Float, nullable=True)
    severity_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    severity_classifier: Mapped[str] = mapped_column(String(64), nullable=True)

    # Acoustic features (serialised as JSON)
    acoustic_features_json: Mapped[str] = mapped_column(Text, nullable=True)

    # Coaching
    coaching_json: Mapped[str] = mapped_column(Text, nullable=True)

    # Embedding (stored path, not inline blob)
    embedding_path: Mapped[str] = mapped_column(String(512), nullable=True)

    def __repr__(self) -> str:
        return f"<Session id={self.id[:8]} severity={self.severity_level} ts={self.timestamp}>"


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schema (used for validation at save time + API response)
# ─────────────────────────────────────────────────────────────────────────────

class SessionRecord(BaseModel):
    """Validated session record — mirrors SessionRecordORM columns."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str
    duration_seconds: float
    original_path: str = ""

    raw_transcript: str
    shield_transcript: str
    shield_changes: list[str] = Field(default_factory=list)
    final_transcript: str
    asr_language: str = "en"
    asr_provider: str = ""

    agent_rounds: int = 0
    ollama_available: bool = True
    guard_triggered: bool = False

    severity_level: str = ""
    severity_score: float = 0.0
    severity_confidence: float = 0.0
    severity_classifier: str = ""

    acoustic_features: dict[str, Any] = Field(default_factory=dict)
    coaching_recommendations: list[str] = Field(default_factory=list)
    embedding_path: str = ""

    def to_orm(self) -> SessionRecordORM:
        """Convert to SQLAlchemy ORM instance for persistence."""
        return SessionRecordORM(
            id=self.id,
            timestamp=self.timestamp,
            source=self.source,
            duration_seconds=self.duration_seconds,
            original_path=self.original_path,
            raw_transcript=self.raw_transcript,
            shield_transcript=self.shield_transcript,
            shield_changes_json=json.dumps(self.shield_changes),
            final_transcript=self.final_transcript,
            asr_language=self.asr_language,
            asr_provider=self.asr_provider,
            agent_rounds=self.agent_rounds,
            ollama_available=int(self.ollama_available),
            guard_triggered=int(self.guard_triggered),
            severity_level=self.severity_level,
            severity_score=self.severity_score,
            severity_confidence=self.severity_confidence,
            severity_classifier=self.severity_classifier,
            acoustic_features_json=json.dumps(self.acoustic_features),
            coaching_json=json.dumps(self.coaching_recommendations),
            embedding_path=self.embedding_path,
        )

    @classmethod
    def from_orm(cls, orm: SessionRecordORM) -> "SessionRecord":
        """Reconstruct from ORM instance."""
        return cls(
            id=orm.id,
            timestamp=orm.timestamp,
            source=orm.source,
            duration_seconds=orm.duration_seconds,
            original_path=orm.original_path or "",
            raw_transcript=orm.raw_transcript,
            shield_transcript=orm.shield_transcript,
            shield_changes=json.loads(orm.shield_changes_json or "[]"),
            final_transcript=orm.final_transcript,
            asr_language=orm.asr_language or "en",
            asr_provider=orm.asr_provider or "",
            agent_rounds=orm.agent_rounds or 0,
            ollama_available=bool(orm.ollama_available),
            guard_triggered=bool(orm.guard_triggered),
            severity_level=orm.severity_level or "",
            severity_score=orm.severity_score or 0.0,
            severity_confidence=orm.severity_confidence or 0.0,
            severity_classifier=orm.severity_classifier or "",
            acoustic_features=json.loads(orm.acoustic_features_json or "{}"),
            coaching_recommendations=json.loads(orm.coaching_json or "[]"),
            embedding_path=orm.embedding_path or "",
        )
