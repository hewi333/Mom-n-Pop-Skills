---
name: grasshopper-voicemail-monitor
description: "Turn voicemail-drop emails from a virtual phone provider (Grasshopper — or any service that emails transcribed voicemails) into CRM leads and Telegram notifications. Cron-based IMAP polling with the no_agent=True pattern — zero cost when idle. The same architecture works for any structured notification email: contact forms, booking alerts, review notifications."
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [grasshopper, voicemail, imap, cron, crm, lead-intake, monitoring]
    related_skills: [crm-lite, lead-to-payment, hermes-production-ops]
---

# Voicemail & Notification-Email Monitor

## Overview
Many virtual phone products auto-transcribe voicemails and **email the
transcript** to one or more inboxes (Grasshopper — GoDaddy's virtual phone —
does this; Google Voice, OpenPhone and similar services have equivalents).
That email is all you need for a fully automated lead-intake pipeline — no
audio processing, no transcription API, no polling the provider's dashboard.

This skill describes a monitor that polls those inboxes every 3 minutes via
IMAP, extracts the transcript and caller info, logs the voicemail to the CRM
database, and delivers a formatted summary to the right person's Telegram.

**Key insight: the provider already gives you speech-to-text in the email
body.** Don't build transcription — parse the notification.

## Architecture
```
Voicemail left → provider auto-transcribes → notification email → IMAP inbox
  ↓ (cron script polls every 3 min, no_agent=True)
Python monitor script: ~/.hermes/scripts/voicemail_monitor.py
  ├─ IMAP search for unread mail FROM the provider
  ├─ Parse: caller #, transcript, extension, timestamp, callback numbers
  ├─ CRM: create lead (new caller) or log activity (returning caller)
  └─ Format clean Telegram message (tappable phone links)
  ↓ (empty stdout = silent = zero tokens when no new voicemails)
Deliver to the right person (extension routing → their Telegram chat)
```

## Components

### Monitor script
`~/.hermes/scripts/voicemail_monitor.py` — takes one argument identifying
which inbox to poll (e.g. `owner-a` / `owner-b`, one per extension recipient).

**Wrapper scripts (required):** the Hermes cron `script` field treats the
entire string as a filename — including spaces and arguments. A script that
needs an argument cannot be called directly from a cron job. Create one
wrapper per variant:

```bash
#!/bin/bash
# ~/.hermes/scripts/voicemail_owner_a.sh
exec python3 "$(dirname "$0")/voicemail_monitor.py" owner-a
```

See `references/cron-script-arguments.md` for the full pattern.

**First-run behavior:** with no tracking file, the script marks ALL existing
provider emails as processed. This prevents a historical flood of every
voicemail ever received from being delivered on day one. Only genuinely new
voicemails are delivered going forward.

**UID tracking:** processed IMAP UIDs persist in
`~/.hermes/cron/state/voicemail_{inbox}_uids.json`. Survives restarts,
prevents re-delivery.

**Silent when idle:** no new voicemails → empty stdout → the `no_agent=True`
cron delivers nothing. Zero tokens, zero cost when idle.

### Cron jobs
One job per inbox:
- Owner A's inbox → Owner A's Telegram, `*/3 * * * *`
- Owner B's inbox → Owner B's Telegram, `*/3 * * * *`

Both `no_agent=True` (script-only, no LLM involvement). The script's stdout
is delivered verbatim as the Telegram message.

**Use 5-field cron syntax (`*/3 * * * *`) with recurring repeat — NOT
`"once in 3m"`.** "once in 3m" is a one-shot: runs once, completes, stops.
A dead one-shot looks identical to a healthy recurring job until you check
`state` and `enabled` in `cronjob(action='list')`.

### Email format (Grasshopper example)
- **From:** `Grasshopper <notifications@grasshopper.com>`
- **Subject:** `Voicemail from (XXX) XXX-XXXX`
- **Body fields:** Caller, Extension (0 = owner A, 1 = owner B), business
  line, Timestamp
- **Transcript:** inline text between predictable markers
- **Attachment:** .mp3 (not processed — the transcript is sufficient)
- **Edge case:** some voicemails show "Transcription unavailable" when the
  provider's own STT fails. Still create the CRM entry; the message shows
  "(transcript unavailable)". Future enhancement: download the .mp3 and
  transcribe with Whisper as a fallback.

### CRM integration
Writes to the crm-lite SQLite database:
- **New caller:** `customers` record (lead_source='voicemail', lead_status='new')
  + `leads` + `activities` + `communications` records.
- **Returning caller:** matched by last 10 digits of the phone number → new
  `activities` record only; the message shows "returning caller — N previous".
