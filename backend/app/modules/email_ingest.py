from __future__ import annotations

import email
import hashlib
import imaplib
import os
import re
import threading
import time
from email.header import decode_header
from email.utils import parseaddr
from html import unescape
from typing import Optional

from app.pipeline import process_ticket
from app.repositories import ingested_messages as ingest_repo
from app.schemas import Attachment, IngestRequest


def _decode_header_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    decoded_parts = []
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
        else:
            decoded_parts.append(part)
    return "".join(decoded_parts).strip()


def _decode_part_payload(part: email.message.Message) -> str:
    payload = part.get_payload(decode=True) or b""
    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _strip_html(text: str) -> str:
    cleaned = re.sub(r"<(script|style)[^>]*>.*?</\\1>", " ", text, flags=re.I | re.S)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return " ".join(unescape(cleaned).split())


def _extract_body(message: email.message.Message) -> str:
    if message.is_multipart():
        plain_text = None
        html_text = None
        for part in message.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get_content_disposition() == "attachment":
                continue
            content_type = part.get_content_type()
            if content_type == "text/plain" and plain_text is None:
                plain_text = _decode_part_payload(part)
            elif content_type == "text/html" and html_text is None:
                html_text = _strip_html(_decode_part_payload(part))
        return plain_text or html_text or ""

    content_type = message.get_content_type()
    body = _decode_part_payload(message)
    if content_type == "text/html":
        return _strip_html(body)
    return body


def _extract_attachments(message: email.message.Message) -> list[Attachment]:
    attachments: list[Attachment] = []
    if not message.is_multipart():
        return attachments
    for part in message.walk():
        if part.get_content_disposition() != "attachment":
            continue
        filename = _decode_header_value(part.get_filename()) or "attachment"
        payload = part.get_payload(decode=True) or b""
        attachments.append(
            Attachment(
                filename=filename,
                content_type=part.get_content_type(),
                size=len(payload),
            )
        )
    return attachments


def _env_list(name: str) -> list[str]:
    raw = os.getenv(name, "")
    if not raw:
        return []
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def _should_skip(sender: str, subject: Optional[str]) -> Optional[str]:
    sender = sender.lower()
    subject_text = (subject or "").lower()
    domain = sender.split("@")[-1] if "@" in sender else ""

    allow_from = _env_list("IMAP_ALLOW_FROM")
    allow_domains = _env_list("IMAP_ALLOW_DOMAINS")
    block_from = _env_list("IMAP_BLOCK_FROM")
    block_domains = _env_list("IMAP_BLOCK_DOMAINS")
    block_subject = _env_list("IMAP_BLOCK_SUBJECT")
    block_noreply = os.getenv("IMAP_BLOCK_NOREPLY", "false").lower() in {"1", "true", "yes"}

    if allow_from and sender not in allow_from:
        return "sender not in allow list"
    if allow_domains and domain not in allow_domains:
        return "domain not in allow list"
    if sender in block_from:
        return "sender blocked"
    if domain in block_domains:
        return "domain blocked"
    if block_noreply and sender.startswith(("no-reply@", "noreply@")):
        return "noreply blocked"
    if block_subject and any(token in subject_text for token in block_subject):
        return "subject blocked"

    return None


def _fingerprint(sender: str, subject: Optional[str], date_header: Optional[str], body: str) -> str:
    payload = "\n".join([sender, subject or "", date_header or "", body])
    return hashlib.sha256(payload.encode("utf-8", errors="ignore")).hexdigest()


def _ingest_message(message: email.message.Message, source: str, uid: Optional[str]) -> str:
    sender = parseaddr(message.get("From", ""))[1] or "unknown@local"
    subject = _decode_header_value(message.get("Subject"))
    message_id = (message.get("Message-ID") or "").strip().lower() or None
    date_header = message.get("Date") or ""

    skip_reason = _should_skip(sender, subject)
    if skip_reason:
        print(f"[imap] skipped message: {skip_reason} sender={sender} subject={subject}")
        return "skipped"

    body = _extract_body(message)
    attachments = _extract_attachments(message)

    if not body:
        body = ""

    fingerprint = _fingerprint(sender, subject, date_header, body)
    if ingest_repo.is_duplicate(source, message_id, uid, fingerprint):
        return "duplicate"

    ticket = process_ticket(
        IngestRequest(
            sender_email=sender,
            subject=subject,
            body=body,
            attachments=attachments,
        )
    )
    ingest_repo.record_message(source, message_id, uid, fingerprint, ticket.ticket_id)
    return "ingested"


