"""
NeuroSpeak-AI — Severity Inference Script
============================================
Loads a trained severity classifier and runs inference on one or more
Wav2Vec2 embeddings.

Usage::

    # Single embedding
    python training/infer_severity.py --model ml_models/severity_model.joblib \\
        --embedding path/to/embedding.npy

    # Batch from .npz
    python training/infer_severity.py --model ml_models/severity_model.joblib \\
        --batch path/to/embeddings.npz --out results.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from severity.ml_classifier import LogisticRegressionSeverityClassifier
from utils.logger import get_logger

logger = get_logger(__name__)


def load_embedding(path: Path) -> np.ndarray:
    """Load a single embedding from a .npy file."""
    emb: np.ndarray = np.load(path)
    if emb.ndim != 1:
        raise ValueError(f"Expected 1-D embedding; got shape {emb.shape}")
    return emb.astype(np.float32)


def load_batch(path: Path) -> np.ndarray:
    """Load a batch of embeddings from an .npz file with key 'X'."""
    data = np.load(path)
    X: np.ndarray = data["X"]
    if X.ndim != 2:
        raise ValueError(f"Expected 2-D batch; got shape {X.shape}")
    return X.astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run severity inference.")
    parser.add_argument(
        "--model", type=Path, required=True, help="Path to trained model (.joblib)."
    )
    parser.add_argument(
        "--embedding", type=Path, help="Path to a single .npy embedding file."
    )
    parser.add_argument(
        "--batch", type=Path, help="Path to .npz with key X for batch inference."
    )
    parser.add_argument(
        "--out", type=Path, default=None, help="JSON output path for batch results."
    )
    args = parser.parse_args()

    if not args.model.exists():
        raise FileNotFoundError(f"Model not found: {args.model}")

    classifier = LogisticRegressionSeverityClassifier.load(args.model)

    if args.embedding:
        emb = load_embedding(args.embedding)
        result = classifier.classify(emb, {})
        print(
            json.dumps(
                {
                    "level": result.level.value,
                    "score": result.score,
                    "confidence": result.confidence,
                    "classifier": result.classifier,
                },
                indent=2,
            )
        )

    if args.batch:
        X = load_batch(args.batch)
        results = []
        for i in range(X.shape[0]):
            res = classifier.classify(X[i], {})
            results.append(
                {
                    "sample": i,
                    "level": res.level.value,
                    "score": res.score,
                    "confidence": res.confidence,
                }
            )
        if args.out:
            args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
            logger.info("Batch results written to %s", args.out)
        else:
            print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()