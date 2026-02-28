from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import get_conn, init_db
from app.modules import preprocessing, classification as classification_module
from app.schemas import Attachment, StructuredTicket
from app.repositories import tickets as ticket_repo


DEPARTMENT_BY_CATEGORY = {
    "technical": "Engineering Support",
    "billing": "Billing",
    "account": "Account",
    "complaint": "Customer Care",
    "feature_request": "Product",
    "government": "Government",
    "general": "General",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reclassify tickets using current keyword/ML rules.")
    parser.add_argument("--hours", type=int, default=168, help="Lookback window in hours (default: 168)")
    parser.add_argument("--include-resolved", action="store_true", help="Include resolved tickets")
    parser.add_argument("--force-labeled", action="store_true", help="Reclassify even if label_category is set")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing changes")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    env_path = ROOT / ".env"
    load_dotenv(env_path, override=False)
    init_db()

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=args.hours)).isoformat()

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, sender_email, subject, body, attachments_json, created_at, status,
                   category, label_category, assigned_agent_id, department
            FROM tickets
            WHERE created_at >= ?
            ORDER BY created_at ASC
            """,
            (cutoff,),
        ).fetchall()

    scanned = 0
    updated = 0
    skipped = 0

    for row in rows:
        scanned += 1
        if row["status"] == "RESOLVED" and not args.include_resolved:
            skipped += 1
            continue
        if row["label_category"] and not args.force_labeled:
            skipped += 1
            continue

        attachments = []
        if row["attachments_json"]:
            try:
                for item in json.loads(row["attachments_json"]):
                    attachments.append(Attachment(**item))
            except Exception:
                attachments = []

        ticket = StructuredTicket(
            ticket_id=row["id"],
            sender=row["sender_email"],
            subject=row["subject"],
            body=row["body"],
            attachments=attachments,
            created_at=row["created_at"],
            status=row["status"],
        )

        preprocess = preprocessing.preprocess(ticket)
        classification = classification_module.classify(preprocess)
        department = DEPARTMENT_BY_CATEGORY.get(classification.ticket_category, row["department"])

        if args.dry_run:
            continue

        ticket_repo.update_ticket_analysis(
            ticket_id=row["id"],
            preprocess=preprocess,
            classification=classification,
            department=None if row["assigned_agent_id"] else department,
        )
        updated += 1

    print(
        "reclassify:",
        f"window_hours={args.hours}",
        f"scanned={scanned}",
        f"updated={updated}",
        f"skipped={skipped}",
        f"dry_run={args.dry_run}",
    )


if __name__ == "__main__":
    main()
