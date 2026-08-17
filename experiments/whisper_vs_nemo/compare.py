"""
NeuroSpeak-AI — Whisper vs NeMo ASR Comparison Script
========================================================
Compares Whisper and NeMo transcriptions on the same audio files:

- Whisper transcription
- NeMo transcription
- Inference time for each
- WER when reference transcripts are available

Usage::

    # With references (computes WER):
    python experiments/whisper_vs_nemo/compare.py --audio audio/*.wav \\
        --references references.csv --nemo-model path/to/model.nemo

    # Without references (only transcription + timing):
    python experiments/whisper_vs_nemo/compare.py --audio audio/*.wav \\
        --nemo-model path/to/model.nemo --no-refs
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from pathlib import Path

import numpy as np

from asr.whisper_provider import WhisperProvider
from services.nemo_asr import NemoASRService
from utils.logger import get_logger

logger = get_logger(__name__)


def wer(reference: str, hypothesis: str) -> float:
    """Compute Word Error Rate (lower is better)."""
    ref_words = reference.strip().lower().split()
    hyp_words = hypothesis.strip().lower().split()
    if not ref_words:
        return 1.0 if hyp_words else 0.0

    n = len(ref_words)
    m = len(hyp_words)

    # DP Levenshtein over words
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # deletion
                dp[i][j - 1] + 1,      # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )
    return dp[n][m] / n


def load_audio(path: Path) -> tuple[np.ndarray, int]:
    """Load an audio file at 16 kHz mono float32 using librosa."""
    import librosa  # noqa: PLC0415

    audio: np.ndarray
    sr_float: float
    audio, sr_float = librosa.load(str(path), sr=16_000, mono=True, dtype=np.float32)
    return audio, int(sr_float)


def load_references(path: Path) -> dict[str, str]:
    """Load a CSV mapping file basename → reference transcript."""
    refs: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            name = row.get("file", "")
            text = row.get("reference", "")
            if name:
                refs[Path(name).stem] = text
    return refs


def main() -> None:
    parser = argparse.ArgumentParser(description="Whisper vs NeMo comparison.")
    parser.add_argument("--audio", nargs="+", type=Path, required=True, help="Audio files.")
    parser.add_argument(
        "--nemo-model",
        type=Path,
        help="Path to .nemo checkpoint. Required for NeMo side.",
    )
    parser.add_argument(
        "--references",
        type=Path,
        help="CSV with 'file' and 'reference' columns for WER.",
    )
    parser.add_argument("--json", type=Path, default=None, help="Output JSON results path.")
    args = parser.parse_args()

    whisper = WhisperProvider()
    nemo = NemoASRService(model_path=args.nemo_model) if args.nemo_model else None

    refs = load_references(args.references) if args.references else {}

    results: list[dict] = []
    for audio_path in args.audio:
        audio, sr = load_audio(audio_path)
        key = audio_path.stem
        ref_text = refs.get(key, "")

        row: dict = {"file": str(audio_path), "duration_s": round(len(audio) / sr, 2)}

        # ── Whisper ────────────────────────────────────────────────────────
        t0 = time.perf_counter()
        w_result = whisper.transcribe(audio, sr)
        row["whisper_time_s"] = round(time.perf_counter() - t0, 3)
        row["whisper_text"] = w_result.transcript
        if ref_text:
            row["whisper_wer"] = round(wer(ref_text, w_result.transcript), 4)

        # ── NeMo ───────────────────────────────────────────────────────────
        if nemo is not None:
            t0 = time.perf_counter()
            n_result = nemo.transcribe(audio, sr)
            row["nemo_time_s"] = round(time.perf_counter() - t0, 3)
            row["nemo_text"] = n_result.transcript
            if ref_text:
                row["nemo_wer"] = round(wer(ref_text, n_result.transcript), 4)

        results.append(row)
        logger.info("Compared %s | whisper=%.3fs nemo=%.3fs", audio_path.name,
                    row.get("whisper_time_s", -1), row.get("nemo_time_s", -1))

    # ── Summary ─────────────────────────────────────────────────────────────
    summary = {"whisper_avg_time": None, "nemo_avg_time": None}
    w_times = [r["whisper_time_s"] for r in results if "whisper_time_s" in r]
    n_times = [r["nemo_time_s"] for r in results if "nemo_time_s" in r]
    if w_times:
        summary["whisper_avg_time"] = round(statistics.mean(w_times), 3)
    if n_times:
        summary["nemo_avg_time"] = round(statistics.mean(n_times), 3)

    w_wers = [r["whisper_wer"] for r in results if "whisper_wer" in r]
    n_wers = [r["nemo_wer"] for r in results if "nemo_wer" in r]
    if w_wers:
        summary["whisper_avg_wer"] = round(statistics.mean(w_wers), 4)
    if n_wers:
        summary["nemo_avg_wer"] = round(statistics.mean(n_wers), 4)

    print(json.dumps({"results": results, "summary": summary}, indent=2))

    if args.json:
        args.json.write_text(
            json.dumps({"results": results, "summary": summary}, indent=2),
            encoding="utf-8",
        )
        logger.info("Results written to %s", args.json)


if __name__ == "__main__":
    main()