from __future__ import annotations

from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score

from app.ml import model_store


def train_category_model(samples: Iterable[tuple[str, str]]) -> dict:
    texts = [s[0] for s in samples]
    labels = [s[1] for s in samples]

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    solver="lbfgs",
                    multi_class="auto",
                ),
            ),
        ]
    )

    pipeline.fit(texts, labels)
    preds = pipeline.predict(texts)
    acc = accuracy_score(labels, preds)

    model_store.save_model(pipeline)

    return {
        "samples": len(texts),
        "accuracy": round(float(acc), 4),
        "classes": sorted(set(labels)),
    }
