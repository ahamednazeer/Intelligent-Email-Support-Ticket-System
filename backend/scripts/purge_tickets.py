from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import get_conn, init_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Purge tickets by sender or subject filters.")
    parser.add_argument(
        "--domain",
        action="append",
        default=[],
        help="Sender domain to match (repeatable). Matches subdomains too.",
    )
    parser.add_argument(
        "--from",
        dest="from_addresses",
        action="append",
        default=[],
        help="Exact sender email address to match (repeatable).",
    )
    parser.add_argument(
        "--subject",
        action="append",
        default=[],
        help="Subject token to match (repeatable).",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=0,
        help="Lookback window in hours (0 = all time).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    return parser.parse_args()


def domain_matches(domain: str, pattern: str) -> bool:
    domain = domain.lower()
    pattern = pattern.lower()
    return domain == pattern or domain.endswith(f".{pattern}")


def main() -> None:
    args = parse_args()
    load_dotenv(ROOT / ".env", override=False)
    init_db()

    cutoff = None
    if args.hours and args.hours > 0:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=args.hours)).isoformat()

    with get_conn() as conn:
        if cutoff:
            rows = conn.execute(
                """
                SELECT id, sender_email, subject, created_at
                FROM tickets
                WHERE created_at >= ?
                ORDER BY created_at ASC
                """,
                (cutoff,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, sender_email, subject, created_at
                FROM tickets
                ORDER BY created_at ASC
                """
            ).fetchall()

    domains = [d.strip().lower() for d in args.domain if d.strip()]
    from_addresses = [f.strip().lower() for f in args.from_addresses if f.strip()]
    subject_tokens = [s.strip().lower() for s in args.subject if s.strip()]

    match_ids: list[str] = []
    for row in rows:
        sender = (row["sender_email"] or "").lower()
        subject = (row["subject"] or "").lower()
        domain = sender.split("@")[-1] if "@" in sender else ""

        matched = False
        if from_addresses and sender in from_addresses:
            matched = True
        if not matched and domains and any(domain_matches(domain, d) for d in domains):
            matched = True
        if not matched and subject_tokens and any(token in subject for token in subject_tokens):
            matched = True

        if matched:
            match_ids.append(row["id"])

    if args.dry_run or not match_ids:
        print(
            "purge:",
            f"hours={args.hours}",
            f"scanned={len(rows)}",
            f"matched={len(match_ids)}",
            f"deleted=0",
            f"dry_run={args.dry_run}",
        )
        return

    placeholders = ",".join("?" for _ in match_ids)
    with get_conn() as conn:
        conn.execute(
            f"DELETE FROM ticket_responses WHERE ticket_id IN ({placeholders})",
            match_ids,
        )
        conn.execute(
            f"DELETE FROM feedback WHERE ticket_id IN ({placeholders})",
            match_ids,
        )
        conn.execute(
            f"DELETE FROM audit_logs WHERE target_type = 'TICKET' AND target_id IN ({placeholders})",
            match_ids,
        )
        conn.execute(
            f"DELETE FROM ingested_messages WHERE ticket_id IN ({placeholders})",
            match_ids,
        )
        conn.execute(
            f"DELETE FROM tickets WHERE id IN ({placeholders})",
            match_ids,
        )
        conn.commit()

    print(
        "purge:",
        f"hours={args.hours}",
        f"scanned={len(rows)}",
        f"matched={len(match_ids)}",
        f"deleted={len(match_ids)}",
        "dry_run=False",
    )


if __name__ == "__main__":
    main()
