#!/usr/bin/env python3
"""
Sends the daily Morning Brief email via Gmail SMTP.
Reads today's date from brief_data.json to build the correct URL.
"""

import json
import os
import smtplib
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "brief_data.json"

TO_ADDRESS = "maxi2010baumgart@gmail.com"


def get_pages_url(date_str: str) -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        return "(URL unavailable — GITHUB_REPOSITORY not set)"
    parts = repo.split("/")
    if len(parts) != 2:
        return "(URL unavailable — unexpected GITHUB_REPOSITORY format)"
    owner, name = parts
    return f"https://{owner}.github.io/{name}/{date_str}.html"


def main():
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")

    missing = [k for k, v in {
        "GMAIL_USER": gmail_user,
        "GMAIL_APP_PASSWORD": gmail_password,
    }.items() if not v]

    if missing:
        print(f"ERROR: Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    date_str = datetime.now().strftime("%Y-%m-%d")
    day_display = datetime.now().strftime("%A, %B %-d")

    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            date_str = data.get("date", date_str)
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            day_display = dt.strftime("%A, %B %-d")
        except (json.JSONDecodeError, ValueError):
            pass

    url = get_pages_url(date_str)

    msg = EmailMessage()
    msg["Subject"] = f"☀️ Maxi's Morning Brief — {date_str}"
    msg["From"] = gmail_user
    msg["To"] = TO_ADDRESS
    msg.set_content(url)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(gmail_user, gmail_password)
            smtp.send_message(msg)
        print(f"Email sent to {TO_ADDRESS} for {date_str}")
    except smtplib.SMTPException as e:
        print(f"ERROR: Gmail send failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
