"""
NeuroSpeak-AI — NeMo ASR Fine-Tuning Script (Scaffold)
========================================================
Scaffold for fine-tuning a NeMo ASR model on dysarthric speech data.

This script is intentionally minimal: NeMo fine-tuning for production
typically requires a data manifest, an experiment config, and GPU training
infrastructure. The scaffold provides the entry point and CLI contract.

Do NOT run this on CPU — NeMo training requires an NVIDIA GPU.

Usage::

    python training/nemo/finetune.py \
        --pretrained stt_en_conformer_ctc_medium \
        --manifest data/train_manifest.json \
        --epochs 20 \
        --out checkpoints/nemo_finetuned.nemo
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune NeMo ASR.")
    parser.add_argument(
        "--pretrained",
        type=str,
        required=True,
        help="Pretrained NeMo model name or .nemo path.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="NeMo manifest JSONL file with 'audio_filepath' and 'text'.",
    )
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--out", type=Path, default=Path("checkpoints/nemo_finetuned.nemo"))
    parser.add_argument("--min-train-duration", type=float, default=0.5)
    parser.add_argument("--max-train-duration", type=float, default=20.0)
    args = parser.parse_args()

    # Validate prerequisites without importing the heavy NeMo library
    if not args.manifest.exists():
        raise FileNotFoundError(f"Manifest not found: {args.manifest}")
    if not args.manifest.suffix == ".json" and not args.manifest.suffix == ".jsonl":
        raise ValueError("Manifest must be a .json/.jsonl NeMo manifest.")

    try:
        import torch  # noqa: PLC0415
    except ImportError as exc:
        raise SystemExit("PyTorch is required for NeMo fine-tuning.") from exc

    if not torch.cuda.is_available():
        raise SystemExit(
            "CUDA GPU required for NeMo fine-tuning. "
            "Install NVIDIA drivers + CUDA 12.x and reinstall PyTorch with CUDA."
        )

    # ---- Fine-tuning implementation goes here --------------------------------
    # 1. Load pretrained model:  nemo_asr.models.EncDecCTCModel.from_pretrained(pretrained)
    # 2. Build ASRDataLayer from the manifest
    # 3. Configure optimiser (AdamW), scheduler, and lightning trainer
    # 4. train_dataloader / val_dataloader
    # 5. trainer.fit(model)
    # 6. model.save_to(out)

    print(
        "NeMo fine-tuning scaffold ready. "
        "Implement the training loop with a NeMo experiment config "
        "(see nemo_finetune.yaml) and your dysarthria dataset."
    )


if __name__ == "__main__":
    main()