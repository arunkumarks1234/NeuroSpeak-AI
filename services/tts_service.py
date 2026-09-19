"""
NeuroSpeak-AI — Text-to-Speech (TTS) Voice Synthesis Service
==============================================================
Synthesizes voice audio for reconstructed speech in English and Kannada (ಕನ್ನಡ).
Uses `gTTS` (Google Text-to-Speech) and converts to data-URI / audio files
for instant playback in the Web UI.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

from config import config
from utils.logger import get_logger

logger = get_logger(__name__)

_TTS_CACHE_DIR = config.data_dir / "tts"
_TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class TTSService:
    """Voice output synthesis service for English and Kannada."""

    def __init__(self) -> None:
        self._enabled = config.tts_enabled

    def synthesize(self, text: str, lang: str = "en") -> tuple[str | None, str | None]:
        """
        Synthesize speech from text.

        Args:
            text: Text to convert to voice audio.
            lang: "en" for English, "kn" for Kannada.

        Returns:
            Tuple of (audio_file_path, base64_data_uri).
        """
        if not text or text == "[No speech detected]" or not self._enabled:
            return None, None

        # Clean text for TTS
        clean_text = text.strip()
        if "(" in clean_text and ")" in clean_text:
            clean_text = clean_text.split("(")[0].strip()

        try:
            from gtts import gTTS  # noqa: PLC0415

            # Map language code
            tts_lang = "kn" if lang in ("kn", "kannada") or self._has_kannada_script(clean_text) else "en"

            tts = gTTS(text=clean_text, lang=tts_lang, slow=False)

            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            audio_bytes = buf.read()

            # Create base64 Data URI for immediate HTML5 audio playback
            b64_str = base64.b64encode(audio_bytes).decode("utf-8")
            data_uri = f"data:audio/mp3;base64,{b64_str}"

            # Save to temporary file in data/tts
            import uuid  # noqa: PLC0415
            file_path = _TTS_CACHE_DIR / f"speech_{uuid.uuid4().hex[:8]}.mp3"
            file_path.write_bytes(audio_bytes)

            logger.info("TTS synthesized | lang=%s | bytes=%d", tts_lang, len(audio_bytes))
            return str(file_path), data_uri

        except Exception as exc:  # noqa: BLE001
            logger.warning("TTS synthesis failed (%s).", exc)
            return None, None

    @staticmethod
    def _has_kannada_script(text: str) -> bool:
        """Detect Kannada Unicode character range (U+0C80..U+0CFF)."""
        return any('\u0c80' <= char <= '\u0cff' for char in text)
