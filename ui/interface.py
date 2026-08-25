"""
NeuroSpeak-AI — Gradio Interface
===================================
Professional dashboard for major-project demonstration with 12 sections:

  1.  Patient / session information
  2.  Audio upload
  3.  Microphone recording
  4.  Raw transcription
  5.  Phonetic Shield output
  6.  Corrected transcription
  7.  Dysarthria severity (+ confidence)
  8.  Confidence score
  9.  Acoustic features
  10. Spectrogram
  11. Speech coaching
  12. Session history

The UI clearly displays GPU/CPU, ASR model, processing time, severity,
and corrected text. It avoids making medical diagnostic claims.
"""

from __future__ import annotations

import io
import json
from datetime import datetime

import gradio as gr
import numpy as np

# matplotlib — non-interactive backend for spectrogram image generation
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from audio.loader import AudioLoadError, load_from_file, load_from_microphone
from audio.preprocessor import AudioPreprocessError
from config import config
from pipeline import NeuroSpeakPipeline, PipelineResult
from severity.base import SeverityLevel
from ui.themes import CUSTOM_CSS, get_theme
from utils.device import cuda_info
from utils.logger import get_logger

logger = get_logger(__name__)

# Singleton pipeline (lazy model loading happens inside)
_pipeline = NeuroSpeakPipeline()

# Session state for patient info
_session_meta = {"patient_name": "", "patient_age": "", "session_note": ""}


# ─────────────────────────────────────────────────────────────────────────────
# HTML helpers
# ─────────────────────────────────────────────────────────────────────────────

def _severity_html(level: str, score: float, confidence: float) -> str:
    css_class = {
        "Mild": "severity-mild",
        "Moderate": "severity-moderate",
        "Severe": "severity-severe",
    }.get(level, "")

    icon = {"Mild": "🟢", "Moderate": "🟡", "Severe": "🔴"}.get(level, "⚪")

    return f"""
<div style="display:flex; align-items:center; gap:1rem; padding:1rem;
            background:#1e293b; border-radius:12px; border:1px solid #334155;">
  <div style="font-size:2.5rem;">{icon}</div>
  <div>
    <div style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase;
                letter-spacing:0.05em;">Dysarthria Severity (research estimate)</div>
    <div class="{css_class}" style="font-size:2rem;">{level}</div>
    <div style="font-size:0.8rem; color:#64748b;">
      Score: {score:.3f} · Confidence: {confidence:.0%}
    </div>
  </div>
</div>
"""


def _confidence_html(confidence: float, classifier: str) -> str:
    pct = max(0.0, min(1.0, confidence)) * 100
    color = "#22c55e" if pct >= 70 else "#f59e0b" if pct >= 40 else "#ef4444"
    return f"""
<div style="display:flex; align-items:center; gap:1rem; padding:1rem;
            background:#1e293b; border-radius:12px; border:1px solid #334155;">
  <div style="font-size:2rem;">🎯</div>
  <div style="flex:1;">
    <div style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase;
                letter-spacing:0.05em;">Classifier Confidence</div>
    <div style="font-size:1.6rem; font-weight:700; color:{color};">
      {pct:.1f}%
    </div>
    <div style="font-size:0.8rem; color:#64748b;">Backend: {classifier}</div>
  </div>
  <div style="width:80px; height:80px; border-radius:50%;
              background:conic-gradient({color} {pct}%, #334155 {pct}% 100%);">
    <div style="width:64px; height:64px; border-radius:50%; background:#1e293b;
                margin:8px auto; display:flex; align-items:center; justify-content:center;
                font-size:0.9rem; font-weight:700; color:#e2e8f0;">{pct:.0f}%</div>
  </div>
</div>
"""


def _acoustic_html(af_dict: dict) -> str:
    metrics = [
        ("🎵", "Avg Pitch", f"{af_dict.get('avg_pitch_hz', 0):.0f} Hz"),
        ("📊", "Pitch SD", f"{af_dict.get('pitch_sd_hz', 0):.1f} Hz"),
        ("⏸", "Pause Ratio", f"{af_dict.get('pause_ratio', 0):.1%}"),
        ("🔊", "Spectral Centroid", f"{af_dict.get('spectral_centroid_hz', 0):.0f} Hz"),
        ("⏱", "Duration", f"{af_dict.get('duration_sec', 0):.2f} s"),
        ("⚙️", "Method", str(af_dict.get("extraction_method", "N/A"))),
    ]

    cards = "".join(
        f"""<div class="ns-metric-card" style="flex:1; min-width:120px;">
              <div class="ns-metric-label">{icon} {label}</div>
              <div class="ns-metric-value" style="font-size:1.1rem;">{value}</div>
            </div>"""
        for icon, label, value in metrics
    )
    return f'<div style="display:flex; flex-wrap:wrap; gap:0.5rem; margin:0.5rem 0;">{cards}</div>'


