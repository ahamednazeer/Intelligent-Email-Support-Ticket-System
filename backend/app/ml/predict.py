from __future__ import annotations

from app.ml import model_store


def predict_category(text: str) -> tuple[str, float] | None:
    model = model_store.get_model()
    if model is None:
        return None

    proba = model.predict_proba([text])[0]
    idx = int(proba.argmax())
    label = model.classes_[idx]
    confidence = float(proba[idx])
    return label, confidence
