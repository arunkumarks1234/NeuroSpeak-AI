# ml_models/ — Trained Severity Classifier Models

This directory stores serialised scikit-learn model artefacts for the
**severity classifier** subsystem.

## File Format

| File | Created by | Description |
|------|-----------|-------------|
| `severity_model.joblib` | `training/train_severity.py` | Trained LogisticRegression + LabelEncoder |

## Training

Train the classifier on labelled Wav2Vec2 embeddings:

```bash
python training/train_severity.py \
    --data data/labelled_embeddings.npz \
    --out ml_models/severity_model.joblib
```

Expected `.npz` format:
- `X` — `(n_samples, 768)` float32 embedding matrix
- `y` — `(n_samples,)` integer labels (0=Mild, 1=Moderate, 2=Severe)

## Activation

Set `SEVERITY_CLASSIFIER=ml` in `.env` to enable the ML backend.
The system automatically falls back to the heuristic classifier if no
model file is present at the configured `SEVERITY_MODEL_PATH`.

## Git Ignored

`.joblib` and `.pkl` files in this directory are excluded from version
control. Store large model files in your cloud storage or a model registry.
