from __future__ import annotations

import argparse
from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import init_db
from app.repositories import tickets as ticket_repo


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove duplicate tickets within a time window.")
    parser.add_argument("--hours", type=int, default=24, help="Lookback window in hours (default: 24)")
    parser.add_argument("--dry-run", action="store_true", help="Preview duplicates without deleting")
    args = parser.parse_args()

    env_path = ROOT / ".env"
    load_dotenv(env_path, override=False)

    init_db()
    result = ticket_repo.dedupe_tickets(window_hours=args.hours, dry_run=args.dry_run)
    print(
        "dedupe:",
        f"window_hours={result['window_hours']}",
        f"scanned={result['scanned']}",
        f"duplicates_found={result['duplicates_found']}",
        f"deleted={result['deleted']}",
        f"dry_run={result['dry_run']}",
    )


if __name__ == "__main__":
    main()
