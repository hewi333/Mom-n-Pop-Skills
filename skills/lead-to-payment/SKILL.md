---
name: lead-to-payment
description: "Use when a new lead arrives (email, Telegram message, or website form) and needs to move through the full pipeline: qualify the lead, generate an estimate, get owner approval, create a payment link, draft a customer email for owner review, and track payment. This is the master flow that orchestrates estimator-engine, crm-lite, stripe-payments, himalaya (IMAP/SMTP), and quickbooks-online. Owner stays in the loop and approves before anything is sent or charged."
version: "2.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [workflow, orchestration, sales-pipeline, lead-to-cash, owner-in-the-loop]
    related_skills: [estimator-engine, crm-lite, stripe-payments, himalaya, quickbooks-online]
---

# Lead-to-Payment — Master Sales Flow

## Overview
This is the end-to-end pipeline for a service business: a lead comes in, the agent
turns it into a priced estimate, the owner approves it over Telegram, and the agent
creates a payment link or invoice and tracks it to paid. The owner is never bypassed —
the agent **drafts and proposes, the human approves**, then the agent executes. This
mirrors how a small business owner actually wants to work: they stay in control, the
agent removes the 30–60 min of manual work per estimate.

## Environment assumptions
- Model: `zai-org/GLM-5.2` via Together AI, **direct** (no proxy).
- Gateway: Telegram, running as a systemd service. Tool calling works in the gateway.
- Secrets live in `~/.hermes/.env`.
- **Email:** GoDaddy Workspace Email via IMAP/SMTP (`himalaya` CLI, not Microsoft Graph).
  Config at `~/.config/himalaya/config.toml`, password at `~/.config/himalaya/.email-pw`.
  IMAP: `imap.secureserver.net:993` TLS. SMTP: `smtpout.secureserver.net:465` TLS.
  NOT M365 — `outlook-graph` skill is kept as a separate skill for businesses that use real M365.
  See `references/godaddy-email-setup.md` for full setup + verified commands.
- **Payments:** Stripe test mode (`STRIPE_SECRET_KEY` in `.env`).
- QuickBooks is not wired (post-hackathon P1). The flow degrades gracefully without it.

## When to Use
- A referral or customer inquiry arrives (e.g., 80% of leads are referral-based).
- Owner forwards/pastes a lead to the agent in Telegram.
- A website estimator form submission needs a real estimate + payment path.

## The Flow (happy path)

### 1. Intake
Lead arrives one of three ways:
- **Email inbox** (GoDaddy via `himalaya`): owner says "check the email" → agent
  runs `himalaya envelope list` to read the inbox, identifies leads vs spam/newsletters.
- **Telegram** (always works): owner pastes "new lead: Jane Doe, 2,400 sqft home in [CITY],
  cigarette smoke, referral from [Referral Partner]."
- **Website form** (if base44-site-spec is live): form payload hits the agent.

Agent extracts: customer name, contact (email/phone), property address + region,
square footage, property type (residential/commercial/apartment), severity/service type
(e.g. cigarette >5yrs, pet/trauma), lead source.

### 2. Summarize + notify owner (Telegram)
Agent posts a short summary to the owner:
> 📥 New lead — Jane Doe (referral, [Referral Partner])
> 2,400 sqft residential, [CITY] ([REGION]), cigarette smoke >5yrs
> Want me to draft an estimate?

Wait for owner go-ahead before pricing. (Keeps a human gate at the top.)

### 3. Price it — `estimator-engine`
Run the estimator with the extracted details. Use the published rate card from
the estimator-engine config (do not invent prices). For 2,400 sqft standard region,
that's the 1,500–2,500 sf tier at the configured rate per psf plus the cigarette >5yrs
extended add-on. Return structured line items, not just a total.

### 4. Log to CRM — `crm-lite`
Upsert the customer and create a lead/estimate record:
- `customers`: name, email, phone, address, city, state, zip, `lead_source`, `lead_status=qualified`
- `estimates`: line items, total, `status=draft`, link back to customer id

### 5. Propose the estimate to the owner (Telegram) — APPROVAL GATE
Show the owner the full estimate and ask before sending:
> 🧾 Estimate for Jane Doe — **$3,300**
> • Odor treatment, 2,400 sqft @ $1.25 = $3,000
> • Cigarette >5yrs extended = +$550   (adjust per rate card tier)
> • Travel surcharge ([REGION]) = +$75
> Send this to the customer as a payment link / invoice? (yes / edit / no)

Do NOT send or charge anything until the owner says yes.

### 6. On approval — create the charge — `stripe-payments`
Default to a **Stripe payment link** (simplest, most demo-friendly). For NET-30 jobs
use a Stripe invoice instead. Amounts are in **cents** ($3,300 = 330000).
- Create/lookup Stripe customer (store metadata: region, sqft, source).
- Create payment link (or invoice → finalize → send).
- Capture the returned `https://buy.stripe.com/...` URL.