def _coaching_html(recommendations: list[str]) -> str:
    if not recommendations:
        return "<p style='color:#64748b;'>No coaching recommendations available.</p>"
    items = "".join(
        f'<div class="ns-coaching-item"><strong>{i + 1}.</strong> {rec}</div>'
        for i, rec in enumerate(recommendations)
    )
    return f'<div style="margin:0.5rem 0;">{items}</div>'


def _agent_log_html(log: list[dict], ollama_available: bool, guard_triggered: bool) -> str:
    status = "🟢 Ollama connected" if ollama_available else "🟡 Ollama offline — fallback mode"
    guard_note = "⚠ Hallucination guard triggered" if guard_triggered else "✓ Guard: OK"

    if not log:
        lines = ["<span style='color:#64748b;'>No agent calls made.</span>"]
    else:
        lines = []
        for entry in log:
            role_color = "#818cf8" if entry["agent"] == "proposer" else "#86efac"
            lines.append(
                f"<span style='color:{role_color};'>[Round {entry['round'] + 1}]"
                f" {entry['agent'].upper()} ({entry['model']}):</span> "
                f"{entry['output'][:120]}{'…' if len(entry['output']) > 120 else ''}"
            )

    log_body = "<br>".join(lines)
    return f"""
<div style="margin-top:0.5rem;">
  <div style="font-size:0.8rem; color:#64748b; margin-bottom:0.5rem;">
    {status} &nbsp;·&nbsp; {guard_note}
  </div>
  <div class="ns-agent-log">{log_body}</div>
</div>
"""


def _system_banner_html(result: PipelineResult) -> str:
    """Clear display of GPU/CPU, ASR model, and processing time."""
    gpu = cuda_info()
    device_str = (
        f"<span class='status-dot-green'>{gpu.get('device_name', 'GPU')}</span>"
        if gpu.get("available")
        else "<span class='status-dot-amber'>CPU</span>"
    )
    return f"""
<div style="display:flex; flex-wrap:wrap; gap:1rem; padding:1rem;
            background:#1e293b; border-radius:12px; border:1px solid #334155;">
  <div><strong>Device:</strong> {device_str}</div>
  <div><strong>ASR:</strong> <code>{result.asr_provider}</code></div>
  <div><strong>Processed:</strong> {result.elapsed_seconds:.1f} s</div>
  <div><strong>Session:</strong> <code>{result.session_id[:8]}</code></div>
  <div><strong>Language:</strong> <code>{result.asr_language}</code></div>
</div>
"""


def _make_spectrogram(audio: np.ndarray, sr: int) -> str | None:
    """Generate a spectrogram PNG and return a data-URI or path."""
    try:
        import librosa  # noqa: PLC0415

        fig, ax = plt.subplots(figsize=(8, 3), dpi=100)
        fig.patch.set_facecolor("#1e293b")
        ax.set_facecolor("#0f172a")

        D = librosa.amplitude_to_db(
            np.abs(librosa.stft(audio, n_fft=2048, hop_length=512)),
            ref=np.max,
        )
        img = ax.imshow(
            D,
            aspect="auto",
            origin="lower",
            extent=(0.0, len(audio) / sr, 0.0, sr / 2),
            cmap="magma",
        )
        ax.set_title("Spectrogram", color="#e2e8f0", fontsize=10)
        ax.tick_params(colors="#94a3b8", labelsize=8)
        ax.set_xlabel("Time (s)", color="#94a3b8", fontsize=9)
        ax.set_ylabel("Frequency (Hz)", color="#94a3b8", fontsize=9)
        fig.colorbar(img, ax=ax, label="dB", fraction=0.02, pad=0.04)

        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        import base64  # noqa: PLC0415

        return "data:image/png;base64," + base64.b64encode(buf.read()).decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Spectrogram generation failed: %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Core processing function
# ─────────────────────────────────────────────────────────────────────────────

