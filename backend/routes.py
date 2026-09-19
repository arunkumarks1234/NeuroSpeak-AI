from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import random
from datetime import datetime, timedelta

from . import schemas, models
from .database import get_db

router = APIRouter(prefix="/api/v1")

@router.post("/speech/decipher", response_model=schemas.DecipherResponse)
def decipher_speech(req: schemas.DecipherRequest, db: Session = Depends(get_db)):
    # Mock inference logic simulating AI4Bharat / Bhashini / Whisper
    # In a real scenario, this would decode the audio_blob_base64
    
    phonemes = ["æ", "b", "d", "eɪ", "f", "g", "i:", "k", "l", "m", "n", "oʊ", "p", "r", "s", "t"]
    
    if req.source_language == 'kn':
        deciphered = "ನಾನು ಚೆನ್ನಾಗಿದ್ದೇನೆ"
        translated = "I am doing well."
    else:
        deciphered = "I am trying to speak clearly."
        translated = "I am trying to speak clearly."

    return schemas.DecipherResponse(
        active_phoneme=random.choice(phonemes),
        deciphered_text=deciphered,
        translated_text=translated,
        synthesized_audio_url="mock_audio.wav",
        clarity_score=random.uniform(70.0, 95.0)
    )

@router.post("/vision/analyze-lip-frame", response_model=schemas.LipFrameResponse)
def analyze_lip_frame(req: schemas.LipFrameRequest):
    # Mock computer vision logic evaluating landmarks against phoneme templates
    error_val = random.uniform(0.0, 5.0)
    is_correct = error_val < 2.0
    
    return schemas.LipFrameResponse(
        aperture_error=error_val,
        roundness_error=random.uniform(0.0, 3.0),
        is_correct=is_correct,
        feedback_message="Perfect!" if is_correct else "Try rounding your lips more."
    )

@router.get("/doctor/patients/{patient_id}/analytics", response_model=schemas.AnalyticsResponse)
def get_analytics(patient_id: str, db: Session = Depends(get_db)):
    # Generate 7 days of mock historical data
    dates = [(datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    dates.reverse()

    clarities = [random.uniform(60, 90) for _ in range(7)]
    completion = [random.uniform(50, 100) for _ in range(7)]

    return schemas.AnalyticsResponse(
        patient_id=patient_id,
        historical_clarity=clarities,
        task_completion_rates=completion,
        dates=dates
    )
