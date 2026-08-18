# Google Workspace Setup

## Overview
This guide sets up Gmail API, Google Drive API, and Google Calendar API access for a construction company agent.

## Prerequisites
- Google Workspace account (e.g., `info@yourdomain.com`)
- Admin access (or ability to create OAuth credentials)
- The agent VPS with Python 3 installed

## Step 1: Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click project dropdown → **New Project**
3. Name: `construction-agent`
4. Click **Create**

## Step 2: Enable APIs

1. In the project, go to **APIs & Services → Library**
2. Search for and enable:
   - **Gmail API**
   - **Google Drive API**
   - **Google Calendar API**

## Step 3: Create OAuth Credentials

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User type: **Internal** (if Workspace admin) or **External**
   - App name: `Construction Agent`
   - User support email: `info@yourdomain.com`
   - Authorized domains: `yourdomain.com`
4. Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: `Construction Agent`
5. **Copy the Client ID and Client Secret** — you'll need these

## Step 4: Set Environment Variables

On the VPS, add to `~/.hermes/.env`:

```bash
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_MAILBOX=info@yourdomain.com
```

## Step 5: One-Time Authentication

On the VPS (via SSH or tmux), run:

```bash
cd ~/.hermes/skills/construction-agent/scripts
python3 google_mail.py authenticate
```

This will:
1. Print a URL
2. You open it in a browser
3. Log in as `info@yourdomain.com`
4. Grant the requested permissions
5. Token saves to `~/.hermes/cache/google_token.json`

**Note:** On a headless VPS, you need to:
- Run this in a terminal with port forwarding (`ssh -L 8080:localhost:8080`)
- Or run the auth flow on your local machine and copy the token file to the VPS

### SSH Port Forward Method (recommended)

From your local machine:
```bash
ssh -L 8080:localhost:8080 hermes@<vps-ip>
```

Then on the VPS:
```bash
python3 google_mail.py authenticate
```

It will start a local server on a random port. The URL it prints will point to `localhost:PORT`. Open it in your local browser (the port forward makes it accessible).

## Step 6: Get Drive Folder IDs

For the email→Drive→PM system pipeline, you need two Drive folders:

1. **Raw inbox folder** — where your existing email script dumps attachments
2. **Processed folder** — where files go after upload to your PM system

### Get folder IDs:
1. Open Google Drive in browser
2. Navigate to the folder
3. The URL looks like: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
4. Copy the FOLDER_ID from the URL

Add to `~/.hermes/.env`:
```bash
GOOGLE_DRIVE_RAW_FOLDER_ID=1ABC...xyz
GOOGLE_DRIVE_PROCESSED_FOLDER_ID=1DEF...uvw
```

## Step 7: Test

```bash
# Test Gmail connection
python3 google_mail.py read --count 5

# Test Drive connection
python3 drive_to_jobtread.py --dry-run
```

## Token Refresh

- The OAuth token refreshes **automatically** using the refresh token
- No browser needed after initial auth
- If the refresh token is revoked (e.g., password change), you'll need to re-authenticate
- Monitor for auth errors in the agent logs

## Scopes Granted

| Scope | What it allows |
|-------|---------------|
| gmail.readonly | Read emails |
| gmail.send | Send emails (via drafts) |
| gmail.compose | Create/manage drafts |
| drive.readonly | Read Drive files |
| drive.file | Read/write files created by this app |
| calendar.readonly | Read calendar events |

## Domain-Wide Delegation (Alternative)

If you have Workspace admin access, you can use a **service account** with domain-wide delegation instead of OAuth user flow. This is more reliable (no token refresh issues) but requires admin console access.

See: https://developers.google.com/admin-sdk/directory/v1/guides/delegation

## Troubleshooting

**"Access blocked" during auth:** Make sure the OAuth consent screen is configured and your email is listed as a test user (if app is in testing mode).

**Token refresh fails:** Re-run `google_mail.py authenticate` to get a fresh token.

**"File not found" on Drive:** Make sure the folder IDs are correct and the authenticated account has access to those folders.