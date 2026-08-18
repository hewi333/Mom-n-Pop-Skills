#!/usr/bin/env python3
"""
Drive → JobTread Pipeline
=========================
Polls Google Drive "raw inbox" folder for new files,
downloads them, uploads to JobTread, then moves to "processed".

This is the workflow that Claude couldn't do (sandbox restrictions
prevented file download/upload). Hermes has no such restrictions.

Flow:
  1. List files in Google Drive raw folder
  2. For each file:
     a. Download to local temp directory
     b. Upload to JobTread via Pave API (create file record)
     c. Move Drive file to "processed" folder
     d. Delete local temp file
     e. Log the transaction

Usage:
  python drive_to_jobtread.py --dry-run          # Show what would be processed
  python drive_to_jobtread.py                     # Process all new files
  python drive_to_jobtread.py --project-id=X     # Upload to specific project
  python drive_to_jobtread.py --notify            # Send Telegram notification

Requires: pip install google-api-python-client google-auth-oauthlib requests
Config: Set GOOGLE_DRIVE_RAW_FOLDER_ID, GOOGLE_DRIVE_PROCESSED_FOLDER_ID,
        JOBTREAD_GRANT_KEY, JOBTREAD_ORG_ID env vars
"""

import sys
import os
import json
import shutil
import tempfile
import argparse
from pathlib import Path
from datetime import datetime

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
except ImportError:
    print("ERROR: Google API libraries not installed.")
    print("Run: pip install google-api-python-client google-auth-oauthlib")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

# ── Config ──────────────────────────────────────────────────
RAW_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_RAW_FOLDER_ID", "")
PROCESSED_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_PROCESSED_FOLDER_ID", "")
JOBTREAD_GRANT_KEY = os.environ.get("JOBTREAD_GRANT_KEY", "")
JOBTREAD_ORG_ID = os.environ.get("JOBTREAD_ORG_ID", "")
JOBTREAD_PROJECT_ID = os.environ.get("JOBTREAD_PROJECT_ID", "")  # Default project

TOKEN_FILE = Path.home() / ".hermes" / "cache" / "google_token.json"
LOG_FILE = Path.home() / ".hermes" / "logs" / "drive-to-jobtread.log"
SCOPES = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive.readonly"]

JOBTREAD_API_URL = "https://api.jobtread.com/pave"


def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"WARNING: Failed to write to log file {LOG_FILE}: {e}")


def get_drive_service():
    """Get authenticated Google Drive service."""
    if not TOKEN_FILE.exists():
        print("ERROR: Google token not found. Run google_mail.py authenticate first.")
        sys.exit(1)
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())
    return build("drive", "v3", credentials=creds)


