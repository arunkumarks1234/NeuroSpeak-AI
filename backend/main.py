"""
NeuroSpeak-AI — Enhanced FastAPI Main Application
====================================================
Extends the original FastAPI backend with:
  - CORS for Next.js frontend (localhost:3000)
  - New pronunciation assessment router
  - Gamification endpoints
  - Clinician monitoring panel
  - Auth endpoints (simplified session-based)
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from . import models
from .routes import router as legacy_router
from .api import router as api_router

# Create all tables (idempotent)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NeuroSpeak-AI API",
    description="Gamified Speech Therapy & Pronunciation Assessment Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:7860",  # Gradio (legacy)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(legacy_router)  # Original /api/v1 routes preserved
app.include_router(api_router)     # New /api/v2 routes


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0", "service": "NeuroSpeak-AI"}
