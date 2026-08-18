#!/usr/bin/env python3
"""
Daily Briefing Generator — Construction Company
================================================
Pulls together email, JobTread tasks, and calendar into a morning briefing.

Usage:
  python daily_briefing.py              # Generate and print briefing
  python daily_briefing.py --telegram   # Format for Telegram delivery
"""

import sys
import os
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Import sibling scripts
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# ── Config ──────────────────────────────────────────────────
JOBTREAD_GRANT_KEY = os.environ.get("JOBTREAD_GRANT_KEY", "")
JOBTREAD_ORG_ID = os.environ.get("JOBTREAD_ORG_ID", "")
TOKEN_FILE = Path.home() / ".hermes" / "cache" / "google_token.json"


def get_jobtread_projects():
    """Get today's and upcoming tasks from JobTread."""
    if not JOBTREAD_GRANT_KEY or not JOBTREAD_ORG_ID:
        return "  ⚠ JobTread not configured (missing JOBTREAD_GRANT_KEY or JOBTREAD_ORG_ID)"

    try:
        import requests
    except ImportError:
        return "  ⚠ requests not installed"

    query = {
        "organization": {
            "$": {"id": JOBTREAD_ORG_ID, "grantKey": JOBTREAD_GRANT_KEY},
            "projects": {
                "nodes": {
                    "id": {},
                    "name": {},
                    "status": {},
                    "startDate": {},
                    "endDate": {},
                }
            }
        }
    }

    try:
        resp = requests.post("https://api.jobtread.com/pave", json={"query": query}, timeout=30)
        if resp.status_code != 200:
            return f"  ⚠ JobTread API error: {resp.status_code}"

        projects = resp.json().get("organization", {}).get("projects", {}).get("nodes", [])
        if not projects:
            return "  No active projects."

        lines = []
        active = [p for p in projects if p.get("status") in ("active", "in_progress", "open")]
        for p in active[:5]:  # Top 5 active projects
            lines.append(f"  📋 {p.get('name', 'Unnamed')} — {p.get('status', 'N/A')}")
            if p.get("endDate"):
                lines.append(f"     End date: {p.get('endDate')}")

        return "\n".join(lines) if lines else "  No active projects."

    except Exception as e:
        return f"  ⚠ JobTread error: {e}"


def get_gmail_unread():
    """Get unread email count and recent subjects from Gmail."""
    if not TOKEN_FILE.exists():
        return "  ⚠ Google not authenticated (run google_mail.py authenticate)"

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        return "  ⚠ Google API libraries not installed"

    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE))
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())

        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(
            userId="me", maxResults=5, q="is:unread"
        ).execute()
        messages = results.get("messages", [])

        if not messages:
            return "  ✅ No unread emails."

        lines = [f"  📬 {len(messages)} unread email(s):"]
        for msg_ref in messages[:5]:
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"], format="metadata",
                metadataHeaders=["From", "Subject"]
            ).execute()
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            subject = headers.get("Subject", "(no subject)")[:50]
            sender = headers.get("From", "Unknown")[:40]
            lines.append(f"    • {subject}")
            lines.append(f"      From: {sender}")

        return "\n".join(lines)

    except Exception as e:
        return f"  ⚠ Gmail error: {e}"


def get_drive_pending():
    """Check for unprocessed files in the Drive raw folder."""
    RAW_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_RAW_FOLDER_ID", "")
    if not RAW_FOLDER_ID or not TOKEN_FILE.exists():
        return "  ⚠ Drive not configured"

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        return "  ⚠ Google API libraries not installed"

    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE))
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())

        service = build("drive", "v3", credentials=creds)
        results = service.files().list(
            q=f"'{RAW_FOLDER_ID}' in parents and trashed=false",
            fields="files(id, name)",
        ).execute()
        files = results.get("files", [])

        if not files:
            return "  ✅ No pending files in Drive raw folder."

        lines = [f"  📎 {len(files)} file(s) pending upload to JobTread:"]
        for f in files[:5]:
            lines.append(f"    • {f['name']}")

        return "\n".join(lines)

    except Exception as e:
        return f"  ⚠ Drive error: {e}"


def generate_briefing():
    """Generate the full daily briefing."""
    today = datetime.now().strftime("%A, %B %d, %Y")

    sections = [
        f"🌅 **Construction Company — Daily Briefing**",
        f"📅 {today}\n",
        f"**📬 Email:**\n{get_gmail_unread()}\n",
        f"**📋 JobTread Projects:**\n{get_jobtread_projects()}\n",
        f"**📎 Drive → JobTread Queue:**\n{get_drive_pending()}\n",
    ]

    return "\n".join(sections)


def main():
    parser = argparse.ArgumentParser(description="Daily Briefing — Construction Company")
    parser.add_argument("--telegram", action="store_true", help="Format for Telegram")
    args = parser.parse_args()

    briefing = generate_briefing()
    print(briefing)


if __name__ == "__main__":
    main()