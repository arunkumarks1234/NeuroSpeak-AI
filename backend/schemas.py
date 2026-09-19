from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Request Schemas
class DecipherRequest(BaseModel):
    audio_blob_base64: str
    source_language: str # 'kn' or 'en-IN'

class LipFrameRequest(BaseModel):
    landmarks: List[Dict[str, float]] # [{x, y, z}, ...]
    expected_phoneme: Optional[str] = None

# Response Schemas
class DecipherResponse(BaseModel):
    active_phoneme: str
    deciphered_text: str
    translated_text: str
    synthesized_audio_url: str
    clarity_score: float

class LipFrameResponse(BaseModel):
    aperture_error: float
    roundness_error: float
    is_correct: bool
    feedback_message: str

class AnalyticsResponse(BaseModel):
    patient_id: str
    historical_clarity: List[float]
    task_completion_rates: List[float]
    dates: List[str]
