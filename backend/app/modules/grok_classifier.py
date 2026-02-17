from __future__ import annotations

import json
import os
import re
from urllib import error, request

from app.schemas import ClassificationResult, PreprocessResult

_ALLOWED_CATEGORIES = {
    "billing",
    "technical",
    "account",
    "complaint",
    "feature_request",
    "general",
}

_SYSTEM_PROMPT = (
    "You classify support tickets for an email support system.\n"
    "Return exactly one category from: billing, technical, account, complaint, feature_request, general.\n"
    "Hard routing rules:\n"
    "- technical: outages, bugs, errors, blank screen, app/page/dashboard not loading, performance failures.\n"
    "- billing: charges, invoices, refunds, payment failures, duplicate charges.\n"
    "- account: login credentials, account lock, 2FA, verification, access permissions.\n"
    "- complaint: dissatisfaction/escalation about service quality.\n"
    "- feature_request: asks for new features/enhancements.\n"
    "- general: everything else.\n"
    "If text includes login + system failure, classify as technical unless it is clearly credentials/account-only.\n"
    "Respond as strict JSON object only with keys: ticket_category, subcategory, intent_label, confidence_score, needs_manual_review."
)


def _api_key() -> str:
    return (os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY") or "").strip()


def is_enabled() -> bool:
    return bool(_api_key())


def _extract_json_payload(content: str) -> dict | None:
    if not content:
        return None
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        loaded = json.loads(text)
        return loaded if isinstance(loaded, dict) else None
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None
    try:
        loaded = json.loads(match.group(0))
        return loaded if isinstance(loaded, dict) else None
    except Exception:
        return None


def _extract_content(response_payload: dict) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict):
                part_text = part.get("text")
                if isinstance(part_text, str):
                    parts.append(part_text)
        return "\n".join(parts)
    return ""


def _coerce_result(payload: dict) -> ClassificationResult | None:
    category = str(payload.get("ticket_category") or payload.get("category") or "").strip().lower()
    if category not in _ALLOWED_CATEGORIES:
        return None

    confidence_raw = payload.get("confidence_score", payload.get("confidence", 0.5))
    try:
        confidence = float(confidence_raw)
    except Exception:
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))

    subcategory = payload.get("subcategory")
    if subcategory is not None:
        subcategory = str(subcategory)[:80]

    intent_label = payload.get("intent_label")
    if intent_label is None:
        intent_label = f"{category}_issue"
    intent_label = str(intent_label)[:80]

    if "needs_manual_review" in payload:
        needs_manual_review = bool(payload.get("needs_manual_review"))
    else:
        min_conf = float(os.getenv("GROK_MIN_CONFIDENCE", "0.55"))
        needs_manual_review = confidence < min_conf

    return ClassificationResult(
        ticket_category=category,
        subcategory=subcategory,
        intent_label=intent_label,
        confidence_score=round(confidence, 2),
        needs_manual_review=needs_manual_review,
    )


def classify(preprocess: PreprocessResult) -> ClassificationResult | None:
    api_key = _api_key()
    if not api_key:
        return None

    model = os.getenv("GROK_MODEL", "grok-4")
    base_url = (
        os.getenv("GROK_API_BASE_URL")
        or os.getenv("XAI_API_BASE_URL")
        or "https://api.x.ai/v1"
    ).rstrip("/")
    timeout = float(os.getenv("GROK_TIMEOUT_SECONDS", "20"))
    max_tokens = int(os.getenv("GROK_MAX_TOKENS", "220"))

    user_prompt = (
        "Classify this support email.\n"
        f"language={preprocess.language}\n"
        f"text={preprocess.cleaned_text}\n"
        f"entities={json.dumps(preprocess.entities, ensure_ascii=True)}"
    )

    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }

    req = request.Request(
        url=f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            response_body = resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        print(f"[grok] classification http error: status={exc.code} body={body[:200]}")
        return None
    except Exception as exc:
        print(f"[grok] classification request failed: {exc}")
        return None

    try:
        response_payload = json.loads(response_body)
    except Exception:
        print("[grok] classification failed: invalid JSON response")
        return None

    content = _extract_content(response_payload)
    data = _extract_json_payload(content)
    if data is None:
        print(f"[grok] classification failed: invalid model content={content[:200]}")
        return None

    result = _coerce_result(data)
    if result is None:
        print(f"[grok] classification failed: invalid category payload={data}")
        return None
    return result
