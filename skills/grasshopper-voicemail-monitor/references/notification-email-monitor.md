# Notification Email Monitor — Website Contact Forms (and Anything Else)

Second application of the IMAP-polling + `no_agent=True` cron pattern (same
architecture as the voicemail monitor). The website contact form emails a
structured notification to the owner's inbox; a cron script polls for it,
parses the fields, logs the lead to CRM, and delivers a formatted message
to the owner's Telegram.

## Source

Any form handler that sends email works: a serverless function calling an
email API (Resend, Postmark, SES) or plain SMTP. Define:
- A **stable subject prefix** to match on (e.g. `New website lead:`)
- A **structured plain-text body** — `Field:    value` lines are trivially parseable
- **Reply-To set to the submitter's email** so the owner can hit Reply

Example body:

```
Name:     Jane Smith
Phone:    (555) 123-4567
Email:    jane@example.com
Address:  123 Main St
City:     Exampleville
Service:  Cigarette smoke
Website estimate: $2,550 – $3,450 (or "not run")
Message:  (multi-line, if provided)
Submitted: 2026-09-08T14:32:00Z
```

## Script

`~/.hermes/scripts/notification_monitor.py` — no arguments needed if it
polls a single inbox, so the cron `script` field can call it directly.
Scripts that need arguments require wrapper scripts — see
`references/cron-script-arguments.md`.

## Cron job

- Schedule: `*/3 * * * *` (recurring — NOT "once in 3m", which is a one-shot)
- `no_agent: true` — script-only, zero tokens when idle
- Deliver: the owner's Telegram chat

## Pitfalls

### 1. RFC 2047-encoded subjects (silent parse failure)

Some IMAP servers return subjects with RFC 2047 encoding (e.g.
`=?utf-8?b?TmV3IHdlYnNpdGUgbGVhZDog...?=`). Python's `msg.get("Subject")`
returns the RAW encoded string — a prefix check like
`"New website lead:" in subject` FAILS because the raw bytes don't contain
the literal text. The monitor runs, finds the email, parses nothing, marks
it processed, and never revisits it. This is a **silent** failure — no error,
no delivery.

**Fix — decode before matching:**

```python
import email.header
raw_subject = msg.get("Subject", "")
subject = str(email.header.make_header(email.header.decode_header(raw_subject)))
```

### 2. IMAP UIDs ≠ mail-client message IDs

A CLI mail client's `envelope list` shows sequence/message IDs that are NOT
IMAP UIDs — the server assigns its own UIDs internally. When debugging "the
monitor missed an email I can see in the inbox," check the IMAP UID directly
with `imaplib.search()`, not the client's displayed ID.

### 3. First-run flood prevention

Same as the voicemail monitor: on first run with no tracking file, ALL
matching emails are marked as processed. Tracking file:
`~/.hermes/cron/state/{monitor_name}_uids.json`.

### 4. End-to-end testing without a real lead

1. Send a synthetic email matching your format to the polled inbox (via SMTP)
2. Remove its UID from the tracking file
3. Run the monitor — it should parse, log to CRM, and print the Telegram message
4. Clean the test record out of the CRM

### 5. Keep the parser in sync with form validation

If the website form requires "at least one of phone or email" (not both),
the parser must handle three cases: phone only, email only, both. Any
validation change on the website is a parser change too.

## Shared architecture (applies to every email monitor)

1. `imaplib.IMAP4_SSL` to the host (e.g. `imap.secureserver.net:993` for
   GoDaddy Workspace email)
2. `conn.search(None, 'SUBJECT', '"prefix:"')` or `conn.search(None, 'FROM', '"sender"')`
3. UID tracking per monitor in `~/.hermes/cron/state/`
4. First run: mark all as processed (no historical flood)
5. Parse each new email into a structured dict
6. Log to the crm-lite SQLite database
7. Format the Telegram message with tappable `tel:` links
8. Empty stdout = silent = zero tokens (`no_agent=True`)
9. Errors go to stderr; the script never crashes the poll