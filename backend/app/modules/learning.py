from __future__ import annotations

from app.ml.training import train_category_model
from app.repositories import tickets as ticket_repo


def queue_retrain(reason: str | None = None) -> dict:
    samples = ticket_repo.list_labeled_samples()
    labels = {label for _, label in samples}

    if len(samples) < 10 or len(labels) < 2:
        return {
            "status": "skipped",
            "message": "Not enough labeled data to train.",
            "samples": len(samples),
            "reason": reason,
        }

    try:
        metrics = train_category_model(samples)
        return {
            "status": "trained",
            "message": "Classification model trained.",
            "metrics": metrics,
            "reason": reason,
        }
    except Exception as exc:
        return {
            "status": "failed",
            "message": f"Training failed: {exc}",
            "samples": len(samples),
            "reason": reason,
        }
