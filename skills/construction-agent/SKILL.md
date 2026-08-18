---
name: construction-agent
description: "Construction company AI agent — orchestrates email (Google Workspace), project management (JobTread Pave API), and file routing for a construction business. Handles email triage, attachment routing to JobTread, project status, task management, and daily briefings via Telegram. Reference implementation for a construction/trades business with an existing email→Drive→PM pipeline."
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [construction, trades, jobtread, google-workspace, email, project-management, small-business]
    related_skills: [outlook-graph, crm-lite, lead-to-payment]
---

# Construction Agent — Email → Project Management Pipeline

## Overview

A reference implementation of an AI agent that runs the back-office of a construction company. The agent orchestrates between three systems a construction business already uses:

1. **Email** (Google Workspace / Gmail) — where leads, estimates, and project documents arrive
2. **File storage** (Google Drive) — where email attachments are auto-dumped by an existing script
3. **Project management** (JobTread, or similar PM system) — where files and tasks need to end up

The agent bridges the gap: it monitors Drive for new files, downloads them, uploads them to the PM system, and notifies the owner — all through text messages the owner already reads.

**For who:** A construction or trades business (general contractor, remodeler, specialty trade) where:
- The owner gets project documents via email
- Email attachments are dumped to a Drive folder (by a separate script or filter)
- Files need to get into a PM system (JobTread, Procore, Buildertrend, etc.)
- The owner doesn't want to manually download and re-upload everything

## When to Use

- A customer or subcontractor emails a project document (plans, permits, invoices, photos)
- The owner asks "what's in the inbox?" or "what came in today?"
- A scheduled cron checks for new files to route to the PM system
- The owner wants a morning briefing: today's tasks, deadlines, new emails
- The owner needs a project status check from the PM system

## The Pattern

Every action follows the same philosophy as all Mom-n-Pop skills:

1. **Agent drafts** — the agent reads email, prepares file uploads, drafts replies
2. **Owner approves** — the owner gets a Telegram message, confirms before anything is sent
3. **Agent executes** — only after approval does anything go out

The exception is file routing (Drive → PM system), which runs autonomously on a cron because it's non-destructive (files are moved, not deleted; originals are preserved). The owner still gets a notification of what was routed.

## Core Workflows

### 1. Email → Drive → Project Management Pipeline

This is the main pipeline. Many construction businesses already have a script that dumps email attachments to a Drive "raw inbox" folder. The agent completes the circuit:

```
Email arrives → existing script dumps attachment to Drive →
Agent polls Drive folder (every 15 min via cron) →
Downloads attachment locally (temp) →
Uploads to PM system via API →
Deletes local temp file →
Moves Drive file to "processed" folder →
Sends Telegram notification to owner
```

**Why the agent does this:** The previous setup got files into Drive, but getting them from Drive into the PM system required manual download + upload. The agent automates that last mile.

### 2. Email Triage

- Reads Gmail inbox (via Google API)
- Summarizes unread emails
- Drafts replies (dual-approval: agent drafts, owner approves via Telegram or Gmail)
- Flags urgent items

### 3. Project Management Queries

- Query projects, tasks, schedules from the PM system
- Create/update tasks
- Daily briefing: today's tasks, upcoming deadlines
- Weekly summary: project progress, completed tasks

### 4. Daily Briefing (cron, 8 AM)

- New emails from overnight
- Today's tasks from the PM system
- Upcoming deadlines
- Files processed

## API Integrations

### Google Workspace

- **Auth:** OAuth2 (one-time browser flow, token persists at `~/.hermes/cache/google_token.json`)
- **APIs:** Gmail, Google Drive, Google Calendar
- **Scopes:** `gmail.readonly`, `gmail.send`, `drive.readonly`, `drive.file`, `calendar.readonly`
- **Setup:** See `references/google-workspace-setup.md`

### JobTread (Pave API)

JobTread is a construction-specific PM system. The Pave API pattern applies to similar construction PM tools (Procore, Buildertrend, etc.) — adapt the query language to your specific system.

- **Endpoint:** `POST https://api.jobtread.com/pave`
- **Auth:** Grant key (from JobTread Settings → Integrations → API)
- **Query Language:** Pave (similar to GraphQL, but not identical)
- **Grant keys expire after 3 months of inactivity** — must use regularly
- **Setup:** See `references/jobtread-api-setup.md`

## Environment Variables

All set in `~/.hermes/.env` (chmod 600):