def poll_once() -> int:
    host = os.getenv("IMAP_HOST")
    user = os.getenv("IMAP_USER")
    password = os.getenv("IMAP_PASSWORD")
    if not host or not user or not password:
        print("[imap] skipped (IMAP not configured).")
        return 0

    port = int(os.getenv("IMAP_PORT", "993"))
    folder = os.getenv("IMAP_FOLDER", "INBOX")
    criteria = os.getenv("IMAP_SEARCH_CRITERIA", "UNSEEN")
    mark_seen = os.getenv("IMAP_MARK_SEEN", "true").lower() in {"1", "true", "yes"}
    use_ssl = os.getenv("IMAP_SSL", "true").lower() in {"1", "true", "yes"}

    client = None
    try:
        client = imaplib.IMAP4_SSL(host, port) if use_ssl else imaplib.IMAP4(host, port)
        client.login(user, password)
        client.select(folder)
        status, data = client.uid("search", None, criteria)
        if status != "OK" or not data or not data[0]:
            return 0

        message_uids = data[0].split()
        ingested = 0
        for uid in message_uids:
            status, msg_data = client.uid("fetch", uid, "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            raw_message = msg_data[0][1]
            message = email.message_from_bytes(raw_message)
            uid_str = uid.decode("utf-8", errors="ignore")
            result = _ingest_message(message, source=f"imap:{user}@{host}", uid=uid_str)
            if result == "ingested":
                ingested += 1
            if mark_seen and result in {"ingested", "duplicate", "skipped"}:
                client.uid("store", uid, "+FLAGS", "\\Seen")
        return ingested
    except Exception as exc:
        print(f"[imap] poll failed: {exc}")
        return 0
    finally:
        try:
            if client is not None:
                client.close()
                client.logout()
        except Exception:
            pass


def _poll_loop(interval_seconds: int) -> None:
    while True:
        try:
            count = poll_once()
            if count:
                print(f"[imap] ingested {count} message(s).")
        except Exception as exc:
            print(f"[imap] loop error: {exc}")
        time.sleep(interval_seconds)


def _acquire_lock(lockfile: str) -> bool:
    try:
        fd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.write(fd, str(os.getpid()).encode("utf-8"))
        os.close(fd)
        return True
    except FileExistsError:
        existing_pid = None
        try:
            with open(lockfile, "r", encoding="utf-8") as handle:
                existing_pid = int(handle.read().strip() or "0")
        except Exception:
            existing_pid = None

        if existing_pid:
            try:
                os.kill(existing_pid, 0)
                print(f"[imap] lock exists (active pid {existing_pid}), skipping poller start: {lockfile}")
                return False
            except ProcessLookupError:
                pass
            except PermissionError:
                print(f"[imap] lock exists (pid {existing_pid} not owned), skipping poller start: {lockfile}")
                return False
            except Exception:
                print(f"[imap] lock exists (pid {existing_pid}), skipping poller start: {lockfile}")
                return False

        try:
            os.remove(lockfile)
        except Exception as exc:
            print(f"[imap] stale lock cannot be removed: {exc}")
            return False

        try:
            fd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.write(fd, str(os.getpid()).encode("utf-8"))
            os.close(fd)
            return True
        except Exception as exc:
            print(f"[imap] lock acquisition failed after cleanup: {exc}")
            return False


def start_imap_poller() -> None:
    enabled = os.getenv("IMAP_POLLING_ENABLED", "false").lower() in {"1", "true", "yes"}
    if not enabled:
        return

    lockfile = os.getenv("IMAP_LOCKFILE")
    if lockfile and not _acquire_lock(lockfile):
        return

    interval = int(os.getenv("IMAP_POLL_INTERVAL", "60"))
    thread = threading.Thread(target=_poll_loop, args=(interval,), daemon=True)
    thread.start()
    print(f"[imap] polling started (every {interval}s).")