- **Caller name extraction:** parse "Hi, this is X" / "my name is X" from the
  transcript; fall back to "Caller (XXX) XXX-XXXX".
- **Callback numbers:** extract numbers mentioned in the transcript that
  differ from the caller ID ("call me back at ...").

### Telegram message format
All phone numbers are tappable `tel:` markdown links — tapping opens the
dialer on mobile:

```
📞 **New Voicemail**

**From:** [(555) 123-4567](tel:+15551234567)
👤 **Name (from transcript):** Jane Smith
**When:** 6/24/2026 12:05 PM Eastern Daylight Time

> Hi, this is Jane Smith — I'm calling about the odor in
> a condo we're listing, can you give me a quote...

📋 **New lead** created in CRM — Jane Smith
📞 **Callback:** [(555) 987-6543](tel:+15559876543)
```

Returning caller:
```
📞 **New Voicemail**

**From:** [(555) 234-9876](tel:+15552349876) *(returning caller — 2 previous)*
**When:** 3/24/2026 5:03 PM Eastern Daylight Time

> (transcript)

📋 Activity logged in CRM — Jane Smith
```

## Pitfalls

1. **IDLE vs polling:** the IMAP host may support IDLE (check CAPABILITY),
   but polling is simpler and needs no persistent process. 3-min polling is
   near-instant for a business getting a few voicemails a day.
2. **First-run flood prevention:** deleting the tracking file does NOT replay
   history — it starts fresh from that point.
3. **"Transcription unavailable"** is handled gracefully; no audio fallback
   is implemented yet.
4. **Phone matching uses the last 10 digits**, so (555) 234-9876 and
   1-555-234-9876 are the same caller.
5. **Dual delivery:** if both inboxes are configured as recipients for the
   same voicemail, both monitors deliver it. Check the provider's extension
   routing so each voicemail lands in one inbox.
6. **Progress-message flooding:** with `tool_progress: all`, a long
   multi-tool turn streams every intermediate step to end-users' chats — it
   looks like the agent is glitching. Use `tool_progress: final` for
   end-user platforms. See the `hermes-production-ops` skill.
7. **Cascading delegation re-entry:** background delegation results re-enter
   the session as new inbound messages and can trigger unplanned turns. Don't
   dispatch background delegations from messaging sessions unless explicitly
   requested — do the work inline.
8. **Gateway restarts confuse end-users:** restart notifications look like
   errors to non-technical users and generate confused "what's wrong?" texts.
   Suppress with `gateway_restart_notification: false` and plan restarts
   deliberately. See the `hermes-production-ops` skill.
9. **Propose, then build:** a monitor that texts real people and writes to a
   live CRM should never be spun up from a passing comment. Get explicit
   owner approval on the design first — which inbox, which routing, who gets
   pinged — before creating scripts, cron jobs, or CRM records.

## Monitoring & Recovery

### Cron job health
Call `cronjob(action='list')` from any session. Red flags:
- `last_status: "error"` + `enabled: false` — job failed and auto-disabled
- `state: "completed"` + `enabled: false` — a one-shot that ran once and
  stopped (you wanted recurring)
- Healthy: `enabled: true`, recurring, recent `last_run_at`

To fix a dead job, try `cronjob(action='update', job_id='...')` with the
correct script path and schedule. A one-shot must be recreated with
`cronjob(action='create')` using recurring cron syntax.

### Gateway dependency
The cron script's stdout reaches Telegram through the gateway. If the
gateway is down or stuck, delivery stops even when cron jobs are healthy.
Under systemd with `Restart=always`, killing the PID is futile — systemd
revives it in seconds. Stopping it properly requires root:

```bash
sudo systemctl stop hermes-gateway.service   # stops the service + prevents restart
```

If the agent has no sudo access it cannot manage the gateway lifecycle — by
design. Recognize this after one attempt and ask the operator to run it
from SSH, rather than trying five approaches in sequence (each failure is
another streamed message under `tool_progress: all`).

## Reusable Pattern

The IMAP-polling + `no_agent=True` cron architecture works for **any
structured notification email** — contact form submissions, booking
confirmations, review alerts. See `references/notification-email-monitor.md`
for a second application (website contact form → CRM + owner's Telegram),
including the RFC 2047 subject-encoding pitfall that causes silent parse
failures.

## Verification
- First run: silent (marks all existing as processed)
- Second run: silent (no new voicemails)
- Simulate a new voicemail by removing a UID from the tracking file →
  message delivered
- CRM entry created with lead_source='voicemail'
- Returning caller detected by phone match → activity logged, no duplicate
  customer
- Cron jobs show as recurring every 3 min with no_agent=True