```bash
# Google Workspace
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_MAILBOX=info@yourdomain.com

# JobTread (or your PM system)
JOBTREAD_GRANT_KEY=your_grant_key_here
JOBTREAD_ORG_ID=your_org_id_here

# Google Drive (for attachment pipeline)
GOOGLE_DRIVE_RAW_FOLDER_ID=your_raw_folder_id
GOOGLE_DRIVE_PROCESSED_FOLDER_ID=your_processed_folder_id
```

## Cron Jobs

| Name | Schedule | What |
|------|----------|------|
| Daily Briefing | `0 8 * * *` | Email summary, today's tasks, deadlines |
| Drive Poll | `*/15 * * * *` | Check Drive for new attachments → upload to PM system |
| Weekly Summary | `0 9 * * 1` | Project progress, completed tasks, files processed |

## Key Scripts

| Script | Purpose | Requires |
|--------|---------|----------|
| `scripts/google_mail.py` | Gmail read/draft/send (Google API) | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_MAILBOX` |
| `scripts/jobtread_pave.py` | JobTread Pave API client | `JOBTREAD_GRANT_KEY`, `JOBTREAD_ORG_ID` |
| `scripts/drive_to_jobtread.py` | Email→Drive→PM pipeline | Google Drive + JobTread credentials |
| `scripts/daily_briefing.py` | Morning briefing generator | All of the above |

## Adapting to Other PM Systems

If you use Procore, Buildertrend, CoConstruct, or another construction PM system instead of JobTread:

1. Replace `scripts/jobtread_pave.py` with a client for your PM system's API
2. Update the query/mutation structure in `scripts/drive_to_jobtread.py` to use your PM system's file upload endpoint
3. Update `scripts/daily_briefing.py` to query your PM system's task/project schema
4. Update the environment variables to match your PM system's auth method

The pipeline pattern (Drive → download → upload → move → notify) stays the same.

## Pitfalls

1. **PM system API keys can expire** — JobTread grant keys expire after 3 months of inactivity. A daily briefing cron that queries the API keeps it active. If your PM system has similar expiration, keep it active with scheduled calls.

2. **Google OAuth tokens refresh automatically** but can fail if the refresh token is revoked (password change, admin revocation). Monitor for auth errors and re-run the authentication flow when needed.

3. **Pave is NOT GraphQL** — it's similar but different syntax. Inputs are passed after the `$` symbol, and empty braces `{}` mean "return this field." Check the API explorer for your PM system before assuming GraphQL syntax works.

4. **File routing is non-destructive** — the pipeline moves Drive files to a "processed" folder rather than deleting them. This is intentional. If your pipeline deletes, add a confirmation step.

5. **Headless VPS auth** — the one-time Google OAuth flow needs a browser. Use SSH port forwarding (`ssh -L 8080:localhost:8080`) to complete the flow from your local machine, or run the auth on your local machine and copy the token file to the VPS.

6. **Large file handling** — construction documents (plans, permits) can be large. The Drive → PM upload uses a temp directory; ensure sufficient disk space. Clean up temp files after each run.

## Verification Checklist

- [ ] Google Cloud Project created with Gmail, Drive, Calendar APIs enabled
- [ ] OAuth credentials created (Desktop app type)
- [ ] Environment variables set: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_MAILBOX`
- [ ] One-time OAuth authentication completed (token saved)
- [ ] Test: `google_mail.py read --count 5` returns inbox
- [ ] JobTread (or PM system) grant key obtained
- [ ] Environment variables set: `JOBTREAD_GRANT_KEY`, `JOBTREAD_ORG_ID`
- [ ] Test: `jobtread_pave.py projects` returns project list
- [ ] Drive folder IDs identified (raw + processed)
- [ ] Test: `drive_to_jobtread.py --dry-run` shows pending files
- [ ] Test: `drive_to_jobtread.py` processes one file end-to-end
- [ ] Daily briefing cron configured and sending
- [ ] Drive poll cron configured and running

## Related

- [outlook-graph](../outlook-graph/) — Microsoft 365 email alternative (if the business uses Outlook instead of Google Workspace)
- [crm-lite](../crm-lite/) — lightweight CRM if the PM system doesn't handle lead tracking
- [lead-to-payment](../lead-to-payment/) — full sales pipeline orchestration
- `references/google-workspace-setup.md` — step-by-step Google OAuth setup
- `references/jobtread-api-setup.md` — JobTread Pave API guide