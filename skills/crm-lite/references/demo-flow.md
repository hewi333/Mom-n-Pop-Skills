# Demo Flow — End-to-End Orchestration

> **Note:** This file documents the demo flow for a service business agent.
> The demo has evolved over time — notes below reflect a working state.

## Context
NVIDIA x Stripe x NousResearch hackathon. Deadline: June 30, 2026.
Demo uses the live Telegram gateway on v0.17.0 — tool calling works end-to-end.

## Skill Inventory (7 total, all under productivity/)

| Skill | Role in Demo Flow | Status |
|-------|-------------------|--------|
| crm-lite | Central hub — all leads, customers, estimates, activities logged here | SKILL.md done, DB not initialized |
| estimator-engine | Calculates price from sqft + region + property type + add-ons | SKILL.md done, exact pricing loaded |
| quickbooks-online | Syncs invoices/payments to QBO, not required for demo | SKILL.md + refs + scripts + templates |
| mailchimp-integration | Email campaigns, not required for core demo | SKILL.md only |
| stripe-payments | Payment links and invoices — CRITICAL for hackathon (Stripe sponsor) | SKILL.md only |
| outlook-graph | Sends estimates, payment links via email; reads inbox leads | SKILL.md only |
| base44-deploy | Website rebuild with embedded estimator form | SKILL.md only |

## Demo Flow (Lead -> Cash)

### Step 1: Lead Intake
- Trigger: Email arrives in inbox (or website form submission, or agent says "new lead")
- Skill: outlook-graph (read inbox) OR crm-lite (manual lead creation)
- Agent action: Read email, extract customer name, address, sqft, region, property type
- Agent action: Create lead in CRM (crm-lite INSERT into leads table)
- Agent action: Log activity (crm-lite INSERT into activities, type=lead_created)

### Step 2: Estimate
- Skill: estimator-engine (calculate price from inputs)
- Agent action: Run pricing logic — region tier (Standard vs Premium), property type (Res/Comm/Apt), sqft, add-ons
- Agent action: Create estimate record in CRM (crm-lite INSERT into estimates)
- Agent action: Log activity (type=estimate_sent)

### Step 3: Payment Link
- Skill: stripe-payments (create payment link or checkout session)
- Agent action: Convert estimate amount to cents (e.g. $2,800 = 280000)
- Agent action: Create Stripe customer
- Agent action: Create payment link with metadata (customer_id, sqft, region)
- Agent action: Store payment URL in CRM estimate record

### Step 4: Send Estimate Email
- Skill: outlook-graph (send email with payment link)
- Agent action: Compose HTML email with estimate details and Stripe payment link
- Agent action: Send via Graph API sendMail
- Agent action: Log communication in CRM (crm-lite INSERT into communications)

### Step 5: Payment Confirmation
- Skill: stripe-payments (check payment status)
- Agent action: Poll checkout session or listen for webhook
- Agent action: When paid, update CRM: lead_status -> won, estimate status -> accepted
- Agent action: Log activity (type=payment_received)

### Step 6: Schedule Job
- Skill: outlook-graph (create calendar event)
- Agent action: Create calendar event with customer info, address, service details
- Agent action: Create task in CRM for the owner (type=job_scheduled)

### Step 7: Daily Report (Cron)
- Skills: crm-lite (query stats) + outlook-graph (email report)
- Agent action: Query CRM for new leads, estimates sent, jobs booked, payments received
- Agent action: Email summary to the owner(s)

## "Agent Earns and Spends" Angle (Hackathon Differentiator)

1. Agent creates Stripe payment link for a service
2. Customer pays -> funds land in business Stripe account
3. Agent uses Stripe to pay for its own SaaS subscriptions (Base44, Mailchimp)
4. This demonstrates the agent generating revenue AND spending it autonomously
5. Tie-in: prize money (if won) goes to marketing campaigns + NVIDIA DGX Spark for local inference

## Demo Recording Script (90 seconds)

1. [0-15s] Hook: "Meet the owner of a service business. They serve multiple regions.
   They're in their 60s. They spend 3 hours a day on manual paperwork. No CRM.
   No online payments. A broken website."
2. [15-40s] Problem: Show the owner's inbox — scattered emails, no tracking, manual
   estimates in a spreadsheet
3. [40-70s] Solution: Open `hermes chat` terminal. Type: "New lead from John Smith,
   2500sqft residential in [CITY]." Agent: creates CRM lead, runs estimator ($3,500),
   creates Stripe payment link, sends email via Outlook, schedules calendar event.
   Show each step in terminal output.
4. [70-90s] Impact: "This agent costs under $50/month. It saves the owner 15 hours a
   week. It handles leads, estimates, payments, and scheduling — autonomously. Built
   with Hermes Agent, GLM-5.2 via Together AI, and Stripe."

## Current Status

### DONE ✅
- CRM database initialized and working (SQLite)
- Stripe test key wired in `~/.hermes/.env`, gateway restarted
- EARN beat recorded (lead → estimate → CRM → approval → Stripe payment → paid → CRM updated)
- SPEND beat recorded (agent → $20 Base44 purchase → Link approval → virtual card → paid)
- All gateway-era blockers resolved (v0.14.0 → v0.17.0, GLM-5.2, direct to Together AI)
- Estimator-engine region classification fixed
- Base44 site build prompt written

### IN PROGRESS
- Base44 site being built (staged — no DNS cutover until contact form routing verified)
- Demo video editing (stitching earn + spend + site scroll + story bookends)

### STILL NEEDED (post-hackathon)
- QuickBooks Online wiring (OAuth consent needed)
- Outlook/Microsoft Graph (Azure AD app registration)
- Mailchimp API key (lower lift, can do anytime)
- Website DNS cutover (after contact form verified)
- Local Chromium for browser automation (only if a flow needs agent-driven browser)

### Credential Checklist

| Service | What's Needed | Status |
|---------|--------------|--------|
| Stripe (test mode) | sk_test_ key | ✅ Wired |
| Stripe Link (spend) | Link wallet authed | ✅ Done (real card) |
| Microsoft Graph | Tenant ID, Client ID, Secret | ⏸️ Not wired |
| QuickBooks Online | OAuth2 tokens | ⏸️ Not wired |
| Mailchimp | API key | ⏸️ Not wired |
| Base44 | Account + subscription | ✅ Active ($20/mo paid via agent) |