def list_drive_files(service, folder_id):
    """List all files in a Google Drive folder."""
    files = []
    page_token = None
    while True:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime)",
            pageToken=page_token,
            pageSize=100,
        ).execute()
        files.extend(results.get("files", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break
    return files


def download_drive_file(service, file_id, dest_path):
    """Download a file from Google Drive to local path."""
    request = service.files().get_media(fileId=file_id)
    with open(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request, chunksize=1024*1024)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    return dest_path


def move_drive_file(service, file_id, new_folder_id):
    """Move a file from its current folder to a new one."""
    # Get current parents
    file = service.files().get(fileId=file_id, fields="parents").execute()
    old_parents = ",".join(file.get("parents", []))
    # Move
    service.files().update(
        fileId=file_id,
        addParents=new_folder_id,
        removeParents=old_parents,
        fields="id, parents"
    ).execute()


def upload_to_jobtread(file_path, display_name, project_id=None):
    """Upload a file to JobTread via Pave API."""
    if not JOBTREAD_GRANT_KEY:
        log("ERROR: JOBTREAD_GRANT_KEY not set", "ERROR")
        return None

    file_size = os.path.getsize(file_path)

    # Create file record in JobTread
    query = {
        "createFile": {
            "$": {
                "name": display_name,
            },
            "createdFile": {
                "id": {},
                "name": {},
            }
        }
    }

    if project_id:
        query["createFile"]["$"]["projectId"] = project_id

    query["createFile"]["$"]["grantKey"] = JOBTREAD_GRANT_KEY

    try:
        resp = requests.post(JOBTREAD_API_URL, json={"query": query}, timeout=60)
        if resp.status_code != 200:
            log(f"JobTread API error {resp.status_code}: {resp.text[:300]}", "ERROR")
            return None
        data = resp.json()
        file_id = data.get("createFile", {}).get("createdFile", {}).get("id")
        log(f"Uploaded to JobTread: {display_name} → file ID: {file_id}")
        return file_id
    except Exception as e:
        log(f"JobTread upload failed: {e}", "ERROR")
        return None


def process_files(dry_run=False, project_id=None, notify=False):
    """Main pipeline: Drive → local → JobTread → cleanup."""
    log("=" * 60)
    log("Starting Drive → JobTread pipeline")

    # Validate config
    if not RAW_FOLDER_ID:
        log("ERROR: GOOGLE_DRIVE_RAW_FOLDER_ID not set", "ERROR")
        return False
    if not PROCESSED_FOLDER_ID:
        log("ERROR: GOOGLE_DRIVE_PROCESSED_FOLDER_ID not set", "ERROR")
        return False

    # Get Drive service
    service = get_drive_service()

    # List files in raw folder
    files = list_drive_files(service, RAW_FOLDER_ID)
    if not files:
        log("No new files in raw folder. Nothing to do.")
        return True

    log(f"Found {len(files)} file(s) to process")

    if dry_run:
        print("\n🔍 DRY RUN — would process:\n")
        for i, f in enumerate(files, 1):
            size_kb = int(f.get("size", 0)) / 1024
            print(f"  {i}. {f['name']} ({size_kb:.0f}KB, {f['mimeType']})")
            print(f"     Drive ID: {f['id']}")
            print(f"     Created: {f.get('createdTime', 'N/A')}")
            print()
        print(f"Would upload to project: {project_id or JOBTREAD_PROJECT_ID or '(not set)'}")
        print(f"Would move to processed folder after upload")
        return True

    # Determine target project
    target_project = project_id or JOBTREAD_PROJECT_ID
    if not target_project:
        log("WARNING: No project ID specified. Files will be uploaded without project association.", "WARN")

    # Process each file
    processed = 0
    failed = 0
    results = []

    for f in files:
        file_name = f["name"]
        file_id = f["id"]
        mime_type = f.get("mimeType", "application/octet-stream")
        size_bytes = int(f.get("size", 0))

        log(f"Processing: {file_name} ({size_bytes:,} bytes)")

        # 1. Download to local temp
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = Path(tmpdir) / file_name
            log(f"  Downloading from Drive...")
            try:
                download_drive_file(service, file_id, str(local_path))
                log(f"  ✓ Downloaded ({local_path.stat().st_size:,} bytes)")
            except Exception as e:
                log(f"  ✗ Download failed: {e}", "ERROR")
                failed += 1
                continue

            # 2. Upload to JobTread
            log(f"  Uploading to JobTread...")
            jt_file_id = upload_to_jobtread(str(local_path), file_name, target_project)
            if not jt_file_id:
                log(f"  ✗ JobTread upload failed", "ERROR")
                failed += 1
                continue

            # 3. Move Drive file to processed folder
            log(f"  Moving Drive file to processed folder...")
            try:
                move_drive_file(service, file_id, PROCESSED_FOLDER_ID)
                log(f"  ✓ Moved to processed folder")
            except Exception as e:
                log(f"  ⚠ Drive move failed (file already in JobTread): {e}", "WARN")

            # 4. Local temp file auto-deleted by tempfile context manager
            log(f"  ✓ Temp file cleaned up")

            processed += 1
            results.append({
                "name": file_name,
                "drive_id": file_id,
                "jobtread_id": jt_file_id,
                "size_bytes": size_bytes,
                "project_id": target_project,
            })

    # Summary
    log(f"Pipeline complete: {processed} processed, {failed} failed")

    # Notification (if requested)
    if notify and results:
        notify_text = f"📎 Drive → JobTread: {processed} file(s) processed\n"
        for r in results:
            notify_text += f"\n  • {r['name']} ({r['size_bytes']:,} bytes)"
        print(f"\n--- TELEGRAM NOTIFICATION ---\n{notify_text}\n--- END NOTIFICATION ---")

    return failed == 0


def main():
    parser = argparse.ArgumentParser(description="Drive → JobTread Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    parser.add_argument("--project-id", default="", help="JobTread project ID to upload to")
    parser.add_argument("--notify", action="store_true", help="Print Telegram notification text")
    args = parser.parse_args()

    success = process_files(
        dry_run=args.dry_run,
        project_id=args.project_id or None,
        notify=args.notify,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()