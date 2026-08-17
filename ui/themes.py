"""
NeuroSpeak-AI — Gradio Theme Configuration
============================================
Custom Gradio Soft theme with a medical-grade, accessible colour palette.
"""

from __future__ import annotations

import gradio as gr


def get_theme() -> gr.themes.Base:
    """Return the NeuroSpeak-AI custom Gradio theme."""
    return gr.themes.Soft(
        primary_hue=gr.themes.Color(
            c50="#eef2ff",
            c100="#e0e7ff",
            c200="#c7d2fe",
            c300="#a5b4fc",
            c400="#818cf8",
            c500="#6366f1",
            c600="#4f46e5",
            c700="#4338ca",
            c800="#3730a3",
            c900="#312e81",
            c950="#1e1b4b",
        ),
        secondary_hue=gr.themes.Color(
            c50="#f0fdf4",
            c100="#dcfce7",
            c200="#bbf7d0",
            c300="#86efac",
            c400="#4ade80",
            c500="#22c55e",
            c600="#16a34a",
            c700="#15803d",
            c800="#166534",
            c900="#14532d",
            c950="#052e16",
        ),
        neutral_hue=gr.themes.Color(
            c50="#f8fafc",
            c100="#f1f5f9",
            c200="#e2e8f0",
            c300="#cbd5e1",
            c400="#94a3b8",
            c500="#64748b",
            c600="#475569",
            c700="#334155",
            c800="#1e293b",
            c900="#0f172a",
            c950="#020617",
        ),
        font=[
            gr.themes.GoogleFont("Inter"),
            gr.themes.GoogleFont("JetBrains Mono"),
            "ui-sans-serif",
            "system-ui",
        ],
        font_mono=[
            gr.themes.GoogleFont("JetBrains Mono"),
            "ui-monospace",
            "monospace",
        ],
    ).set(
        # Layout
        body_background_fill="#0f172a",
        body_background_fill_dark="#0f172a",
        body_text_color="#e2e8f0",
        body_text_color_dark="#e2e8f0",
        # Blocks / containers
        block_background_fill="#1e293b",
        block_background_fill_dark="#1e293b",
        block_border_color="#334155",
        block_border_color_dark="#334155",
        block_label_text_color="#94a3b8",
        block_label_text_color_dark="#94a3b8",
        block_title_text_color="#e2e8f0",
        block_title_text_color_dark="#e2e8f0",
        block_radius="12px",
        block_shadow="0 4px 24px 0 rgba(0,0,0,0.4)",
        # Inputs
        input_background_fill="#0f172a",
        input_background_fill_dark="#0f172a",
        input_border_color="#334155",
        input_border_color_dark="#334155",
        input_border_color_focus="#6366f1",
        input_border_color_focus_dark="#6366f1",
        input_radius="8px",
        # Buttons
        button_primary_background_fill="linear-gradient(135deg, #6366f1, #4f46e5)",
        button_primary_background_fill_hover="linear-gradient(135deg, #4f46e5, #4338ca)",
        button_primary_text_color="#ffffff",
        button_secondary_background_fill="#1e293b",
        button_secondary_background_fill_hover="#334155",
        button_secondary_text_color="#e2e8f0",
        button_border_width="1px",
        button_large_radius="8px",
        button_small_radius="6px",
        # Tabs
        border_color_primary="#334155",
        # Typography
        body_text_size="14px",
        block_label_text_size="12px",
    )


# CSS injected into the Gradio interface for additional polish
CUSTOM_CSS = """
/* ── Global ──────────────────────────────────────────────────────────────── */
:root {
    --ns-indigo: #6366f1;
    --ns-green: #22c55e;
    --ns-amber: #f59e0b;
    --ns-red: #ef4444;
    --ns-slate-900: #0f172a;
    --ns-slate-800: #1e293b;
    --ns-slate-700: #334155;
    --ns-slate-400: #94a3b8;
    --ns-slate-200: #e2e8f0;
}

/* ── Header banner ────────────────────────────────────────────────────────── */
.ns-header {
    background: linear-gradient(135deg, #312e81 0%, #1e1b4b 50%, #0f172a 100%);
    border-bottom: 1px solid #334155;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
}

.ns-header::before {
    content: "";
    position: absolute;
    top: -40%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%);
    pointer-events: none;
}

.ns-header h1 {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #a5b4fc, #818cf8, #6366f1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -0.02em;
}

.ns-header p {
    color: #94a3b8;
    font-size: 0.95rem;
    margin: 0.4rem 0 0;
}

/* ── Severity badge ────────────────────────────────────────────────────────── */
.severity-mild    { color: #22c55e; font-weight: 700; }
.severity-moderate { color: #f59e0b; font-weight: 700; }
.severity-severe  { color: #ef4444; font-weight: 700; }

/* ── Metric cards ────────────────────────────────────────────────────────────*/
.ns-metric-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin: 0.25rem;
}

.ns-metric-label {
    font-size: 0.75rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.25rem;
}

.ns-metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #e2e8f0;
    font-family: "JetBrains Mono", monospace;
}

/* ── Pipeline timeline ───────────────────────────────────────────────────── */
.ns-step {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid #1e293b;
    font-size: 0.85rem;
    color: #94a3b8;
}

.ns-step-done  { color: #22c55e; }
.ns-step-active { color: #6366f1; }

/* ── Coaching recommendations ────────────────────────────────────────────── */
.ns-coaching-item {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border-left: 3px solid #6366f1;
    border-radius: 0 8px 8px 0;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    line-height: 1.6;
}

/* ── Agent log ────────────────────────────────────────────────────────────── */
.ns-agent-log {
    font-family: "JetBrains Mono", monospace;
    font-size: 0.78rem;
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 1rem;
    max-height: 200px;
    overflow-y: auto;
    color: #64748b;
}

/* ── Accordion override ────────────────────────────────────────────────────── */
.label-wrap { font-size: 0.9rem !important; }

/* ── History table ─────────────────────────────────────────────────────────── */
.ns-history-table { font-size: 0.82rem; }

/* ── Warning banner ────────────────────────────────────────────────────────── */
.ns-warning {
    background: rgba(245,158,11,0.1);
    border: 1px solid rgba(245,158,11,0.3);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-size: 0.85rem;
    color: #fcd34d;
}

/* ── Status dot ─────────────────────────────────────────────────────────────── */
.status-dot-green::before { content: "●"; color: #22c55e; margin-right: 0.4rem; }
.status-dot-amber::before { content: "●"; color: #f59e0b; margin-right: 0.4rem; }
.status-dot-red::before   { content: "●"; color: #ef4444; margin-right: 0.4rem; }

/* ── Upload zone ─────────────────────────────────────────────────────────────── */
.audio-upload-zone {
    border: 2px dashed #334155 !important;
    border-radius: 12px !important;
    transition: border-color 0.2s ease;
}
.audio-upload-zone:hover {
    border-color: #6366f1 !important;
}
"""
