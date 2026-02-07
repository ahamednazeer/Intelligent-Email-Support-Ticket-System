from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

MODEL_PATH = Path(__file__).resolve().parents[3] / "backend" / "data" / "models" / "category_model.joblib"

_model_cache: Any | None = None


def get_model() -> Any | None:
    global _model_cache
    if _model_cache is None and MODEL_PATH.exists():
        _model_cache = joblib.load(MODEL_PATH)
    return _model_cache


def save_model(model: Any) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    global _model_cache
    _model_cache = model
