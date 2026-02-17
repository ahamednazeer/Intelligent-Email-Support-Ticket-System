from __future__ import annotations

import os

from app.schemas import ClassificationResult, PreprocessResult
from app.ml.predict import predict_category
from app.modules import grok_classifier

_CATEGORY_KEYWORDS = {
    "billing": [
        "invoice",
        "invoiced",
        "refund",
        "refunded",
        "charge",
        "charged",
        "chargeback",
        "billing",
        "bill",
        "payment",
        "paid",
        "pay",
        "price",
        "pricing",
        "credit",
        "debit",
        "cost",
        "subscription",
        "renewal",
        "renew",
        "cancel",
        "cancellation",
        "overcharged",
        "overcharge",
        "double",
        "duplicate",
        "double charge",
        "duplicate charge",
        "charged twice",
        "two charges",
        "receipt",
        "tax",
        "vat",
        "fee",
        "late fee",
        "balance",
        "statement",
        "transaction",
        "card",
        "credit card",
        "debit card",
        "promo",
        "promotion",
        "discount",
        "coupon",
        "order total",
        "amount",
        "incorrect amount",
        "wrong amount",
        "billing address",
        "payment failed",
        "card declined",
        "declined",
    ],
    "technical": [
        "error",
        "bug",
        "issue",
        "problem",
        "down",
        "outage",
        "incident",
        "crash",
        "fail",
        "failed",
        "failure",
        "timeout",
        "timed out",
        "latency",
        "slow",
        "sluggish",
        "performance",
        "not working",
        "unavailable",
        "cannot connect",
        "can't connect",
        "connection",
        "server error",
        "500",
        "502",
        "503",
        "504",
        "exception",
        "stack trace",
        "loading",
        "stuck",
        "hang",
        "hangs",
        "freeze",
        "frozen",
        "not responding",
        "blank",
        "screen",
        "white screen",
        "blank screen",
        "loading screen",
        "dashboard",
        "page",
        "api",
        "integration",
        "webhook",
        "sync",
        "syncing",
    ],
    "account": [
        "login",
        "log in",
        "sign in",
        "signin",
        "sign-in",
        "password",
        "reset",
        "forgot password",
        "account",
        "signup",
        "sign up",
        "register",
        "registration",
        "profile",
        "verify",
        "verification",
        "access",
        "locked",
        "unlock",
        "suspended",
        "deactivated",
        "disabled",
        "mfa",
        "2fa",
        "two-factor",
        "two factor",
        "otp",
        "code",
        "email change",
        "username",
        "permissions",
        "role",
        "invite",
        "invitation",
    ],
    "complaint": [
        "complaint",
        "formal complaint",
        "file a complaint",
        "lodge a complaint",
        "angry",
        "upset",
        "frustrated",
        "disappointed",
        "not satisfied",
        "not satisfactory",
        "unsatisfactory",
        "unacceptable",
        "bad",
        "terrible",
        "awful",
        "poor",
        "rude",
        "unhappy",
        "inconvenience",
        "disruption",
        "delay",
        "delayed response",
        "poor experience",
        "bad experience",
        "service quality",
        "customer service",
        "not function as expected",
        "did not function as expected",
        "escalate",
        "escalation",
        "complain",
        "dissatisfied",
        "investigate this matter",
        "resolve this issue",
    ],
    "feature_request": [
        "feature request",
        "feature",
        "enhancement",
        "improve",
        "improvement",
        "add",
        "adding",
        "roadmap",
        "idea",
        "suggest",
        "suggestion",
        "wish",
        "would like",
        "could you add",
        "please add",
        "new feature",
    ],
    "general": [
        "question",
        "help",
        "info",
        "information",
        "how",
        "what",
        "where",
        "when",
        "who",
        "general",
        "inquiry",
        "need help",
        "assist",
    ],
}

_CATEGORY_STRONG_PHRASES = {
    "billing": [
        "charged twice",
        "double charged",
        "duplicate charge",
        "wrong amount",
        "incorrect amount",
        "overcharged",
        "payment failed",
        "card declined",
        "invoice",
        "refund",
        "billing issue",
    ],
    "technical": [
        "blank screen",
        "white screen",
        "blank page",
        "not loading",
        "loading screen",
        "system is not loading",
        "dashboard is not loading",
        "server error",
        "timeout",
        "timed out",
        "not responding",
        "service down",
        "system down",
        "outage",
    ],
    "account": [
        "cannot login",
        "can t login",
        "login failed",
        "forgot password",
        "password reset",
        "account locked",
        "verification code",
        "two factor",
        "2fa",
        "mfa",
    ],
    "complaint": [
        "lodge a complaint",
        "formal complaint",
        "file a complaint",
        "poor service",
        "bad service",
        "very disappointed",
        "not satisfied",
        "not satisfactory",
        "unsatisfactory",
        "unacceptable",
        "poor experience",
        "bad experience",
        "service quality",
        "customer service issue",
        "did not function as expected",
        "caused inconvenience",
        "caused disruption",
        "investigate this matter",
        "escalate",
    ],
    "feature_request": [
        "feature request",
        "please add",
        "would like to",
        "new feature",
        "add feature",
    ],
}

