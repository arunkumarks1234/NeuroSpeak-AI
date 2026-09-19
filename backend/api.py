"""
NeuroSpeak-AI — API v2 Routes
================================
New endpoints for the Next.js frontend:
  /api/v2/auth/*          — Simple session-based auth
  /api/v2/speech/*        — Pronunciation assessment + TTS
  /api/v2/session/*       — Session retrieval + phoneme detail
  /api/v2/patient/*       — Patient dashboard + gamification
  /api/v2/clinician/*     — Clinician monitoring + prescriptions + export
  /api/v2/words/*         — Word set library
"""

from __future__ import annotations

import base64
import csv
import io
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import get_db
from .models import (
    User, PronunciationSession, PhonemeScore,
    GamificationStats, Prescription,
)
from .services.pronunciation_service import (
    PronunciationService, classify_difficulty, PronunciationAssessmentResult
)
from .services.gamification_service import GamificationService

router = APIRouter(prefix="/api/v2")

_pronunciation_svc = PronunciationService()
_gamification_svc = GamificationService()


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str  # Plain text for demo — hash in production

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    role: str  # "patient" | "clinician"

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    preferred_language: str

class AssessRequest(BaseModel):
    user_id: int
    target_text: str
    audio_base64: str         # WAV audio encoded as base64
    language: str = "en-US"
    audio_duration_sec: float = 3.0

class PhonemeOut(BaseModel):
    phoneme: str
    score: float
    error_type: Optional[str] = None

class WordOut(BaseModel):
    word: str
    accuracy_score: float
    error_type: Optional[str] = None
    phonemes: list[PhonemeOut]

class AssessResponse(BaseModel):
    session_uuid: str
    accuracy_score: float
    fluency_score: float
    completeness_score: float
    prosody_score: float
    overall_score: float
    difficulty: str
    xp_earned: int
    tier_promoted: bool
    new_tier: str
    streak_days: int
    words: list[WordOut]
    provider: str

class PrescribeRequest(BaseModel):
    clinician_id: int
    patient_id: int
    title: str
    notes: Optional[str] = None
    difficulty: str = "moderate"
    word_set: list[dict]  # [{"text": "...", "category": "..."}]

# ─────────────────────────────────────────────────────────────────────────────
# Word Library (Built-in)
# ─────────────────────────────────────────────────────────────────────────────

WORD_LIBRARY = {
    "easy": [
        {"text": "cat", "category": "animals"}, {"text": "dog", "category": "animals"},
        {"text": "sun", "category": "nature"}, {"text": "map", "category": "objects"},
        {"text": "cup", "category": "objects"}, {"text": "big", "category": "adjectives"},
        {"text": "red", "category": "colors"}, {"text": "run", "category": "verbs"},
        {"text": "sit", "category": "verbs"}, {"text": "bat", "category": "objects"},
    ],
    "moderate": [
        {"text": "butterfly", "category": "animals"}, {"text": "telephone", "category": "objects"},
        {"text": "beautiful", "category": "adjectives"}, {"text": "hospital", "category": "places"},
        {"text": "yesterday", "category": "time"}, {"text": "celebrate", "category": "verbs"},
        {"text": "adventure", "category": "concepts"}, {"text": "chocolate", "category": "food"},
        {"text": "strawberry", "category": "food"}, {"text": "remember", "category": "verbs"},
    ],
    "hard": [
        {"text": "The strength of the structure was thoroughly tested.", "category": "sentence"},
        {"text": "She sells seashells by the seashore.", "category": "tongue-twister"},
        {"text": "Specific instructions for extraordinary circumstances.", "category": "sentence"},
        {"text": "The thirty-three thieves thought that they thrilled the throne.", "category": "tongue-twister"},
        {"text": "Respiratory physiotherapy strengthens articulation.", "category": "clinical"},
    ],
}


@router.get("/words/library")
def get_word_library(difficulty: Optional[str] = None):
    if difficulty and difficulty in WORD_LIBRARY:
        return {"difficulty": difficulty, "words": WORD_LIBRARY[difficulty]}
    return {"library": WORD_LIBRARY}


