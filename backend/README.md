# Backend – Intelligent Email Support Ticket System

This backend implements the module-wise flow as a single FastAPI service with clear module boundaries and a SQLite database.

## Quickstart
1) Create a virtualenv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Run the API:

```bash
python run.py
```

3) Open API docs:

- http://localhost:8000/docs

## Default Credentials (Dev)
- Admin: `admin` / `admin123`
- Technical: `agent1` / `agent123`

## Modules Implemented
- Input Module: `app/modules/input_module.py`
- Preprocessing Module: `app/modules/preprocessing.py`
- Intent & Classification: `app/modules/classification.py`
- Priority & Urgency: `app/modules/priority.py`
- Routing & Assignment: `app/modules/routing.py`
- Ticket Management: `app/modules/ticket_management.py`
- Closure & Feedback: `app/modules/closure_feedback.py`
- Continuous Learning: `app/modules/learning.py`
- Analytics & Monitoring: `app/modules/analytics.py`

## Data Storage
- SQLite DB file: `backend/data/tickets.db`

## Notes
- Classification uses a trainable ML model when available and falls back to heuristics if no model is trained.
- ML classification is trainable: label tickets via `POST /tickets/{id}/label` and call `POST /retrain`.
- Routing uses agent skills and workload to assign tickets when available.
- Auto-assignment can be gated by admin review with `ASSIGNMENT_REQUIRES_REVIEW=true` (routes set `REVIEW_PENDING` and suggested agent until approved).
- Auth uses JWT with role-based access (`ADMIN`, `SUPERVISOR`, plus category roles: `BILLING`, `TECHNICAL`, `ACCOUNT`, `COMPLAINT`, `FEATURE_REQUEST`, `GENERAL`).
- Outbound email is a hook (SMTP). Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` to send real emails.
- Inbound email can be ingested via IMAP polling (disabled by default). Set `IMAP_POLLING_ENABLED=true` and configure `IMAP_HOST`, `IMAP_PORT`, `IMAP_USER`, `IMAP_PASSWORD`, `IMAP_FOLDER`, `IMAP_POLL_INTERVAL`. Use `IMAP_SEARCH_CRITERIA=UNSEEN` and `IMAP_MARK_SEEN=true` to avoid duplicates.
- The backend auto-loads `backend/.env` on startup (via `python-dotenv`).
- You can filter inbound email via IMAP rules: `IMAP_ALLOW_FROM`, `IMAP_ALLOW_DOMAINS`, `IMAP_BLOCK_FROM`, `IMAP_BLOCK_DOMAINS`, `IMAP_BLOCK_SUBJECT`, `IMAP_BLOCK_NOREPLY`.
- IMAP ingestion now de-duplicates messages using `Message-ID`, IMAP UID, and a content fingerprint to prevent repeated tickets.
- Cleanup duplicates (admin): `POST /maintenance/dedupe?hours=24` (add `&dry_run=true` to preview).
- Audit logs are available at `GET /audit/logs` for admin.