_HARD_RULES = {
    "technical": [
        "blank screen",
        "white screen",
        "not loading",
        "system is not loading",
        "dashboard is not loading",
        "server error",
        "500",
        "502",
        "503",
        "504",
        "timeout",
        "timed out",
        "not responding",
        "outage",
        "service down",
        "system down",
    ],
    "billing": [
        "charged twice",
        "double charged",
        "duplicate charge",
        "wrong amount",
        "incorrect amount",
        "overcharged",
        "payment failed",
        "card declined",
    ],
    "account": [
        "cannot login",
        "can t login",
        "login failed",
        "forgot password",
        "password reset",
        "account locked",
        "verification code",
    ],
    "complaint": [
        "lodge a complaint",
        "formal complaint",
        "file a complaint",
        "not satisfactory",
        "not satisfied",
        "unsatisfactory",
        "caused inconvenience",
        "caused disruption",
        "poor service",
        "bad service",
        "very disappointed",
        "unacceptable service",
        "customer service issue",
    ],
}

_SUBCATEGORY_HINTS = {
    "billing": "refunds",
    "technical": "availability",
    "account": "access",
    "complaint": "service",
    "feature_request": "product",
    "general": "general",
}


def _classify_local(preprocess: PreprocessResult) -> ClassificationResult:
    text = preprocess.cleaned_text
    tokens = preprocess.tokens

    scores: dict[str, int] = {category: 0 for category in _CATEGORY_KEYWORDS}

    for category, keywords in _CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if " " in kw:
                if kw in text:
                    scores[category] += 2
            else:
                scores[category] += tokens.count(kw)

    for category, phrases in _CATEGORY_STRONG_PHRASES.items():
        for phrase in phrases:
            if phrase in text:
                scores[category] += 3

    hard_hits = {category for category, phrases in _HARD_RULES.items() if any(phrase in text for phrase in phrases)}

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]
    total_hits = sum(scores.values()) or 1
    confidence = min(1.0, best_score / total_hits)
    conflict_margin = int(os.getenv("KEYWORD_CONFLICT_MARGIN", "1"))
    override_min = int(os.getenv("KEYWORD_OVERRIDE_MIN", "1"))
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0

    if hard_hits:
        if len(hard_hits) == 1:
            category = next(iter(hard_hits))
            return ClassificationResult(
                ticket_category=category,
                subcategory=_SUBCATEGORY_HINTS.get(category),
                intent_label=f"{category}_issue",
                confidence_score=0.95,
                needs_manual_review=False,
            )
        best_category = max(hard_hits, key=lambda c: scores.get(c, 0))
        return ClassificationResult(
            ticket_category=best_category,
            subcategory=_SUBCATEGORY_HINTS.get(best_category),
            intent_label=f"{best_category}_issue",
            confidence_score=0.7,
            needs_manual_review=True,
        )

    if best_score >= override_min:
        needs_manual_review = (best_score - second_score) <= conflict_margin or confidence < 0.45
        return ClassificationResult(
            ticket_category=best_category,
            subcategory=_SUBCATEGORY_HINTS.get(best_category),
            intent_label=f"{best_category}_issue",
            confidence_score=round(confidence, 2),
            needs_manual_review=needs_manual_review,
        )

    ml_result = predict_category(text)
    if ml_result:
        ml_category, ml_confidence = ml_result
        if ml_category not in _CATEGORY_KEYWORDS:
            ml_category = "general"
            ml_confidence = max(0.2, min(1.0, ml_confidence))

        intent_label = f"{ml_category}_issue"
        subcategory = _SUBCATEGORY_HINTS.get(ml_category)
        min_ml_conf = float(os.getenv("ML_MIN_CONFIDENCE", "0.55"))
        needs_manual_review = ml_confidence < min_ml_conf

        return ClassificationResult(
            ticket_category=ml_category,
            subcategory=subcategory,
            intent_label=intent_label,
            confidence_score=round(ml_confidence, 2),
            needs_manual_review=needs_manual_review,
        )

    if best_score == 0:
        best_category = "general"
        confidence = 0.2

    return ClassificationResult(
        ticket_category=best_category,
        subcategory=_SUBCATEGORY_HINTS.get(best_category),
        intent_label=f"{best_category}_issue",
        confidence_score=round(confidence, 2),
        needs_manual_review=True if best_score == 0 else confidence < 0.45,
    )


def _classifier_provider() -> str:
    provider = os.getenv("CLASSIFIER_PROVIDER", "grok_first").strip().lower()
    if provider not in {"local", "grok", "grok_first"}:
        return "grok_first"
    return provider


def classify(preprocess: PreprocessResult) -> ClassificationResult:
    provider = _classifier_provider()
    local_result = _classify_local(preprocess)

    if provider == "local":
        return local_result

    # Grok-first: if configured and available, use it; otherwise fallback to local rules/ML.
    if not grok_classifier.is_enabled():
        return local_result
    grok_result = grok_classifier.classify(preprocess)
    if grok_result is not None:
        return grok_result
    return local_result