def _process(
    file_audio: str | None,
    mic_audio: tuple | None,
    patient_name: str,
    patient_age: str,
    session_note: str,
) -> tuple:
    """
    Process audio from either file upload or microphone.

    Returns:
        raw_tr, shield_tr, final_tr, severity_html, confidence_html,
        acoustic_html, spectrogram_img, coaching_html, agent_html,
        system_banner, status_md, warnings_md
    """
    _session_meta.update(
        {"patient_name": patient_name or "", "patient_age": patient_age or "", "session_note": session_note or ""}
    )
    EMPTY = (
        "", "", "", "", "", "", None, "", "",
        "", "⏳ Ready", "",
    )

    try:
        if file_audio:
            audio_input = load_from_file(file_audio)
        elif mic_audio is not None:
            sr, arr = mic_audio
            audio_input = load_from_microphone(sr, arr)
        else:
            return (
                "", "", "", "", "", "", None, "", "",
                "", "⚠ Please upload a file or record audio.", "",
            )

        result: PipelineResult = _pipeline.run(audio_input)

        # ── Assemble outputs ──────────────────────────────────────────────
        raw_tr = result.raw_transcript
        shield_tr = result.shield_transcript

        shield_note = ""
        if result.shield_changes:
            changes_str = ", ".join(result.shield_changes[:5])
            shield_note = f"\n\n*Phonetic corrections: {changes_str}*"

        final_tr = result.final_transcript

        sev_html = _severity_html(
            result.severity.level.value if hasattr(result.severity.level, "value")
            else str(result.severity.level),
            result.severity.score,
            result.severity.confidence,
        )

        conf_html = _confidence_html(
            result.severity.confidence, result.severity.classifier
        )

        ac_html = _acoustic_html(result.acoustic_features.to_dict())
        coach_html = _coaching_html(result.coaching_recommendations)
        agent_html = _agent_log_html(
            result.agent_log, result.ollama_available, result.guard_triggered
        )
        banner_html = _system_banner_html(result)

        # Spectrogram from the preprocessed audio
        spec_plt = _make_spectrogram(
            np.asarray(result.acoustic_features.to_dict().get("_audio", [])),
            16_000,
        )
        # Note: PipelineResult does not carry the raw audio array; generate
        # the spectrogram upstream is not possible here. We use a placeholder
        # and regenerate from the pipeline output in a future enhancement.
        # For now, return None and rely on the audio input widget.
        spec_plt = None

        status_md = (
            f"✅ **Done** — processed in **{result.elapsed_seconds:.1f} s** · "
            f"Session ID: `{result.session_id[:8]}` · "
            f"Language: `{result.asr_language}` · "
            f"Device: `{config.device}`"
        )

        warnings_md = ""
        if result.warnings:
            warnings_md = "⚠ **Warnings:**\n" + "\n".join(f"- {w}" for w in result.warnings)

        return (
            raw_tr,
            shield_tr + shield_note,
            final_tr,
            sev_html,
            conf_html,
            ac_html,
            spec_plt,
            coach_html,
            agent_html,
            banner_html,
            status_md,
            warnings_md,
        )

    except (AudioLoadError, AudioPreprocessError) as exc:
        msg = f"❌ Audio error: {exc}"
        logger.warning(msg)
        return ("", "", "", "", "", "", None, "", "", "", msg, "")

    except Exception as exc:  # noqa: BLE001
        msg = f"❌ Unexpected error: {exc}"
        logger.error(msg, exc_info=True)
        return ("", "", "", "", "", "", None, "", "", "", msg, "")


# ─────────────────────────────────────────────────────────────────────────────
# History tab helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_history() -> list[list]:
    """Load session history for the Gradio Dataframe."""
    sessions = _pipeline.get_history(limit=100)
    rows = []
    for s in sessions:
        rows.append([
            s.id[:8],
            s.timestamp.strftime("%Y-%m-%d %H:%M") if s.timestamp else "",
            s.source,
            f"{s.duration_seconds:.1f}s",
            s.severity_level,
            s.final_transcript[:80] + ("…" if len(s.final_transcript) > 80 else ""),
        ])
    return rows


def _delete_session(session_id_short: str) -> str:
    sessions = _pipeline.get_history(limit=200)
    matched = [s for s in sessions if s.id.startswith(session_id_short)]
    if not matched:
        return f"⚠ Session `{session_id_short}` not found."
    _pipeline.delete_session(matched[0].id)
    return f"✅ Deleted session `{session_id_short}`"


