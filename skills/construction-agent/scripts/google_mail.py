#!/usr/bin/env python3
"""
Google Workspace Mail Client
=============================
Read, draft, and send emails via Gmail API.
Drafts save to Gmail's Drafts folder for dual-approval
(Telegram or Gmail). Uses OAuth2 for headless server auth.

Requires: pip install google-api-python-client google-auth-oauthlib

Usage:
  python google_mail.py authenticate           # One-time OAuth flow
  python google_mail.py read [--count 10] [--unread-only]
  python google_mail.py inbox-summary [--count 10]
  python google_mail.py read-email <message_id>
  python google_mail.py draft-reply <message_id> --body "reply text"
  python google_mail.py draft-new --to addr@example.com --subject "Subject" --body "body"
  python google_mail.py list-drafts
  python google_mail.py send-draft <draft_id> [--yes]
  python google_mail.py send-draft-by-index <index> [--yes]
  python google_mail.py delete-draft <draft_id>
"""

import sys
import json
import os
import argparse
import base64
from pathlib import Path
from datetime import datetime

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("ERROR: Google API libraries not installed.")
    print("Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
    sys.exit(1)

# ── Config ──────────────────────────────────────────────────
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
MAILBOX = os.environ.get("GOOGLE_MAILBOX", "info@constructionconstruction.com")

# Token persistence
TOKEN_DIR = Path.home() / ".hermes" / "cache"
TOKEN_DIR.mkdir(parents=True, exist_ok=True)
TOKEN_FILE = TOKEN_DIR / "google_token.json"
DRAFT_STATE_FILE = TOKEN_DIR / "google_drafts.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def get_credentials():
    """Get OAuth credentials, refreshing if needed."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())
        return creds

    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET not set.")
        print("See references/google-workspace-setup.md for setup instructions.")
        sys.exit(1)

    # Run OAuth flow — requires a browser for initial auth
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        },
        scopes=SCOPES,
    )
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json())
    print(f"✅ Authenticated! Token saved to {TOKEN_FILE}")
    print(f"   Connected to: {MAILBOX}")
    return creds


def get_service():
    """Get Gmail API service."""
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def get_drive_service():
    """Get Google Drive API service."""
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


# ── Draft tracking ──────────────────────────────────────────
def load_draft_state():
    if DRAFT_STATE_FILE.exists():
        with open(DRAFT_STATE_FILE) as f:
            return json.load(f)
    return {"drafts": []}


def save_draft_state(state):
    with open(DRAFT_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def track_draft(draft_id, to_addr, subject, body_preview, draft_type="reply"):
    state = load_draft_state()
    state["drafts"].append({
        "google_id": draft_id, "to": to_addr, "subject": subject,
        "preview": body_preview[:200], "type": draft_type,
        "created_at": datetime.now().isoformat(), "status": "pending_approval"
    })
    save_draft_state(state)


def update_draft_status(draft_id, status):
    state = load_draft_state()
    for d in state["drafts"]:
        if d["google_id"] == draft_id:
            d["status"] = status
    save_draft_state(state)


# ── Commands ────────────────────────────────────────────────
def cmd_authenticate(args):
    get_credentials()


def cmd_read(args):
    service = get_service()
    count = args.count or 10
    q = "is:unread" if args.unread_only or args.unread else None
    results = service.users().messages().list(
        userId="me", maxResults=count, q=q
    ).execute()
    messages = results.get("messages", [])

    if not messages:
        print("📭 No emails found.")
        return

    print(f"📬 Inbox ({len(messages)} emails)\n")
    for i, msg_ref in enumerate(messages, 1):
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        print(f"{i}. {headers.get('From', 'Unknown')} — {headers.get('Subject', '(no subject)')} [{msg['id']}]")


def cmd_inbox_summary(args):
    service = get_service()
    count = args.count or 10
    results = service.users().messages().list(
        userId="me", maxResults=count, q="is:unread"
    ).execute()
    messages = results.get("messages", [])

    if not messages:
        print("📭 Inbox is clear — no unread emails.")
        return

    lines = [f"📬 Inbox — {len(messages)} unread\n"]
    for i, msg_ref in enumerate(messages, 1):
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="full"
        ).execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

        # Extract body
        body = extract_body(msg.get("payload", {}))
        preview = body[:150].replace("\n", " ").strip()

        lines.append(f"{i}. **{headers.get('Subject', '(no subject)')}**")
        lines.append(f"   From: {headers.get('From', 'Unknown')}")
        lines.append(f"   {preview}")
        lines.append(f"   ID: {msg['id']}\n")

    print("\n".join(lines))


def extract_body(payload):
    """Extract text content from Gmail message payload."""
    body = ""
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain" and "data" in part.get("body", {}):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                break
            elif part["mimeType"] == "text/html" and "data" in part.get("body", {}):
                html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                # Simple HTML stripping
                import re
                body = re.sub(r'<[^>]+>', ' ', html).strip()
                break
    elif "body" in payload and "data" in payload["body"]:
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    return body


def cmd_read_email(args):
    service = get_service()
    msg = service.users().messages().get(
        userId="me", id=args.message_id, format="full"
    ).execute()

    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    print(f"From: {headers.get('From', 'N/A')}")
    print(f"To: {headers.get('To', 'N/A')}")
    print(f"Subject: {headers.get('Subject', 'N/A')}")
    print(f"Received: {headers.get('Date', 'N/A')}\n")

    body = extract_body(msg.get("payload", {}))
    print(body)

    # Check for attachments
    if "parts" in msg.get("payload", {}):
        attachments = [p for p in msg["payload"]["parts"] if p.get("filename")]
        if attachments:
            print(f"\n📎 Attachments ({len(attachments)}):")
            for a in attachments:
                print(f"   {a['filename']} ({a.get('mimeType', 'unknown')})")


def cmd_draft_reply(args):
    service = get_service()
    # Get original message
    msg = service.users().messages().get(
        userId="me", id=args.message_id, format="metadata",
        metadataHeaders=["From", "Subject"]
    ).execute()
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

    # Create reply
    subject = headers.get("Subject", "")
    if not subject.startswith("Re:"):
        subject = f"Re: {subject}"

    raw = create_email_raw(
        to=headers.get("From", ""),
        subject=subject,
        body=args.body,
        in_reply_to=msg["id"],
        references=msg["id"]
    )

    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw}}
    ).execute()

    track_draft(draft["id"], headers.get("From", ""), subject, args.body, "reply")
    print(f"✅ Draft saved to Gmail Drafts.")
    print(f"   To: {headers.get('From', '')}")
    print(f"   Subject: {subject}")
    print(f"   ID: {draft['id']}")
    print(f"\n📋 Approve via: Gmail Drafts folder OR Telegram 'send draft {draft['id']}'")


def cmd_draft_new(args):
    service = get_service()
    raw = create_email_raw(
        to=args.to, subject=args.subject, body=args.body, cc=args.cc
    )
    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw}}
    ).execute()

    track_draft(draft["id"], args.to, args.subject, args.body, "new")
    print(f"✅ Draft saved. To: {args.to} | Subject: {args.subject} | ID: {draft['id']}")


def create_email_raw(to, subject, body, cc=None, in_reply_to=None, references=None):
    """Create a base64url-encoded raw email message."""
    from email.mime.text import MIMEText
    from email.utils import formataddr

    msg = MIMEText(body)
    msg["to"] = to
    msg["subject"] = subject
    if cc:
        msg["cc"] = cc
    if in_reply_to:
        msg["in-reply-to"] = in_reply_to
    if references:
        msg["references"] = references

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return raw


def cmd_list_drafts(args):
    service = get_service()
    drafts = service.users().drafts().list(userId="me").execute().get("drafts", [])
    if not drafts:
        print("📭 No drafts.")
        return

    state = load_draft_state()
    tracked_ids = {d["google_id"] for d in state["drafts"]}

    print(f"📝 Drafts ({len(drafts)} total)\n")
    for i, d in enumerate(drafts, 1):
        draft = service.users().drafts().get(userId="me", id=d["id"], format="metadata").execute()
        msg = draft.get("message", {})
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        source = "agent" if d["id"] in tracked_ids else "manual"
        to_addr = headers.get("To", "(no recipient)")[:35]
        print(f"{i}. [{source}] To: {to_addr} | {headers.get('Subject', '(no subject)')} | ID: {d['id']}")


def cmd_send_draft(args):
    service = get_service()
    try:
        draft = service.users().drafts().get(userId="me", id=args.message_id).execute()
    except Exception:
        print(f"❌ Draft not found: {args.message_id}")
        return

    msg = draft.get("message", {})
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    print(f"📤 Sending: To: {headers.get('To', '?')} | Subject: {headers.get('Subject', '?')}")

    if not args.yes:
        if input("Send? (yes/no): ").lower() not in ["yes", "y"]:
            print("❌ Cancelled.")
            return

    service.users().drafts().send(userId="me", body={"id": args.message_id}).execute()
    update_draft_status(args.message_id, "sent")
    print("✅ Sent.")


def cmd_send_draft_by_index(args):
    service = get_service()
    drafts = service.users().drafts().list(userId="me").execute().get("drafts", [])
    if args.index < 1 or args.index > len(drafts):
        print(f"❌ Invalid index. Range: 1-{len(drafts)}")
        return
    draft_id = drafts[args.index - 1]["id"]
    args.message_id = draft_id
    cmd_send_draft(args)


def cmd_delete_draft(args):
    service = get_service()
    try:
        service.users().drafts().delete(userId="me", id=args.message_id).execute()
        print(f"🗑️ Deleted: {args.message_id}")
    except Exception as e:
        print(f"❌ Error: {e}")


# ── CLI ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Google Workspace Mail Agent — read, draft, send emails")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("authenticate", help="Connect Google Workspace account (one-time)")
    p = sub.add_parser("read", help="List inbox")
    p.add_argument("--count", type=int, default=10)
    p.add_argument("--unread-only", action="store_true")
    p.add_argument("--unread", action="store_true")
    p = sub.add_parser("inbox-summary", help="Telegram-friendly summary")
    p.add_argument("--count", type=int, default=10)
    p = sub.add_parser("read-email", help="Read one email")
    p.add_argument("message_id")
    p = sub.add_parser("draft-reply", help="Draft a reply")
    p.add_argument("message_id")
    p.add_argument("--body", required=True)
    p = sub.add_parser("draft-new", help="Draft new email")
    p.add_argument("--to", required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--cc")
    sub.add_parser("list-drafts", help="List drafts")
    p = sub.add_parser("send-draft", help="Send draft by ID")
    p.add_argument("message_id")
    p.add_argument("--yes", "-y", action="store_true")
    p = sub.add_parser("send-draft-by-index", help="Send draft by #")
    p.add_argument("index", type=int)
    p.add_argument("--yes", "-y", action="store_true")
    p = sub.add_parser("delete-draft", help="Delete draft")
    p.add_argument("message_id")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    cmds = {
        "authenticate": cmd_authenticate,
        "read": cmd_read,
        "inbox-summary": cmd_inbox_summary,
        "read-email": cmd_read_email,
        "draft-reply": cmd_draft_reply,
        "draft-new": cmd_draft_new,
        "list-drafts": cmd_list_drafts,
        "send-draft": cmd_send_draft,
        "send-draft-by-index": cmd_send_draft_by_index,
        "delete-draft": cmd_delete_draft,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()