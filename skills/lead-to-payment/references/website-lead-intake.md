# Website Lead Intake — Automated Form → CRM → Telegram

v2.0 addition: website contact-form submissions now enter the pipeline
automatically. No webhook, no public endpoint — just email + a cron script.

## Architecture

```
Contact form (serverless function) → email API (Resend/Postmark/SES)
  → owner's inbox, subject "New website lead: {name}, {city} (${low}–${high})"
  → cron job polls inbox every 3 min (no_agent=True, script-only)
  → parse fields → log lead to crm-lite → deliver formatted summary
    to the owner's Telegram
  → owner replies "price it" → lead-to-payment flow continues from step 2
```

Latency ~3 min — irrelevant for a business that gets a few leads a week.
Zero tokens when idle (empty stdout = silent).

## Why email polling instead of a webhook

A webhook gives instant delivery but exposes a public URL on the agent box —
something to secure, rate-limit, and monitor. The form has to send a
notification email anyway (the owner wants the lead in the inbox regardless),
so the same email doubles as the machine-readable intake. Nothing new to
attack. Keep the webhook code in the form handler if you want the option, but
don't activate it until volume justifies the surface area.

## Email format (keep the form and the parser in sync)

The form handler sends a structured plain-text body:

```
Name:     Jane Doe
Phone:    (555) 123-4567
Email:    jane@example.com
Address:  123 Main St
City:     Exampleville
Service:  Cigarette smoke
Website estimate: $2,550 – $3,450   (or "not run")
Region:   Standard
Type:     Residential   Size (sqft): 2400   Add-ons: none
Message:  (multi-line, if provided)
Submitted: 2026-09-08T14:32:00Z
Referrer: https://...
```

- **Reply-To** set to the submitter's email — the owner can hit Reply.
- Required fields: name, address, city, service + **at least one of
  phone/email** (not both required). The parser handles all three cases.

## Implementation notes

1. **RFC 2047 subject encoding (silent failure).** Some IMAP servers return
   the subject RFC 2047-encoded (`=?utf-8?b?...?=`), so a literal
   `"New website lead:" in subject` check FAILS on the raw string — the
   monitor sees the email, parses nothing, marks it processed, and never
   comes back. Always decode before matching:
   ```python
   import email.header
   subject = str(email.header.make_header(
       email.header.decode_header(msg.get("Subject", ""))))
   ```
2. **IMAP UIDs ≠ mail-client IDs.** When debugging a missed email, check
   the IMAP UID with `imaplib.search()`, not the sequence number a CLI mail
   client displays.
3. **First-run flood prevention.** On first run (no tracking file), mark all
   matching emails as processed so a year of old submissions doesn't dump at
   once. Tracking: `~/.hermes/cron/state/website_lead_uids.json`.
4. **End-to-end test without waiting for a real lead.** Send a synthetic
   email matching the format via SMTP, remove its UID from the tracking
   file, run the script, verify CRM + output, then clean the test record.
5. **One script, no arguments** → the cron `script` field can call it
   directly. If you need per-inbox arguments, use wrapper shell scripts
   (see `grasshopper-voicemail-monitor` / `references/cron-script-arguments.md`).

## After intake: the owner gate stays

The monitor only **delivers** the lead — it never prices, contacts, or
charges. The owner sees the summary in Telegram and says "price it" (or
ignores it). Only then does the agent continue with step 2 of the master
flow. The first human gate of lead-to-payment is unchanged; automation just
guarantees the gate gets hit.