# ─────────────────────────────────────────────────────────────────────────────
# Auth Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=UserResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(email=req.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")

    user = User(
        email=req.email,
        hashed_password=req.password,  # NOTE: hash with bcrypt in production
        name=req.name,
        role=req.role,
        preferred_language="en",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize gamification stats
    stats = GamificationStats(user_id=user.id)
    db.add(stats)
    db.commit()

    return UserResponse(id=user.id, email=user.email, name=user.name,
                        role=user.role, preferred_language=user.preferred_language)


@router.post("/auth/login", response_model=UserResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=req.email).first()
    if not user or user.hashed_password != req.password:
        raise HTTPException(401, "Invalid credentials")

    user.last_active = datetime.utcnow()
    db.commit()

    return UserResponse(id=user.id, email=user.email, name=user.name,
                        role=user.role, preferred_language=user.preferred_language)


@router.get("/auth/user/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return UserResponse(id=user.id, email=user.email, name=user.name,
                        role=user.role, preferred_language=user.preferred_language)


# ─────────────────────────────────────────────────────────────────────────────
# Speech Assessment
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/speech/assess", response_model=AssessResponse)
def assess_pronunciation(req: AssessRequest, db: Session = Depends(get_db)):
    """
    Main pronunciation assessment endpoint.
    Accepts base64-encoded WAV audio + reference text.
    Returns full scoring + gamification updates.
    """
    user = db.query(User).filter_by(id=req.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    # Decode audio
    try:
        audio_bytes = base64.b64decode(req.audio_base64)
    except Exception:
        raise HTTPException(400, "Invalid base64 audio data")

    # Assess pronunciation
    difficulty = classify_difficulty(req.target_text)
    result: PronunciationAssessmentResult = _pronunciation_svc.assess(
        audio_bytes=audio_bytes,
        reference_text=req.target_text,
        audio_duration_sec=req.audio_duration_sec,
        language=req.language,
    )

    # Gamification update
    gam_update = _gamification_svc.process_session(
        db=db,
        user_id=req.user_id,
        accuracy=result.accuracy_score,
        difficulty=difficulty,
        audio_duration_sec=req.audio_duration_sec,
    )

    # Persist session
    session_uuid = str(uuid.uuid4())
    phoneme_detail = []
    phoneme_rows = []
    for word in result.words:
        for ph in word.phonemes:
            phoneme_detail.append({
                "phoneme": ph.phoneme,
                "score": ph.score,
                "error_type": ph.error_type,
                "word": word.word,
            })
            phoneme_rows.append(PhonemeScore(
                phoneme=ph.phoneme,
                score=ph.score,
                error_type=ph.error_type,
                duration_ms=ph.duration_ms,
            ))

    ps = PronunciationSession(
        session_uuid=session_uuid,
        user_id=req.user_id,
        target_text=req.target_text,
        target_language=req.language,
        difficulty=difficulty,
        audio_duration_sec=req.audio_duration_sec,
        accuracy_score=result.accuracy_score,
        fluency_score=result.fluency_score,
        completeness_score=result.completeness_score,
        prosody_score=result.prosody_score,
        overall_score=result.overall_score,
        xp_earned=gam_update.xp_earned,
        phoneme_detail_json=phoneme_detail,
        phoneme_scores=phoneme_rows,
    )
    db.add(ps)
    db.commit()

    return AssessResponse(
        session_uuid=session_uuid,
        accuracy_score=result.accuracy_score,
        fluency_score=result.fluency_score,
        completeness_score=result.completeness_score,
        prosody_score=result.prosody_score,
        overall_score=result.overall_score,
        difficulty=difficulty,
        xp_earned=gam_update.xp_earned,
        tier_promoted=gam_update.tier_promoted,
        new_tier=gam_update.new_tier,
        streak_days=gam_update.streak_days,
        words=[
            WordOut(
                word=w.word,
                accuracy_score=w.accuracy_score,
                error_type=w.error_type,
                phonemes=[
                    PhonemeOut(phoneme=p.phoneme, score=p.score, error_type=p.error_type)
                    for p in w.phonemes
                ]
            )
            for w in result.words
        ],
        provider=result.provider,
    )


@router.get("/session/{session_uuid}")
def get_session(session_uuid: str, db: Session = Depends(get_db)):
    session = db.query(PronunciationSession).filter_by(session_uuid=session_uuid).first()
    if not session:
        raise HTTPException(404, "Session not found")
    return {
        "session_uuid": session.session_uuid,
        "target_text": session.target_text,
        "difficulty": session.difficulty,
        "accuracy_score": session.accuracy_score,
        "fluency_score": session.fluency_score,
        "completeness_score": session.completeness_score,
        "overall_score": session.overall_score,
        "xp_earned": session.xp_earned,
        "phoneme_detail": session.phoneme_detail_json,
        "timestamp": session.timestamp.isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Patient Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/patient/{user_id}/dashboard")
def patient_dashboard(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    stats = db.query(GamificationStats).filter_by(user_id=user_id).first()
    sessions = (
        db.query(PronunciationSession)
        .filter_by(user_id=user_id)
        .order_by(PronunciationSession.timestamp.desc())
        .limit(30)
        .all()
    )

    # Build streak calendar (last 30 days)
    practice_dates = {s.timestamp.date() for s in sessions}
    today = datetime.utcnow().date()
    calendar = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        calendar.append({"date": d.isoformat(), "practiced": d in practice_dates})

    # Phoneme weakness analysis
    all_phonemes: dict[str, list[float]] = {}
    for s in sessions:
        if s.phoneme_detail_json:
            for p in s.phoneme_detail_json:
                ph = p.get("phoneme", "")
                sc = p.get("score", 100)
                all_phonemes.setdefault(ph, []).append(sc)

    weaknesses = sorted(
        [{"phoneme": ph, "avg_score": round(sum(scores)/len(scores), 1)}
         for ph, scores in all_phonemes.items()],
        key=lambda x: x["avg_score"]
    )[:5]

    # Prescriptions
    prescriptions = (
        db.query(Prescription)
        .filter_by(patient_id=user_id, is_active=True)
        .all()
    )

    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "gamification": {
            "total_xp": stats.total_xp if stats else 0,
            "tier": stats.tier if stats else "bronze",
            "streak_days": stats.current_streak_days if stats else 0,
            "longest_streak": stats.longest_streak_days if stats else 0,
            "total_sessions": stats.total_sessions if stats else 0,
            "avg_accuracy": stats.avg_accuracy if stats else None,
            "daily_quest_progress": (
                min(stats.daily_quest_completed_minutes / 15 * 100, 100) if stats else 0
            ),
            "daily_quest_completed": stats.daily_quest_completed if stats else False,
        },
        "streak_calendar": calendar,
        "phoneme_weaknesses": weaknesses,
        "recent_sessions": [
            {
                "session_uuid": s.session_uuid,
                "target_text": s.target_text,
                "difficulty": s.difficulty,
                "overall_score": s.overall_score,
                "xp_earned": s.xp_earned,
                "timestamp": s.timestamp.isoformat(),
            }
            for s in sessions[:10]
        ],
        "prescriptions": [
            {
                "id": p.id,
                "title": p.title,
                "difficulty": p.difficulty,
                "word_count": len(p.word_set_json),
                "notes": p.notes,
            }
            for p in prescriptions
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Clinician Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/clinician/{clinician_id}/patients")
def get_patients(clinician_id: int, db: Session = Depends(get_db)):
    """Return all patients with active prescriptions from this clinician."""
    prescriptions = (
        db.query(Prescription)
        .filter_by(clinician_id=clinician_id, is_active=True)
        .all()
    )
    patient_ids = list({p.patient_id for p in prescriptions})
    patients = db.query(User).filter(User.id.in_(patient_ids), User.role == "patient").all()

    result = []
    for patient in patients:
        stats = db.query(GamificationStats).filter_by(user_id=patient.id).first()
        last_session = (
            db.query(PronunciationSession)
            .filter_by(user_id=patient.id)
            .order_by(PronunciationSession.timestamp.desc())
            .first()
        )
        result.append({
            "id": patient.id,
            "name": patient.name,
            "email": patient.email,
            "tier": stats.tier if stats else "bronze",
            "streak_days": stats.current_streak_days if stats else 0,
            "avg_accuracy": stats.avg_accuracy if stats else None,
            "total_sessions": stats.total_sessions if stats else 0,
            "last_session": last_session.timestamp.isoformat() if last_session else None,
        })

    return {"clinician_id": clinician_id, "patients": result}


@router.get("/clinician/patient/{patient_id}/analysis")
def patient_analysis(patient_id: int, db: Session = Depends(get_db)):
    """Detailed phoneme analysis + longitudinal accuracy for clinician view."""
    sessions = (
        db.query(PronunciationSession)
        .filter_by(user_id=patient_id)
        .order_by(PronunciationSession.timestamp.asc())
        .limit(60)
        .all()
    )

    # Longitudinal accuracy (last 30 sessions)
    longitudinal = [
        {
            "date": s.timestamp.strftime("%Y-%m-%d"),
            "accuracy": s.accuracy_score,
            "fluency": s.fluency_score,
            "overall": s.overall_score,
            "difficulty": s.difficulty,
        }
        for s in sessions[-30:]
    ]

    # Phoneme error frequency map
    phoneme_errors: dict[str, dict] = {}
    for s in sessions:
        if s.phoneme_detail_json:
            for p in s.phoneme_detail_json:
                ph = p.get("phoneme", "")
                err = p.get("error_type")
                score = p.get("score", 100)
                if ph not in phoneme_errors:
                    phoneme_errors[ph] = {"phoneme": ph, "scores": [], "errors": []}
                phoneme_errors[ph]["scores"].append(score)
                if err:
                    phoneme_errors[ph]["errors"].append(err)

    phoneme_summary = [
        {
            "phoneme": v["phoneme"],
            "avg_score": round(sum(v["scores"]) / len(v["scores"]), 1),
            "error_count": len(v["errors"]),
            "most_common_error": max(set(v["errors"]), key=v["errors"].count) if v["errors"] else None,
        }
        for v in phoneme_errors.values()
    ]
    phoneme_summary.sort(key=lambda x: x["avg_score"])

    return {
        "patient_id": patient_id,
        "total_sessions": len(sessions),
        "longitudinal_data": longitudinal,
        "phoneme_analysis": phoneme_summary,
    }


@router.post("/clinician/prescribe")
def prescribe_word_set(req: PrescribeRequest, db: Session = Depends(get_db)):
    prescription = Prescription(
        clinician_id=req.clinician_id,
        patient_id=req.patient_id,
        title=req.title,
        notes=req.notes,
        difficulty=req.difficulty,
        word_set_json=req.word_set,
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return {"id": prescription.id, "message": "Prescription created successfully"}


@router.get("/clinician/patient/{patient_id}/export/csv")
def export_patient_csv(patient_id: int, db: Session = Depends(get_db)):
    """Export all sessions as CSV for clinical review."""
    sessions = (
        db.query(PronunciationSession)
        .filter_by(user_id=patient_id)
        .order_by(PronunciationSession.timestamp.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date", "Target Text", "Difficulty", "Accuracy", "Fluency",
        "Completeness", "Prosody", "Overall", "XP Earned", "Duration (s)"
    ])
    for s in sessions:
        writer.writerow([
            s.timestamp.strftime("%Y-%m-%d %H:%M"),
            s.target_text,
            s.difficulty,
            f"{s.accuracy_score:.1f}" if s.accuracy_score else "",
            f"{s.fluency_score:.1f}" if s.fluency_score else "",
            f"{s.completeness_score:.1f}" if s.completeness_score else "",
            f"{s.prosody_score:.1f}" if s.prosody_score else "",
            f"{s.overall_score:.1f}" if s.overall_score else "",
            s.xp_earned,
            f"{s.audio_duration_sec:.1f}" if s.audio_duration_sec else "",
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=patient_{patient_id}_report.csv"},
    )
