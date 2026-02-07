from __future__ import annotations

from app.schemas import ClassificationResult, PreprocessResult, PriorityResult
from app.utils.time import add_hours_iso

_URGENCY_KEYWORDS = {
    "urgent",
    "asap",
    "immediately",
    "down",
    "outage",
    "not working",
    "critical",
}

_NEGATIVE_WORDS = {
    "angry",
    "upset",
    "bad",
    "terrible",
    "unacceptable",
    "broken",
    "frustrated",
    "issue",
    "problem",
}

_BASE_PRIORITY = {
    "technical": "MEDIUM",
    "billing": "MEDIUM",
    "account": "MEDIUM",
    "complaint": "HIGH",
    "feature_request": "LOW",
    "general": "LOW",
}

_PRIORITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

_SLA_HOURS = {
    "CRITICAL": 4,
    "HIGH": 24,
    "MEDIUM": 72,
    "LOW": 120,
}


def _bump(priority: str, steps: int = 1) -> str:
    idx = _PRIORITY_ORDER.index(priority)
    idx = min(len(_PRIORITY_ORDER) - 1, idx + steps)
    return _PRIORITY_ORDER[idx]


def predict_priority(
    preprocess: PreprocessResult,
    classification: ClassificationResult,
    customer_tier: str | None = None,
) -> PriorityResult:
    text = preprocess.cleaned_text
    tokens = preprocess.tokens
    urgency_hits = sum(1 for kw in _URGENCY_KEYWORDS if kw in text)
    negative_hits = sum(1 for t in tokens if t in _NEGATIVE_WORDS)
    sentiment_score = -min(1.0, negative_hits / max(1, len(tokens)))

    priority = _BASE_PRIORITY.get(classification.ticket_category, "LOW")
    if urgency_hits > 0:
        priority = _bump(priority, 1)
    if sentiment_score < -0.3:
        priority = _bump(priority, 1)
    if customer_tier and customer_tier.lower() in {"vip", "enterprise"}:
        priority = _bump(priority, 1)

    urgency_score = min(1.0, (urgency_hits + abs(sentiment_score)) / 3)
    sla_deadline = add_hours_iso(_SLA_HOURS[priority])

    return PriorityResult(
        priority_level=priority,
        urgency_score=round(urgency_score, 2),
        sla_deadline=sla_deadline,
        sentiment_score=round(sentiment_score, 2),
    )
