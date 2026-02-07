from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send_email(to_address: str, subject: str, body: str) -> dict:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM", "support@local")

    if not host:
        print(f"[email] skipped (SMTP not configured). to={to_address} subject={subject}")
        return {"status": "skipped", "reason": "SMTP not configured"}

    message = EmailMessage()
    message["From"] = sender
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(message)
        return {"status": "sent"}
    except Exception as exc:
        print(f"[email] failed to send: {exc}")
        return {"status": "failed", "reason": str(exc)}
