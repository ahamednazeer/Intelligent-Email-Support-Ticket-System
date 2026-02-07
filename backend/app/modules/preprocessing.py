from __future__ import annotations

from app.schemas import PreprocessResult, StructuredTicket
from app.utils import text as text_utils


def preprocess(ticket: StructuredTicket) -> PreprocessResult:
    raw = ticket.body or ""
    cleaned = text_utils.strip_html(raw)
    cleaned = text_utils.strip_reply_chain(cleaned)
    cleaned = text_utils.strip_signature(cleaned)
    cleaned = text_utils.normalize(cleaned)
    tokens = text_utils.tokenize(cleaned)
    entities = text_utils.extract_entities(raw)
    embedding = text_utils.embed_tokens(tokens)
    language = text_utils.detect_language(raw)
    return PreprocessResult(
        cleaned_text=cleaned,
        entities=entities,
        embedding=embedding,
        language=language,
        tokens=tokens,
    )
