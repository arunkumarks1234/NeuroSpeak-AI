"""
NeuroSpeak-AI — Enhanced SQLAlchemy Models
============================================
Extends the original Doctor/Patient/SessionLog schema with:
  - User (unified role-based auth)
  - PronunciationSession (full scoring + XP)
  - PhonemeScore (per-phoneme breakdown)
  - GamificationStats (streak, XP, tier)
  - Prescription (clinician-assigned word sets)

Original Doctor/Patient/SessionLog models are preserved for backward compatibility.
"""

from __future__ import annotations

import datetime
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey,
    DateTime, Text, Boolean, JSON
)
from sqlalchemy.orm import relationship
from .database import Base


# ─────────────────────────────────────────────────────────────────────────────
# Legacy Models (preserved for backward compatibility with existing Gradio UI)
# ─────────────────────────────────────────────────────────────────────────────

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(String, unique=True, index=True)
    name = Column(String)
    department = Column(String)
    license_no = Column(String)
    contact = Column(String)

    patients = relationship("Patient", back_populates="assigned_doctor")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, unique=True, index=True)
    assigned_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    name = Column(String)
    diagnosis_type = Column(String)
    current_streak = Column(Integer, default=0)
    total_xp = Column(Integer, default=0)

    assigned_doctor = relationship("Doctor", back_populates="patients")
    sessions = relationship("SessionLog", back_populates="patient")


class SessionLog(Base):
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    raw_audio_url = Column(String)
    deciphered_text = Column(String)
    language_mode = Column(String)
    clarity_score = Column(Float)
    lip_sync_accuracy_score = Column(Float)
    active_phoneme_matrix = Column(String)  # Stored as JSON string

    patient = relationship("Patient", back_populates="sessions")


# ─────────────────────────────────────────────────────────────────────────────
# New Models — Gamified Pronunciation Platform
# ─────────────────────────────────────────────────────────────────────────────

class User(Base):
    """Unified user model for both patients and clinicians."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)          # "patient" | "clinician"
    name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    preferred_language = Column(String, default="en")
    dialect = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_active = Column(DateTime, nullable=True)

    # Relationships
    pronunciation_sessions = relationship(
        "PronunciationSession", back_populates="user",
        foreign_keys="PronunciationSession.user_id"
    )
    gamification_stats = relationship(
        "GamificationStats", back_populates="user", uselist=False
    )
    prescriptions_received = relationship(
        "Prescription", back_populates="patient",
        foreign_keys="Prescription.patient_id"
    )
    prescriptions_given = relationship(
        "Prescription", back_populates="clinician",
        foreign_keys="Prescription.clinician_id"
    )


class PronunciationSession(Base):
    """Records a single speech exercise session with full scoring metrics."""
    __tablename__ = "pronunciation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_uuid = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    # Target content
    target_text = Column(Text, nullable=False)
    target_language = Column(String, default="en")
    difficulty = Column(String, default="moderate")  # "easy" | "moderate" | "hard"

    # Audio
    audio_url = Column(String, nullable=True)
    audio_duration_sec = Column(Float, nullable=True)

    # Scoring (0-100)
    accuracy_score = Column(Float, nullable=True)
    fluency_score = Column(Float, nullable=True)
    completeness_score = Column(Float, nullable=True)
    prosody_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)

    # ASR transcript from pipeline
    asr_transcript = Column(Text, nullable=True)
    final_transcript = Column(Text, nullable=True)

    # Severity from pipeline
    severity_level = Column(String, nullable=True)   # "mild" | "moderate" | "severe"
    severity_score = Column(Float, nullable=True)

    # Gamification
    xp_earned = Column(Integer, default=0)
    combo_multiplier = Column(Float, default=1.0)

    # Full phoneme detail (JSON array of PhonemeScore records)
    phoneme_detail_json = Column(JSON, nullable=True)

    # Coaching recommendations from pipeline
    coaching_json = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="pronunciation_sessions",
                        foreign_keys=[user_id])
    phoneme_scores = relationship("PhonemeScore", back_populates="session",
                                  cascade="all, delete-orphan")


class PhonemeScore(Base):
    """Per-phoneme accuracy record within a session."""
    __tablename__ = "phoneme_scores"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("pronunciation_sessions.id"), nullable=False)
    phoneme = Column(String, nullable=False)          # IPA symbol, e.g. "æ"
    score = Column(Float, nullable=False)             # 0.0 – 100.0
    error_type = Column(String, nullable=True)        # "substitution" | "omission" | "distortion" | None
    duration_ms = Column(Float, nullable=True)        # Duration of phoneme in utterance

    session = relationship("PronunciationSession", back_populates="phoneme_scores")


class GamificationStats(Base):
    """Tracks a user's XP, tier, streaks, and quest progress."""
    __tablename__ = "gamification_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    total_xp = Column(Integer, default=0)
    # Tier: "bronze" | "silver" | "gold" | "master"
    tier = Column(String, default="bronze")
    tier_rank = Column(Integer, default=1)            # rank within tier (1-10)

    # Streak
    current_streak_days = Column(Integer, default=0)
    longest_streak_days = Column(Integer, default=0)
    last_practice_date = Column(DateTime, nullable=True)

    # Daily quest
    daily_quest_target_minutes = Column(Integer, default=15)
    daily_quest_completed_minutes = Column(Float, default=0.0)
    daily_quest_completed = Column(Boolean, default=False)
    daily_quest_date = Column(DateTime, nullable=True)

    # Aggregate stats
    total_sessions = Column(Integer, default=0)
    total_practice_minutes = Column(Float, default=0.0)
    avg_accuracy = Column(Float, nullable=True)

    user = relationship("User", back_populates="gamification_stats")


class Prescription(Base):
    """Clinician-assigned word/sentence sets for specific patients."""
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    clinician_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    title = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    difficulty = Column(String, default="moderate")

    # JSON array: [{"text": "...", "category": "...", "difficulty": "..."}]
    word_set_json = Column(JSON, nullable=False)

    is_active = Column(Boolean, default=True)

    clinician = relationship("User", back_populates="prescriptions_given",
                             foreign_keys=[clinician_id])
    patient = relationship("User", back_populates="prescriptions_received",
                           foreign_keys=[patient_id])
