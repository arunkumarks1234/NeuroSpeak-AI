# 🧠 NeuroSpeak-AI

An AI-powered dysarthric speech recognition and rehabilitation system designed for production use. It combines state-of-the-art ASR (Whisper Large V3), a multi-agent semantic reconstruction engine (Qwen 2.5 + Llama 3.1 via Ollama), acoustic feature extraction (Praat), and speech embeddings (Wav2Vec2) into a cohesive Gradio application.

The architecture is **NVIDIA-ready** — with abstract base classes and provider registries that allow you to drop in NeMo ASR, NeMo Embeddings, or Riva gRPC clients by changing a single `.env` value.

## 🚀 Quickstart (Local CPU)

```bash
# 1. Clone & enter directory
cd NeuroSpeak-AI

# 2. Create a virtual environment (Python 3.10+)
python -m venv venv
source venv/bin/activate  # on Windows: .\venv\Scripts\activate

# 3. Install core dependencies
make install

# 4. Start Ollama and pull required agents (ensure Ollama is installed on your OS)
make setup-ollama

# 5. Configure environment (optional, defaults are fine for CPU)
cp .env.example .env

# 6. Launch the Gradio UI
make run
```

## 🏎️ NVIDIA GPU Upgrade Path

To unlock 10–30× inference speedups (especially on Whisper and Wav2Vec2):

1. Ensure you have the CUDA 12.x toolkit installed.
2. Install the GPU dependencies instead of CPU:
   ```bash
   make install-gpu
   ```
3. Set `DEVICE=cuda` in your `.env`.

### Integrating NeMo / Riva

The `asr/base.py` and `embeddings/base.py` define clean abstract interfaces. We have provided architectural stubs in `providers/`. 

To activate NeMo ASR:
1. Uncomment `nvidia-nemo[asr]` in `requirements-gpu.txt` and install.
2. Download a `.nemo` checkpoint.
3. Edit `.env`:
   ```env
   ASR_PROVIDER=nemo
   NEMO_MODEL_PATH=/path/to/model.nemo
   ```

## 🏗️ Architecture

NeuroSpeak-AI is split into 8 modular packages:

1. **`audio/`**: Normalises inbound speech to 16 kHz mono float32.
2. **`asr/`**: Transcribes speech. Includes a configurable `PhoneticShield` for common dysarthric substitutions.
3. **`agents/`**: Qwen 2.5 proposes semantic reconstructions; Llama 3.1 critiques and refines. Constrained by an audio-duration `HallucinationGuard`.
4. **`embeddings/`**: Wav2Vec2-large extracts 1024-D speech vectors.
5. **`severity/`**: Classifies speech as Mild/Moderate/Severe using a tunable heuristic scoring engine.
6. **`acoustics/`**: Uses `parselmouth` (Praat) to extract pathological-grade pitch, pause ratios, and spectral centroids.
7. **`coaching/`**: Uses the LLM to generate personalised rehab exercises based on the acoustic profile.
8. **`storage/`**: Persists every session to SQLite (swappable to PostgreSQL) for longitudinal analysis.

## 🛠️ Development Commands

```bash
make test       # Run pytest test suite
make lint       # Run Ruff linter
make format     # Auto-format codebase
make clean      # Clear cache files
```
