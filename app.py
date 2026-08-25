"""
NeuroSpeak-AI — Entry Point
=============================
Main application runner.
Sets up the logger and launches the Gradio server.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path so modules can be imported
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from config import config
from ui.interface import build_interface
from utils.logger import get_logger

logger = get_logger("neurospeak_ai")


def main() -> None:
    """Launch the NeuroSpeak-AI Gradio application."""
    logger.info("Starting NeuroSpeak-AI...")
    logger.info("Device: %s", config.device)
    logger.info("ASR Provider: %s", config.asr_provider)

    app = build_interface()

    logger.info("Pre-warming ASR and Embedding models for fast inference...")
    try:
        from ui.interface import _pipeline
        _pipeline._get_asr().warm_up()
        _pipeline._get_embedding().warm_up()
        logger.info("Models pre-warmed and ready in RAM.")
    except Exception as exc:
        logger.warning("Pre-warm note: %s", exc)

    try:
        app.launch(
            server_name=config.gradio_server_name,
            server_port=config.gradio_server_port,
            share=config.gradio_share,
        )
    except Exception as exc:
        logger.critical("Failed to launch Gradio server: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