### 7. Draft customer email — `himalaya` (IMAP/SMTP) — DRAFT ONLY, NO AUTO-SEND
Agent composes a customer-facing email from `owner@yourdomain.com` containing:
- The estimate summary (line items + total)
- The Stripe payment link
- Business contact info + call-to-action

**The agent does NOT send this email automatically.** It shows the full draft to the
owner in Telegram and asks: "Here's the draft email to [customer]. Want me to send it?"
The owner must explicitly say "send" / "yes" before the agent sends via himalaya.

If the owner says "edit" → agent revises and shows again.
If the owner says "no" → agent does not send, logs the decision in CRM.

To send after approval:
```bash
cat << 'EOF' | himalaya template send
From: owner@yourdomain.com
To: customer@example.com
Subject: Your [BUSINESS_NAME] Estimate

[Email body with estimate + payment link]
EOF
```

To save as draft in the owner's Drafts folder (for the owner to review/edit/send):
```bash
cat << 'EOF' | himalaya message save --folder Drafts
From: owner@yourdomain.com
To: customer@example.com
Subject: Your [BUSINESS_NAME] Estimate

[Email body with estimate + payment link]
EOF
```

Both paths keep the owner in control. Drafts live in the Drafts folder and sync
to the owner's desktop email client.

**For email thread replies** (when replying to an existing conversation, e.g. a
referral email): use `himalaya template reply <message_id>` to generate a
reply template with proper `In-Reply-To` and `References` headers, then pipe the
edited template through `himalaya message save --folder Drafts` (to save as draft)
or `himalaya template send` (to send after owner approval). Do NOT compose a fresh
email for a thread reply — it breaks the threading headers and the customer won't
see it as part of the conversation.

### 8. Update CRM + set follow-up
- `estimates.status = sent`, store the Stripe link / invoice id.
- Create a follow-up reminder (todo or cron) for 3 days out if unpaid.

### 9. Track to paid
- Poll Stripe payment status (or receive a webhook if configured).
- On `paid`: notify owners in Telegram ("✅ Jane Doe paid $3,300"), set
  `estimates.status = paid` and `customers.lead_status = won`.
- If QuickBooks is wired: record the payment against the QBO invoice. If not, the Stripe
  record is the source of truth — fine for now.

## Current state (what runs TODAY)
- Intake: Telegram paste OR `himalaya` inbox read (GoDaddy IMAP — wired and verified).
- Price: estimator-engine (no creds needed, rate tables in skill config).
- Log: crm-lite (SQLite, no creds needed).
- Charge: Stripe payment link (test mode key set).
- Draft email: himalaya IMAP/SMTP (GoDaddy — wired and verified). DRAFT ONLY — owner
  approves before send. Use `himalaya message save --folder Drafts` to save drafts (NOT
  `template save` — that command does not exist). Use `himalaya template reply <msg_id>` for
  thread replies to preserve In-Reply-To headers.
- Track: agent checks Stripe status on request.
QuickBooks is not wired (post-hackathon P1). The Stripe record is the source of truth.

## Owner-in-the-loop rules (important)
- Always summarize a lead before pricing, and always show an estimate before sending.
- Never create a Stripe charge, send an email, or mark anything paid without explicit
  owner approval in the chat. The agent proposes; the human commits.
- Keep Hermes command approvals ON. For a business that spends real money, annoying-but-safe
  beats fast-but-loose.

## Demo script

1. Owner pastes a referral lead into Telegram.
2. Agent summarizes it and asks to draft an estimate.
3. Agent prices it with estimator-engine, logs to crm-lite, shows the estimate.
4. Owner taps "yes."
5. Agent creates a Stripe (test mode) payment link and returns it.
6. On camera, pay with test card `4242 4242 4242 4242`.
7. Agent detects `paid`, posts "✅ paid" in Telegram, updates the CRM.

## Pitfalls
- Stripe amounts are in **cents**. $3,300 = 330000, not 3300.
- Use Stripe **test mode** (`sk_test_…`) for the demo; test cards only work in test mode.
- Match estimate totals to the estimator-engine output exactly so the charge equals the quote.
- Don't claim QuickBooks is live if it isn't wired — present it as roadmap.
- Severity add-on amounts vary by sqft tier — pull the exact figure from the estimator rate card.
- **Email is GoDaddy IMAP/SMTP via himalaya, NOT Microsoft Graph.** Do not use `outlook-graph`
  skill for GoDaddy-hosted email — it's kept as a separate skill for other businesses that use real M365.
- **Never auto-send customer emails.** Always draft, show the owner in Telegram, get explicit
  "send" approval, then send via himalaya.
- **Region classification must match across all locations:** `estimator-engine/SKILL.md`
  Location Tiers → `base44-site-spec` estimator HTML → Base44 site estimator widget. If you update
  one, update all three. Canonical source is `estimator-engine`.
- **Link CLI approval holds expire in ~6 minutes.** When filming + approving real-money
  flows, set up the camera first, then trigger the spend request. Don't race the timer.
- **One-time virtual cards don't work for recurring subscriptions.** The Link CLI issues
  one-time-use cards; the first charge works but rebilling will fail. Accepted for demo;
  handle recurring billing properly post-hackathon.