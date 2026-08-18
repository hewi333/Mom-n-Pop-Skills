---
name: small-business-ai-transformation
description: "Methodology for auditing a real non-technical small service business, understanding its operations, and designing an AI agent system (lead generation, qualification, estimation, booking, billing, reporting) that the owners interact with entirely by text message."
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [methodology, small-business, ai-transformation, service-business, agent-employee]
    related_skills: [lead-to-payment, construction-agent, estimator-engine, crm-lite, stripe-payments, agent-cheatsheet-builder, financial-analysis]
---

# Small Business AI Transformation

## When to Use
- User wants to help a real small service business with AI (family business, friend's business, etc.)
- Owners are non-technical — phone-driven, no CRM, no dashboards
- Goal: build an AI "front-office employee" that finds leads, qualifies them, estimates jobs, books, bills, and reports
- Also applies when a hackathon concept needs a real-world customer story (not AI-for-AI-people)

## Core Principle: The Agent is an Employee, Not a Tool

The framing matters for both the business owners AND for hackathon judges. A tool requires someone to operate it. An employee works 24/7 and reports by text. The owners don't log into anything. They text. The agent handles the rest.

**The demo moment that wins:** "My 62-year-old mom texts an AI agent to run her business. She doesn't know what an API is."

---

## Methodology: 6 Steps

### Step 1: Website Audit (Browser Tools)

Navigate the full site systematically: Home → Services → Testimonials → FAQ → Blog → Contact. For each page, note:

- **Broken pages** (404s, dead links) — common in old WordPress sites built by contractors
- **Stale content** (blog last updated >1 year ago, copyright date)
- **Missing features** (no online estimator, no chat, no booking, no online payment)
- **Mobile experience** (does it render on phone?)
- **SEO gaps** (no geo-targeted content for service areas, no fresh content)
- **Contact form** (does it actually work? does it have reCAPTCHA? what fields does it collect?)

Record findings in the North Star wiki page (Step 5).

### Step 2: Business Model Discovery (Ask the User OR Analyze Their Data)

**Option A — Ask the user** (when no financial data is available):

Ask these questions to the user (who talks to the business owners). Get rough numbers — precision isn't needed for concept development:

1. **Who runs it?** Owners, roles, who does what (ops vs marketing vs field)
2. **Volume & pricing** — Jobs per month, average job cost, pricing model (sqft? flat rate? tiers?)
3. **Lead sources** — Where do customers come from today? Rough percentage split (realtors, Google, referrals, insurance, etc.)
4. **Revenue channel risk** — Is 80% of revenue from one source? What happens when that source slows?
5. **Customer flow** — Step by step: how does someone go from "interested" to "job completed and paid"?
6. **What systems exist?** CRM? Calendar? Email list? QuickBooks? Stripe? Or is it all phone + memory?
7. **Tech maturity** — Would the owners text a bot? Would they read a weekly SMS summary? What's their comfort level?
8. **Existing contacts** — Do they have a list of past clients, referral partners (realtors, insurance adjusters) that's dormant?

**Option B — Quantitative financial analysis** (when the user provides an actual data export):

If the user can get a QuickBooks, bank, or Stripe export from the business, run a full financial analysis BEFORE the qualitative discovery. This replaces rough guesses with hard numbers and surfaces concrete cost-cutting opportunities. The findings directly inform agent design (minimum job size enforcement, travel surcharge calculation, pricing model validation, marketing timing).

Analysis framework:
1. Parse the export, separate estimates from actual transactions, filter internal transfers from real expenses
2. Revenue analysis (invoiced vs collected, top customers, concentration risk, seasonality)
3. Expense breakdown by category (flag uncategorized, flag bank fees >3% of revenue)
4. P&L and cumulative loss (has the business ever been profitable?)
5. Travel cost attribution per job (match fuel/meals within ±2 days of invoices — flag jobs where travel >20% of revenue)
6. Anomaly detection (largest expenses, recurring charges, miscategorized buckets)
7. Generate 5-7 charts optimized for Telegram/mobile delivery
8. Deliver: charts as images + full text report + concise written summary with actionable recommendations

See `references/quickbooks-financial-analysis.md` for the full methodology: CSV parsing patterns, transaction type taxonomy, expense filtering code, travel attribution technique, chart specs, and common findings patterns in service businesses.

**Key insight:** Non-technical owners need interfaces that work via text message (SMS or Telegram). No dashboards. No logins. The agent sends, they read.

### Step 3: Agent System Design

Map the business operations to a 6-stage agent loop:

```
Find Leads → Capture & Qualify → Estimate → Book → Bill → Report
    ↑                                                        |
    └────────────── Weekly Summary to Owners ←───────────────┘
```

**Stage 1 — Find Leads:**
- Scrape listing sites (Zillow, MLS) for properties that signal "needs work": vacant, price drops, as-is, smoke damage, estate sales, foreclosures
- Draft personalized outreach to listing agents
- Import dormant contact lists → systematic re-engagement campaign

**Stage 2 — Capture & Qualify:**
- Website chat agent → after-hours visitors don't bounce
- Qualify: service type, square footage, location, insurance vs private, urgency
- Text owners immediately with qualified lead info

**Stage 3 — Estimate:**
- Auto-calculate from sqft × rate + modifiers (ceiling height, severity, travel distance, add-ons)
- Give a range (order of magnitude), not a binding quote
- Send formatted estimate for signature

**Stage 4 — Book:**
- Check shared calendar availability
- Schedule job → confirm with customer
- Send field tech the job details

**Stage 5 — Bill (Stripe):**
- Stripe invoice or Payment Link for deposit
- Final invoice after completion
- This is the "agent earns real money" moment — real invoice, real business

**Stage 6 — Report:**
- Weekly cron job: text summary to owners
- Leads contacted, responses, estimates sent, jobs booked, revenue collected
- Pipeline status: what's hot, what's stalled
- Owners read it on their phone. That's it.

### Step 4: Stakeholder & Sponsor Mapping (If Applicable)

If you're building this for a demo, pilot, or hackathon, map each agent stage to the stakeholder requirements that matter most:

| Stakeholder | How to Hit It |
|---|---|
| **Agent platform** | The agent IS the platform — cron, skills, subagents, text delivery. This is the commercial proof point. |
| **Payments** | Real invoicing for real jobs. The "agent bills a customer" moment is a real invoice, not a test transaction. |
| **Compute** | Agent processes many leads cost-effectively. Keep cost-per-lead low enough that the economics work. |

**The story that lands:** "I gave a real small business an AI employee. It found real leads, sent estimates, booked a $2,400 job, and collected the deposit. The owner saw it all in a text message."

A real business with a non-technical owner is the differentiator — proof that AI helps normal people, not just AI developers.

### Step 5: Create the North Star Wiki Page

Write a structured project page to the Obsidian vault at `projects/<business-name>/index.md`. This is the cross-session anchor — the user can pull it up in any future session.

**Required sections:**
1. **North Star** — one-sentence vision at the top (blockquote)
2. **Business Profile** — table with owners, service area, avg job, lead sources, systems, website URL
3. **Current Flow** — step-by-step how jobs work today
4. **Pain Points** — bullet list of specific problems
5. **The Concept** — the agent loop diagram + description per stage
6. **Hackathon Mapping** — sponsor table (if applicable)
7. **Architecture & Tech Stack** — infrastructure table, agent skills table, owner interface
8. **Pricing Model** — table with rates, modifiers, TBDs
9. **Implementation Plan** — phased with checkboxes (hackathon sprint + post-hackathon phases)
10. **Prerequisites Checklist** — what the user needs to get from the business owners
11. **Success Metrics** — hackathon, business (90-day), long-term
12. **Session Tracker** — table with date, what was done, next steps
13. **Related Links** — wikilinks + external URLs

**Update the session tracker** at the end of each session so the user can pick up where they left off.

### Step 6: Infrastructure Setup

- **Separate VPS + Hermes instance** for the business — NOT on the user's personal instance
- **Stripe account** — new, test mode for hackathon, real for production
- **Twilio or Telegram** — for SMS/Telegram notifications to owners
- **Shared Google Calendar** — for scheduling
- **Airtable or Google Sheets** — lightweight CRM/pipeline tracker
- **Domain access** — get registrar login from owners to rebuild website
- **Email integration** — connect the owner's mailbox so the agent can read inbox, draft replies, and send approved emails. For Google Workspace accounts, use the Gmail API with OAuth2. For Microsoft 365 / Outlook.com accounts, use the `outlook-graph` skill (Microsoft Graph API, NOT IMAP — Microsoft blocks basic auth IMAP). Device code flow for headless server auth. Dual-approval pattern: drafts save to the email provider's native Drafts folder → owner approves via Telegram or directly in the email client. See the `outlook-graph` skill for M365 setup, or `construction-agent` skill's `references/google-workspace-setup.md` for Google Workspace setup.

---

## Pitfalls

1. **Don't build dashboards for non-technical owners.** They won't log in. Everything must work via text message.
2. **Don't assume the website works.** Old WordPress sites built by contractors frequently have 404'd pages and stale content. Verify every nav link.
3. **Don't skip the pricing formula.** The estimator tool is the "wow" moment for owners. Get exact rates, modifiers, and travel surcharges before building.
4. **Don't put the business agent on the user's personal Hermes instance.** Separate VPS. The business needs its own instance that the user monitors remotely.
5. **Don't forget the dormant contact list.** Most small service businesses have thousands of past contacts in phones/heads that have never been digitized. This is the fastest path to leads.
6. **Don't over-engineer the CRM.** Start with Airtable or Google Sheets. Not Salesforce.
7. **Don't get owner names wrong — and don't auto-correct them either.** Check spelling carefully at the start. A misspelled name in the wiki page propagates across sessions and into code. If the user corrects a name, fix it everywhere immediately — wiki, reference files, code, GitHub repo. This is a first-class error, not a typo. **Critically:** if a name is already documented, do NOT "fix" it to a more common spelling (e.g., the owner → the owner) based on your own assumption — only change it when the user explicitly tells you to. Auto-correcting a correct name to a wrong one is worse than the original typo because it compounds across every file and forces the user to correct you multiple times.

8. **Don't build for the echo chamber.** If the hackathon concept only serves AI developers, it won't stand out. A real business with a non-technical owner is the differentiator.
9. **Don't use IMAP for Microsoft 365 email.** Microsoft 365 blocks basic auth IMAP. Use the `outlook-graph` skill (Microsoft Graph API + OAuth2 device code flow) instead. This works on headless servers (no browser redirect needed). The agent reads inbox, drafts replies to the native Drafts folder, and the owner approves via Telegram or directly in Outlook — dual path, no lock-in. For Google Workspace, use the Gmail API (see `construction-agent` skill's `references/google-workspace-setup.md`).
10. **Don't auto-send emails without owner approval.** Email is business communication, not a notification. Drafts go to the owner's Drafts folder; the agent never sends without explicit approval (via Telegram or Outlook). This is critical for trust — the owner must see every email before it goes out.

