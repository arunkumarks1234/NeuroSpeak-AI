"""
NeuroSpeak-AI — Severity Evaluation Metrics
=============================================
Provides a standard evaluation report for severity classifiers:

- Accuracy
- Precision (macro)
- Recall (macro)
- F1-score (macro)
- Confusion matrix

The evaluation runs on train/split data from labelled Wav2Vec2 embeddings.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report as sklearn_classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


@dataclass
class EvaluationReport:
    """Structured evaluation output."""

    accuracy: float
    precision: float
    recall: float
    f1: float
    confusion_matrix: np.ndarray
    labels: list[str] = field(default_factory=list)
    classification_report: str = ""

    def to_dict(self) -> dict:
        return {
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "confusion_matrix": self.confusion_matrix.tolist(),
            "labels": self.labels,
        }

    def __str__(self) -> str:
        lines = [
            "── Severity Evaluation ──────────────────────────",
            f"Accuracy : {self.accuracy:.4f}",
            f"Precision: {self.precision:.4f}",
            f"Recall   : {self.recall:.4f}",
            f"F1 Score : {self.f1:.4f}",
        ]
        if self.classification_report:
            lines.append("\nClassification report:\n" + self.classification_report)
        lines.append("\nConfusion matrix:\n" + str(self.confusion_matrix))
        return "\n".join(lines)


def evaluate(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: list[str] | None = None,
) -> EvaluationReport:
    """
    Compute standard classification metrics.

    Args:
        y_true: Ground-truth label indices.
        y_pred: Predicted label indices.
        labels: Optional ordered class labels for the report.

    Returns:
        :class:`EvaluationReport` with accuracy, precision, recall, F1,
        and a confusion matrix.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if y_true.size == 0 or y_pred.size != y_true.size:
        raise ValueError("y_true and y_pred must share a non-empty length.")

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    rec = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    cm = confusion_matrix(y_true, y_pred)

    report_str: str = ""
    if labels:
        report_str = str(
            sklearn_classification_report(
                y_true,
                y_pred,
                target_names=labels,
                zero_division=0,
                output_dict=False,
            )
        )

    return EvaluationReport(
        accuracy=acc,
        precision=prec,
        recall=rec,
        f1=f1,
        confusion_matrix=cm,
        labels=list(labels) if labels else [],
        classification_report=report_str,
    )