# ─────────────────────────────────────────────────────────────────────────────
# System info
# ─────────────────────────────────────────────────────────────────────────────

def _system_info_md() -> str:
    gpu = cuda_info()
    gpu_str = (
        f"**GPU:** {gpu.get('device_name', 'N/A')} ({gpu.get('total_memory_gb', 0)} GB)"
        if gpu.get("available") else "**GPU:** Not available — running on CPU"
    )
    return f"""
## System Status

| Setting | Value |
|---|---|
| Device | `{config.device}` |
| ASR Provider | `{config.asr_provider}` ({config.whisper_model}) |
| Embedding Provider | `{config.embedding_provider}` ({config.wav2vec2_model}) |
| Severity Classifier | `{config.severity_classifier}` |
| Proposer (LLM) | `{config.qwen_model}` via Ollama |
| Critic (LLM) | `{config.llama_model}` via Ollama |
| Ollama Host | `{config.ollama_host}` |
| Max Refine Rounds | `{config.max_refine_rounds}` |
| WPS Limit | `{config.words_per_second_limit}` |
| Severity Thresholds | Mild < `{config.severity_mild_max}` ≤ Moderate < `{config.severity_moderate_max}` |
| Database | `{config.database_url}` |

{gpu_str}

### NVIDIA Integration
- **NeMo ASR (experimental):** set `ASR_PROVIDER=nemo` in `.env` after installing `requirements-gpu.txt`
- **NeMo Embeddings:** set `EMBEDDING_PROVIDER=nemo` in `.env`
- Compare Whisper vs NeMo: `python experiments/whisper_vs_nemo/compare.py --audio files/*.wav`
"""


# ─────────────────────────────────────────────────────────────────────────────
# Build Gradio interface
# ─────────────────────────────────────────────────────────────────────────────