11. **Don't over-engineer for non-technical end-users.** When the agent is for a non-technical end-user (business owner, family member), don't add Tailscale, tmux, or full tool access. The end-user interacts via Telegram only — they never SSH in. Tailscale and tmux are builder tools. Restrict the Telegram platform toolset to business-workflow tools only (file, vision, web, memory, skills, todo, clarify). No terminal, no code_execution, no cronjob, no delegation, no browser. Business workflows (briefings, email polling, pipelines) run via cron on the backend and deliver results to Telegram — the end-user doesn't trigger or manage them.

12. **Two interfaces, two roles.** SSH is the builder channel (you — for updates, config, debugging). Telegram is the end-user channel (the business owner — for business workflows only). Design the deployment with this separation from the start. Don't expose admin capabilities (updates, restarts, config editing) through the Telegram gateway just because you can — it's bad practice and a security risk.

---

## Generalization

This methodology is designed to be a **template**. The same 6-stage agent loop applies to:
- **Plumbing** — lead gen from home inspection reports, emergency after-hours capture, sqft-based or issue-based estimation
- **AC repair** — seasonal outreach (pre-summer checkups), service tiers, recurring maintenance contracts
- **Lawn care** — recurring billing (unlike one-shot services), neighborhood-based lead gen
- **Cleaning services** — sqft-based estimation, realtor relationships
- **Construction** — email→PM pipeline, project tracking, document routing (see `construction-agent` skill)
- **Any field service** — find leads, qualify, estimate, schedule, bill, report

---

## Reference Files

- `references/quickbooks-financial-analysis.md` — Methodology for analyzing QuickBooks/bank financial exports: CSV parsing patterns, transaction type taxonomy, separating real expenses from internal transfers, travel cost attribution per job, chart generation for Telegram delivery, and common findings patterns in small service businesses.

This skill is a methodology guide. The skills in this repo are the concrete implementations of this pattern for specific business types. Use this skill to understand the approach, then use the other skills as reference implementations.

## Related Skills in This Repo

- [`lead-to-payment`](../lead-to-payment/) — the orchestration spine (the 6-stage loop in practice)
- [`construction-agent`](../construction-agent/) — worked example: construction business with email→PM pipeline
- [`estimator-engine`](../estimator-engine/) — the estimation stage
- [`crm-lite`](../crm-lite/) — the capture/qualification stage
- [`stripe-payments`](../stripe-payments/) — the billing stage
- [`agent-cheatsheet-builder`](../agent-cheatsheet-builder/) — the owner onboarding stage
- [`financial-analysis`](../financial-analysis/) — the reporting stage (CSV-based financial analysis)