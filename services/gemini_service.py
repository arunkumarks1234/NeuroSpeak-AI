"""
NeuroSpeak-AI — Google Gemini Service
======================================
Integrates Google Gemini API (gemini-2.5-flash) for:
  1. Multilingual dysarthric intent understanding & semantic reconstruction.
  2. Kannada speech translation and Kannada intent formatting.
  3. Visual Intent Scene Generation — SVG / graphical scene descriptions
     for instant caregiver comprehension in a visual box.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from config import config
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GeminiAnalysisResult:
    """Output from Gemini dysarthric intent processing."""

    intent_category: str          # e.g. "Physical Need", "Medical / Pain", "Emotional", "Social"
    intent_summary: str           # e.g. "Patient wants to drink water"
    reconstructed_english: str   # Clean English sentence
    reconstructed_kannada: str   # Clean Kannada sentence (ಕನ್ನಡ ಮರುರಚನೆ)
    visual_scene_svg: str        # SVG string representing visual intent icon
    confidence: float
    is_gemini_active: bool


class GeminiService:
    """
    Google Gemini API integration service.

    Gracefully falls back to heuristic rule-based intent synthesis
    if GEMINI_API_KEY is not provided or network is unreachable.
    """

    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        self._api_key = api_key or config.gemini_api_key
        self._model_name = model_name or config.gemini_model or "gemini-2.5-flash"
        self._client = None

        if self._api_key:
            try:
                from google import genai  # noqa: PLC0415
                self._client = genai.Client(api_key=self._api_key)
                logger.info("GeminiService initialised | model=%s", self._model_name)
            except Exception as exc:
                logger.warning("Failed to initialize Google GenAI SDK: %s", exc)

    @property
    def is_available(self) -> bool:
        return self._client is not None or bool(self._api_key)

    def analyze_intent(
        self,
        raw_transcript: str,
        shield_transcript: str,
        target_language: str = "auto",
    ) -> GeminiAnalysisResult:
        """
        Analyze dysarthric transcript with Gemini for intent, Kannada translation,
        and graphical SVG scene generation.
        """
        input_text = shield_transcript.strip() or raw_transcript.strip()
        if not input_text or input_text == "[No speech detected]":
            return self._default_result("[No speech detected]")

        if self._client:
            try:
                prompt = f"""
You are an expert Speech-Language Pathologist and Dysarthric Speech AI Assistant.
Analyze the following dysarthric speech transcript:
Transcript: "{input_text}"

Task:
1. Identify the patient's core intent (Category: "Water/Food", "Pain/Medical", "Comfort", "Social", "Help").
2. Reconstruct the full clear sentence in English.
3. Reconstruct / translate the sentence in Kannada script (ಕನ್ನಡ).
4. Provide a simple, colorful SVG string (width="120" height="120") illustrating the intent visually (e.g. cup of water, heart, bed, food bowl, alert sign).

Return JSON only in this exact format:
{{
  "intent_category": "Category Name",
  "intent_summary": "Short 3-5 word summary",
  "reconstructed_english": "Clean English sentence",
  "reconstructed_kannada": "ಕನ್ನಡ ವಾಕ್ಯ",
  "visual_svg": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>...</svg>",
  "confidence": 0.95
}}
"""
                response = self._client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                )
                text_content = response.text or ""
                # Extract JSON block
                json_match = re.search(r"\{.*\}", text_content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                    return GeminiAnalysisResult(
                        intent_category=data.get("intent_category", "General"),
                        intent_summary=data.get("intent_summary", input_text),
                        reconstructed_english=data.get("reconstructed_english", input_text),
                        reconstructed_kannada=data.get("reconstructed_kannada", input_text),
                        visual_scene_svg=data.get("visual_svg", self._generate_default_svg("general")),
                        confidence=float(data.get("confidence", 0.9)),
                        is_gemini_active=True,
                    )
            except Exception as exc:
                logger.warning("Gemini API call failed (%s) — using fallback engine.", exc)

        # Fallback engine when Gemini API is offline or key not supplied
        return self._fallback_analysis(input_text, target_language)

    def _fallback_analysis(self, text: str, target_lang: str) -> GeminiAnalysisResult:
        """Rule-based intent and Kannada fallback."""
        lower = text.lower()
        category = "General Communication"
        summary = text
        kannada_tr = text
        icon_type = "speech"

        if any(w in lower for w in ("water", "drink", "thirsty", "pwease water", "bwing water")):
            category = "Physical Need — Hydration"
            summary = "Patient needs water"
            kannada_tr = "ದಯವಿಟ್ಟು ನನಗೆ ನೀರು ಕೊಡಿ (Bring me water)"
            icon_type = "water"
        elif any(w in lower for w in ("pain", "hurt", "doctor", "headache", "ouch")):
            category = "Medical — Pain Alert"
            summary = "Patient experiencing discomfort or pain"
            kannada_tr = "ನನಗೆ ನೋವಾಗುತ್ತಿದೆ, ಸಹಾಯ ಬೇಕು (I have pain, need help)"
            icon_type = "pain"
        elif any(w in lower for w in ("food", "eat", "hungry", "lunch", "dinner")):
            category = "Physical Need — Food"
            summary = "Patient wants food"
            kannada_tr = "ನನಗೆ ಊಟ ಬೇಕು (I want food)"
            icon_type = "food"
        elif any(w in lower for w in ("sleep", "tired", "bed", "rest")):
            category = "Comfort — Rest"
            summary = "Patient needs rest"
            kannada_tr = "ನನಗೆ ವಿಶ್ರಾಂತಿ ಬೇಕು (I need rest)"
            icon_type = "rest"
        else:
            kannada_tr = f"ಸಂದೇಶ: {text}"

        return GeminiAnalysisResult(
            intent_category=category,
            intent_summary=summary,
            reconstructed_english=text.capitalize(),
            reconstructed_kannada=kannada_tr,
            visual_scene_svg=self._generate_default_svg(icon_type),
            confidence=0.85,
            is_gemini_active=False,
        )

    def _default_result(self, msg: str) -> GeminiAnalysisResult:
        return GeminiAnalysisResult(
            intent_category="None",
            intent_summary=msg,
            reconstructed_english=msg,
            reconstructed_kannada=msg,
            visual_scene_svg=self._generate_default_svg("none"),
            confidence=0.0,
            is_gemini_active=False,
        )

    @staticmethod
    def _generate_default_svg(kind: str) -> str:
        """Generate clean, lightweight SVG icons for visual intent box."""
        colors = {
            "water": ("#38bdf8", "#0284c7", "💧"),
            "pain": ("#f87171", "#dc2626", "❤️‍🩹"),
            "food": ("#fbbf24", "#d97706", "🍲"),
            "rest": ("#a78bfa", "#7c3aed", "🌙"),
            "speech": ("#60a5fa", "#2563eb", "💬"),
        }
        bg, border, emoji = colors.get(kind, ("#818cf8", "#4f46e5", "🗣️"))
        return f"""<svg width="96" height="96" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect x="5" y="5" width="90" height="90" rx="20" fill="{bg}" fill-opacity="0.2" stroke="{border}" stroke-width="3"/>
  <circle cx="50" cy="50" r="32" fill="{bg}" fill-opacity="0.3"/>
  <text x="50" y="58" font-size="36" text-anchor="middle">{emoji}</text>
</svg>"""