def build_interface() -> gr.Blocks:
    """Construct and return the full Gradio Blocks application."""

    with gr.Blocks(
        theme=get_theme(),
        css=CUSTOM_CSS,
        title="NeuroSpeak-AI",
        analytics_enabled=False,
    ) as app:

        # ── Header ──────────────────────────────────────────────────────────
        gr.HTML("""
        <div class="ns-header">
            <h1>🧠 NeuroSpeak-AI</h1>
            <p>AI-Powered Dysarthric Speech Recognition & Rehabilitation System — Research Dashboard</p>
        </div>
        """)

        with gr.Tabs():

            # ════════════════════════════════════════════════════════════════
            # TAB 1: ANALYSE — 12 sections
            # ════════════════════════════════════════════════════════════════
            with gr.TabItem("🎙 Analyse", id="tab-analyse"):
                with gr.Row():
                    # ── Left column: inputs ──────────────────────────────
                    with gr.Column(scale=1):
                        # Section 1: Patient / session info
                        gr.Markdown("### 1️⃣ Patient / Session")
                        patient_name = gr.Textbox(
                            label="Patient name (optional)",
                            placeholder="e.g. Patient A",
                        )
                        patient_age = gr.Textbox(
                            label="Age (optional)",
                            placeholder="e.g. 34",
                        )
                        session_note = gr.Textbox(
                            label="Session note (optional)",
                            placeholder="e.g. Reading passage 1",
                            lines=2,
                        )

                        # Section 2 & 3: Audio input
                        gr.Markdown("### 2️⃣ / 3️⃣ Audio Input")
                        with gr.Tab("📂 Upload File"):
                            file_audio = gr.Audio(
                                label="Upload WAV / MP3 / FLAC",
                                type="filepath",
                                elem_classes=["audio-upload-zone"],
                            )

                        with gr.Tab("🎤 Microphone"):
                            mic_audio = gr.Audio(
                                label="Record from Microphone",
                                sources=["microphone"],
                                type="numpy",
                                elem_classes=["audio-upload-zone"],
                            )

                        analyse_btn = gr.Button(
                            "▶ Analyse Speech",
                            variant="primary",
                            size="lg",
                        )
                        clear_btn = gr.Button("🗑 Clear", size="sm")

                        status_md = gr.Markdown("⏳ Ready — upload audio or record to begin.")
                        warnings_md = gr.Markdown(visible=True)

                    # ── Right column: results ────────────────────────────
                    with gr.Column(scale=2):
                        gr.Markdown("### Results")

                        # Section 11: System banner (GPU/CPU, ASR, time)
                        system_banner = gr.HTML()

                        with gr.Accordion("📝 Transcription Pipeline (4–6)", open=True):
                            # Section 4: Raw transcription
                            raw_tr = gr.Textbox(
                                label="4️⃣ Raw Transcription",
                                lines=2,
                                interactive=False,
                            )
                            # Section 5: Phonetic Shield output
                            shield_tr = gr.Textbox(
                                label="5️⃣ Phonetic Shield Output",
                                lines=2,
                                interactive=False,
                            )
                            # Section 6: Corrected transcription
                            final_tr = gr.Textbox(
                                label="6️⃣ Corrected Transcription (Multi-Agent)",
                                lines=3,
                                interactive=False,
                            )

                        with gr.Accordion("📊 Severity & Confidence (7–8)", open=True):
                            # Section 7: Severity
                            severity_html = gr.HTML()
                            # Section 8: Confidence
                            confidence_html = gr.HTML()

                        with gr.Accordion("🎛 Acoustic Features (9)", open=True):
                            acoustic_html = gr.HTML()

                        with gr.Accordion("🌈 Spectrogram (10)", open=False):
                            spectrogram_img = gr.Image(
                                type="pil",
                                label="Spectrogram",
                                height=240,
                                interactive=False,
                            )

                        with gr.Accordion("💡 Speech Coaching (11)", open=True):
                            coaching_html = gr.HTML()

                        with gr.Accordion("🤖 Multi-Agent Log", open=False):
                            agent_html = gr.HTML()

                # ── Event handlers ───────────────────────────────────────
                _all_outputs = [
                    raw_tr, shield_tr, final_tr,
                    severity_html, confidence_html,
                    acoustic_html, spectrogram_img,
                    coaching_html, agent_html,
                    system_banner, status_md, warnings_md,
                ]

                analyse_btn.click(
                    fn=_process,
                    inputs=[
                        file_audio, mic_audio,
                        patient_name, patient_age, session_note,
                    ],
                    outputs=_all_outputs,
                    show_progress="full",
                )

                def _clear():
                    return (
                        None, None,  # file_audio, mic_audio
                        "", "", "",  # patient fields
                        None, None,
                        "", "", "",  # transcripts
                        "", "", None,
                        "", "",
                        "", "", "",
                    )

                clear_btn.click(
                    fn=_clear,
                    outputs=[file_audio, mic_audio, patient_name, patient_age, session_note] + _all_outputs,
                )

            # ════════════════════════════════════════════════════════════════
            # TAB 2: HISTORY — section 12
            # ════════════════════════════════════════════════════════════════
            with gr.TabItem("📋 History", id="tab-history"):
                gr.Markdown("### 12️⃣ Session History")

                with gr.Row():
                    refresh_btn = gr.Button("🔄 Refresh", size="sm")
                    delete_id_box = gr.Textbox(
                        label="Session ID (first 8 chars) to delete",
                        placeholder="e.g. a1b2c3d4",
                        scale=2,
                    )
                    delete_btn = gr.Button("🗑 Delete", size="sm", variant="stop")
                    delete_status = gr.Markdown("")

                history_table = gr.Dataframe(
                    headers=["ID", "Timestamp", "Source", "Duration", "Severity", "Transcript"],
                    datatype=["str", "str", "str", "str", "str", "str"],
                    value=_load_history,
                    interactive=False,
                    elem_classes=["ns-history-table"],
                )

                refresh_btn.click(fn=_load_history, outputs=history_table)
                delete_btn.click(
                    fn=_delete_session,
                    inputs=delete_id_box,
                    outputs=delete_status,
                ).then(fn=_load_history, outputs=history_table)

            # ════════════════════════════════════════════════════════════════
            # TAB 3: SYSTEM INFO
            # ════════════════════════════════════════════════════════════════
            with gr.TabItem("⚙ System", id="tab-system"):
                gr.Markdown(_system_info_md())
                gr.Markdown("""
---
### Quick Setup

```bash
# 1. Install CPU dependencies
pip install -r requirements.txt

# 2. Pull Ollama models (required for multi-agent reconstruction)
ollama pull qwen2.5
ollama pull llama3.1

# 3. Copy and configure environment
cp .env.example .env

# 4. Run
python app.py
```

### GPU Upgrade Path
```bash
pip install -r requirements-gpu.txt
```

### Research Notes
- This system produces a **research estimate**, not a medical diagnosis.
- Severity classification is based on acoustic proxies and a heuristic/ML model.
- Consult a certified speech-language pathologist for clinical assessment.
""")

    return app