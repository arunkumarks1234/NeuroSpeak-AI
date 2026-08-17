"""
NeuroSpeak-AI — NeMo Training Scaffolding
============================================
This package contains scripts and configuration for fine-tuning NVIDIA NeMo
ASR models on dysarthric speech data.

Usage::

    # 1. Prepare your data in NeMo manifest format (see nemo_manifest.md)
    # 2. Configure training hyperparameters in config/nemo_finetune.yaml
    # 3. Run fine-tuning
    python training/nemo/finetune.py --config config/nemo_finetune.yaml

Requirements:
    - nvidia-nemo  (pip install nvidia-nemo[asr])
    - CUDA-capable GPU
    - NeMo-compatible ASR checkpoint (e.g. stt_en_conformer_ctc_medium)
"""