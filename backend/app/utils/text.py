from __future__ import annotations

import hashlib
import re
from typing import Iterable

_STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "then",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "as",
    "by",
    "at",
    "from",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "this",
    "that",
    "it",
    "its",
    "i",
    "we",
    "you",
    "they",
    "he",
    "she",
    "my",
    "our",
    "your",
}

_SIGNATURE_SPLITS = [
    r"\n--\n",
    r"\nthanks,",
    r"\nbest,",
    r"\nregards,",
]

_REPLY_SPLITS = [
    r"\nOn .* wrote:",
    r"\n-----Original Message-----",
    r"\nFrom: ",
]


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def strip_reply_chain(text: str) -> str:
    for pattern in _REPLY_SPLITS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return text[: match.start()]
    return text


def strip_signature(text: str) -> str:
    for pattern in _SIGNATURE_SPLITS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return text[: match.start()]
    return text


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def stem_token(token: str) -> str:
    if len(token) > 4 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 3 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    tokens = text.split()
    tokens = [stem_token(t) for t in tokens if t not in _STOPWORDS]
    return [t for t in tokens if t]


def detect_language(text: str) -> str:
    if not text:
        return "unknown"
    ascii_ratio = sum(1 for c in text if ord(c) < 128) / max(1, len(text))
    return "en" if ascii_ratio > 0.9 else "unknown"


def extract_entities(text: str) -> dict[str, list[str]]:
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    order_ids = re.findall(r"order\s*[-#]?\s*\d+", text, flags=re.IGNORECASE)
    dates = re.findall(
        r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        text,
    )
    numbers = re.findall(r"\b\d+\b", text)
    return {
        "emails": list(dict.fromkeys(emails)),
        "order_ids": list(dict.fromkeys(order_ids)),
        "dates": list(dict.fromkeys(dates)),
        "numbers": list(dict.fromkeys(numbers)),
    }


def embed_tokens(tokens: Iterable[str], size: int = 32) -> list[int]:
    vector = [0] * size
    for token in tokens:
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        idx = int(digest, 16) % size
        vector[idx] += 1
    return vector
