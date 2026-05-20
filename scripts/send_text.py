#!/usr/bin/env python3
"""
Sends the daily Morning Brief SMS via Twilio.
Reads today's date from brief_data.json to build the correct URL.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "brief_data.json"

TO_NUMBER = "+16038040400"


def get_pages_url(date_str: str) -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        return f"(URL unavailable — GITHUB_REPOSITORY not set)"
    parts = repo.split("/")
    if len(parts) != 2:
        return f"(URL unavailable — unexpected GITHUB_REPOSITORY format)"
    owner, name = parts
    return f"https://{owner}.github.io/{name}/{date_str}.html"


def main():
    # Validate env vars early so we fail loudly
    account_sid  = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token   = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number  = os.environ.get("TWILIO_FROM_NUMBER")

    missing = [k for k, v in {
        "TWILIO_ACCOUNT_SID":  account_sid,
        "TWILIO_AUTH_TOKEN":   auth_token,
        "TWILIO_FROM_NUMBER":  from_number,
    }.items() if not v]

    if missing:
        print(f"ERROR: Missing Twilio env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    # Load date from brief data if available, fall back to today
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

    body = (
        f"☀️ Maxi's Morning Brief — {day_display}\n\n"
        f"Today's top stories in politics, tech, soccer & basketball are ready.\n\n"
        f"{url}\n\n"
        f"Reply STOP to unsubscribe."
    )

    # Import twilio here so an import error surfaces cleanly
    try:
        from twilio.rest import Client
    except ImportError:
        print("ERROR: twilio package not installed. Run: pip install twilio", file=sys.stderr)
        sys.exit(1)

    client = Client(account_sid, auth_token)

    try:
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=TO_NUMBER,
        )
        print(f"SMS sent. SID: {message.sid}  Status: {message.status}")
    except Exception as e:
        print(f"ERROR: Twilio send failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
