.PHONY: run test lint format install setup-ollama clean help

PYTHON := python
PIP    := pip
OLLAMA := ollama

## ─── Help ────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  NeuroSpeak-AI — Available commands"
	@echo "  ──────────────────────────────────"
	@echo "  make install       Install CPU dependencies"
	@echo "  make install-gpu   Install GPU (CUDA) dependencies"
	@echo "  make setup-ollama  Pull Qwen 2.5 + Llama 3.1 models via Ollama"
	@echo "  make run           Launch the Gradio web interface"
	@echo "  make test          Run all tests"
	@echo "  make lint          Lint with ruff"
	@echo "  make format        Auto-format with ruff"
	@echo "  make clean         Remove cache artefacts"
	@echo ""

## ─── Install ──────────────────────────────────────────────────────────────────
install:
	$(PIP) install -r requirements.txt

install-gpu:
	$(PIP) install -r requirements.txt -r requirements-gpu.txt

## ─── Ollama setup ─────────────────────────────────────────────────────────────
setup-ollama:
	@echo "[NeuroSpeak] Pulling Qwen 2.5 (proposer agent)..."
	$(OLLAMA) pull qwen2.5
	@echo "[NeuroSpeak] Pulling Llama 3.1 (critic agent)..."
	$(OLLAMA) pull llama3.1
	@echo "[NeuroSpeak] Ollama models ready."

## ─── Run ──────────────────────────────────────────────────────────────────────
run:
	$(PYTHON) app.py

## ─── Test ─────────────────────────────────────────────────────────────────────
test:
	$(PYTHON) -m pytest tests/ -v --tb=short

test-cov:
	$(PYTHON) -m pytest tests/ -v --tb=short --cov=. --cov-report=term-missing

## ─── Lint / Format ────────────────────────────────────────────────────────────
lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .

## ─── Clean ────────────────────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "[NeuroSpeak] Clean complete."
