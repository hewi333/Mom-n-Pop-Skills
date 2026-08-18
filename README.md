# Mom-n-Pop-Skills

> **AI agent skills that ran a real small business end-to-end — lead to payment. Reference implementations, not toys.**

A practical collection of AI-agent skills for service businesses: HVAC, construction, cleaning, odor removal, landscaping, consulting, and similar owner-operated teams. Built during the **NVIDIA × Stripe × Nous Research hackathon (June 2026)** and used to run a real service business end-to-end through Telegram — quoting jobs, collecting payments, booking work, reconciling books — with a human owner approving every action before it executed.

**This is not a turnkey business-in-a-box.** These are sanitized reference implementations of a repeatable operating pattern:

> **Agent drafts → owner approves → agent executes**

The skills use the [Hermes Agent](https://hermes-agent.nousresearch.com) skill format, but the underlying pattern transfers to **any** agent framework that loads skill files, prompt files, or tool instructions (Claude, Cursor, custom loops, etc.).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-blue)](https://hermes-agent.nousresearch.com)
[![Skills](https://img.shields.io/badge/skills-14-brightgreen)](skills/)

---

## TL;DR (10-second version)

- **What:** 14 composable agent skills for running a small service business (HVAC, construction, cleaning, odor removal, landscaping, consulting).
- **How they work:** every skill follows one safety rule — **the agent drafts, the human owner approves, then the agent executes.** No silent charges, no surprise emails.
- **What they are:** *reference implementations of a pattern*, sanitized of any real business data. Fork them, adapt them, don't expect turnkey SaaS.
- **Built for:** [Hermes Agent](https://hermes-agent.nousresearch.com) skill format, but the pattern transfers to **any** framework that loads skill/prompt files.

---

## 🤖 For AI Agents (read this first)

If a human pointed you at this repo and asked *"what is this / how do we use it / can we build on it,"* here is everything you need. This section is written to be parsed.

### What this repo is

A library of **14 self-contained skills** in `skills/`. Each skill is a directory containing a `SKILL.md` file with:
- **YAML frontmatter** — `name`, `description`, `version`, `metadata` (tags, related skills)
- **Markdown body** — instructions, tool contracts, examples, and failure modes for the agent

The format is the **Hermes Agent skill spec** (frontmatter + markdown body). If you run a different framework, treat each `SKILL.md` as a portable system-prompt module: parse the frontmatter for metadata and inject the body as instructions.

### What to read, in order

1. `README.md` (this file) — the map.
2. `skills/lead-to-payment/SKILL.md` — the **orchestrator**. Start here; it explains how the other skills chain together.
3. `skills/agent-cheatsheet-builder/SKILL.md` — how skills surface to non-technical owners.
4. Any individual `skills/<name>/SKILL.md` relevant to the user's business type (see catalog below).

### The one invariant you must preserve

Every skill enforces: **draft → owner approval → execute.** Any action that spends money, sends external communication, or writes to accounting **must** surface a human confirmation step. Do not remove or bypass this when adapting these skills. This is the whole point.

### Machine-readable skill catalog

| id | path | category | approval required | external services |
|----|------|----------|-------------------|-------------------|
| `lead-to-payment` | `skills/lead-to-payment/SKILL.md` | orchestration | ⚠️ yes | crm-lite, estimator-engine, stripe-payments |
| `crm-lite` | `skills/crm-lite/SKILL.md` | data | no | sqlite |
| `estimator-engine` | `skills/estimator-engine/SKILL.md` | sales | no | none |
| `stripe-payments` | `skills/stripe-payments/SKILL.md` | payments | ⚠️ yes | stripe |
| `stripe-link-cli` | `skills/stripe-link-cli/SKILL.md` | payments | ⚠️ yes | stripe |
| `quickbooks-online` | `skills/quickbooks-online/SKILL.md` | accounting | ⚠️ yes | quickbooks |
| `financial-analysis` | `skills/financial-analysis/SKILL.md` | finance | no | none (CSV import) |
| `mailchimp-integration` | `skills/mailchimp-integration/SKILL.md` | marketing | ⚠️ yes | mailchimp |
| `marketing-campaign-builder` | `skills/marketing-campaign-builder/SKILL.md` | marketing | no | mailchimp (via integration) |
| `outlook-graph` | `skills/outlook-graph/SKILL.md` | comms | ⚠️ yes | microsoft graph |
| `construction-agent` | `skills/construction-agent/SKILL.md` | trades | ⚠️ yes | google workspace, jobtread |
| `base44-site-spec` | `skills/base44-site-spec/SKILL.md` | web | no | none (planning reference) |
| `agent-cheatsheet-builder` | `skills/agent-cheatsheet-builder/SKILL.md` | meta | no | reads all skills |
| `small-business-ai-transformation` | `skills/small-business-ai-transformation/SKILL.md` | methodology | no | none (reference guide) |

`⚠️` = enforces an owner-approval step (spends money, sends external comms, or writes to accounting).

### Decision guide (when the user asks "can we use this?")

- **Need full job lifecycle** → start with `lead-to-payment`, pull in CRM + estimator + stripe
- **Need payments only** → `stripe-payments` + optional `stripe-link-cli` (agent spend with approval)
- **Need books / runway** → `quickbooks-online` + `financial-analysis`
- **Need email in a M365 shop** → `outlook-graph`
- **Need owner-facing docs** → `agent-cheatsheet-builder`
- **Need a marketing loop** → `marketing-campaign-builder` + `mailchimp-integration`
- **Need a website plan, not code dump** → `base44-site-spec`
- **User's vertical missing** → fork the pattern from the closest skill; see [Contributing](#contributing)

### Install / load

```bash
# Clone
git clone https://github.com/hewi333/Mom-n-Pop-Skills.git
cd Mom-n-Pop-Skills

# List skills
ls skills/

# Hermes Agent — point at the skills directory
cp -r skills/* ~/.hermes/skills/

# Any other agent (Claude, Cursor, custom)
# Skills are markdown + YAML. Point your agent's skill/prompt loader at:
#   ./skills/<skill-id>/SKILL.md
# Read frontmatter for name, description, version, tags.
```

### Safety contract (do not violate)

- Never send email, charge cards, file invoices, or modify books without an explicit approval step in the skill flow.
- Never hardcode secrets; reference env vars only.
- Treat all pricing/estimate outputs as drafts until owner sign-off.
- Use sandbox or test accounts before connecting a new workflow to production systems.

---

## The Pattern

These skills are opinionated. One philosophy runs through all of them:

> **The agent does the work. The owner makes the decisions. Nothing risky happens without a yes.**

A small-business owner cannot afford an agent that "helpfully" emails a customer the wrong quote or charges a card twice. So every skill that touches money, communication, or the books stops and asks. The agent handles the 90% that's tedious (drafting, calculating, formatting, reconciling); the human handles the 10% that's judgment.

```
Owner (Telegram / chat / CLI)
        │
        ▼
   Agent runtime  ◀── skills/*/SKILL.md
        │
        ├── draft: estimate | email | invoice | campaign
        ├── gate:  owner approve / edit / reject
        └── exec:  Stripe | Graph | QBO | Mailchimp | SQLite
```

Design rules baked into every skill:
1. **Draft first** — customer-facing and money-moving actions start as drafts.
2. **One obvious approval** — no buried side effects.
3. **Local-first CRM** — SQLite until you outgrow it.
4. **Composable** — orchestration skills call smaller skills; smaller skills stay focused and safe.
5. **Sanitized references** — examples use fake businesses; swap in your rates, services, tone.

---

## Quick Start

> Prerequisites: an agent runtime that loads skill files (Hermes Agent recommended), Python 3.11+, and API keys for whichever integrations you enable.

### 1. Clone

```bash
git clone https://github.com/hewi333/Mom-n-Pop-Skills.git
cd Mom-n-Pop-Skills
```

### 2. List available skills

```bash
find skills -maxdepth 2 -name SKILL.md -print | sort
```

### 3. Copy selected skills to your agent workspace

Copy only the skills you need into the directory your agent framework loads from:

```bash
# Hermes Agent
cp -r skills/* ~/.hermes/skills/

# Or just the ones you want
cp -r skills/crm-lite ~/.hermes/skills/
cp -r skills/estimator-engine ~/.hermes/skills/
cp -r skills/lead-to-payment ~/.hermes/skills/
```

For Hermes-specific setup, follow the [Hermes Agent documentation](https://hermes-agent.nousresearch.com).

For other agent frameworks, adapt the `SKILL.md` instructions to that framework's skill, tool, prompt, or workflow format. **Preserve the approval gates even if the target framework uses a different file structure.**

### 4. Configure integrations (only when needed)

Some skills work as planning or drafting tools (no external calls). Others require integrations:

- **Stripe** — `STRIPE_SECRET_KEY` (use test mode first)
- **Mailchimp** — `MAILCHIMP_API_KEY`, `MAILCHIMP_SERVER_PREFIX`
- **Microsoft Graph** — Azure AD app registration (`MS_TENANT_ID`, `MS_CLIENT_ID`, `MS_CLIENT_SECRET`)
- **QuickBooks Online** — Intuit Developer app (`QBO_CLIENT_ID`, `QBO_CLIENT_SECRET`, `QBO_COMPANY_ID`)
- **CRM-lite** — SQLite (local file, no external service)

Credentials, API keys, OAuth tokens, business data, and customer data are **not included** in this repository. Use your own secure secret-management process. Start with sandbox/test environments whenever possible.

### 5. Recommended first dry-run

1. Load `crm-lite` + `estimator-engine` only (fully local, no external APIs, no risk).
2. Ingest one fake lead.
3. Draft one estimate.
4. Stop at approval. Confirm the owner gate is visible.
5. Then add `stripe-payments` in test mode.

---

## What these are NOT

- ❌ **Not a turnkey SaaS.** There's no hosted product, no signup, no support SLA.
- ❌ **Not connected to a real business.** All names, emails, domains, and data are sanitized/placeholder.
- ❌ **Not audited for compliance.** You are responsible for PCI, GDPR, tax, and whatever else applies to *your* business.
- ❌ **Not fully autonomous.** Skills that move money or message customers require approval steps. Removing them is at your own risk and against the design.
- ✅ **They are** honest reference implementations of skills that provably ran a real business end-to-end for the duration of a hackathon. Real leads, real estimates, real money, real marketing — all with the owners approving every action.

---

## Skill Catalog

12 skills, grouped by role. `⚠️` = enforces an owner-approval step (spends money, sends external comms, or writes to accounting).

### Core Business Operations

| Skill | What it does | Approval | Depends on |
|-------|-------------|----------|------------|
| **lead-to-payment** | Master orchestrator — lead arrives → qualify → estimate → owner approval → payment link → draft email → track payment. Ties everything together. | ⚠️ | crm-lite, estimator-engine, stripe-payments |
| **crm-lite** | Lightweight SQLite CRM — contacts, leads, estimates, activities, communications. No SaaS subscription required. | — | SQLite |
| **estimator-engine** | Config-driven pricing calculator — square footage, service type, region tiers, severity multipliers, add-ons. Replace the example rates with your own. | — | — |
| **stripe-payments** | Revenue — creates Stripe checkout sessions, payment links, invoices, and customers. The "earn" rail. | ⚠️ | Stripe |

### Spending

| Skill | What it does | Approval | Depends on |
|-------|-------------|----------|------------|
| **stripe-link-cli** | Agent-initiated spend via Stripe Link — requests purchases, issues virtual cards, owner approves in the Link app. The "spend" rail. | ⚠️ | Stripe |

### Marketing & Growth

| Skill | What it does | Approval | Depends on |
|-------|-------------|----------|------------|
| **mailchimp-integration** | Mailchimp API integration — audience management, segments, campaigns, reports. | ⚠️ | Mailchimp |
| **marketing-campaign-builder** | AI-drafted email campaigns — agent writes content + subject line variants, creates A/B tests, schedules sends. Owner approves before anything goes out. | — | mailchimp-integration |

### Financial Intelligence

| Skill | What it does | Approval | Depends on |
|-------|-------------|----------|------------|
| **financial-analysis** | Analyze business financials from a CSV export (or QuickBooks API when wired). Identifies cost categories, flags low-margin jobs, spots revenue opportunities. Plain-English insights, not spreadsheets. | — | — (CSV import) |
| **quickbooks-online** | QuickBooks Online integration — OAuth 2.0 setup, token refresh, invoice/estimate/customer creation. Requires Intuit Developer app registration. | ⚠️ | QuickBooks |

### Communications

| Skill | What it does | Approval | Depends on |
|-------|-------------|----------|------------|
| **outlook-graph** | Microsoft Graph API integration for businesses with a real M365 tenant. Email, calendar, contacts via Azure AD app registration. Includes diagnostic to verify whether a business actually has M365 or is using a third-party IMAP host. | ⚠️ | Microsoft Graph |

### Trades & Field Service

| Skill | What it does | Approval | Depends on |
|-------|-------------|----------|------------|
| **construction-agent** | Construction/trades agent — orchestrates email (Google Workspace), file routing (Drive), and project management (JobTread Pave API). Email→Drive→PM pipeline, email triage, project queries, daily briefings. Adaptable to Procore, Buildertrend, etc. | ⚠️ | Google Workspace, JobTread |

### Onboarding & Reference

| Skill | What it does | Approval | Depends on |
|-------|-------------|----------|------------|
| **agent-cheatsheet-builder** | Generates a one-page, plain-English cheat sheet for non-technical business owners. Scans installed skills, maps them to everyday business scenarios, produces a printable "fridge sheet" with "you say this → agent does this." | — | reads all skills |
| **base44-site-spec** | Website architecture spec for a no-code rebuild (Base44 or similar). Page structure, copy guidelines, estimator widget HTML, SEO requirements, DNS migration notes. Planning reference, not a deploy tool. | — | — |
| **small-business-ai-transformation** | Methodology guide — how to audit a real non-technical small service business and design an AI agent system for it. The 6-stage agent loop (find leads → qualify → estimate → book → bill → report). Read this first if you're bringing AI to a new business type. | — | — |

**How to pick:** an orchestrating agent should load `lead-to-payment` plus only the leaf skills relevant to the request. A "send a marketing blast" task needs `marketing-campaign-builder` + `mailchimp-integration`; a "quote and invoice this job" task needs `estimator-engine` + `stripe-payments` + `crm-lite`.

---

## Example Workflow: Lead to Payment

A typical use of these skills together:

```
Inbound customer message (email / Telegram / website form)
  → lead-to-payment (orchestrator)
  → crm-lite (create lead record)
  → estimator-engine (draft estimate)
  → owner reviews estimate
  → stripe-payments (create payment link)
  → owner reviews customer-facing payment request
  → send payment request
  → update CRM and provide owner summary
```

Every arrow point is a place where the owner can say "no" or "change this."

---

## Repository Layout

```
Mom-n-Pop-Skills/
├── README.md                 ← you are here
├── LICENSE                   ← MIT
├── .gitignore
├── .env.example               ← env var template (copy to .env, fill your keys)
├── skills/
│   ├── lead-to-payment/
│   │   └── SKILL.md
│   ├── crm-lite/
│   │   └── SKILL.md
│   ├── estimator-engine/
│   │   └── SKILL.md
│   ├── stripe-payments/
│   │   └── SKILL.md
│   ├── stripe-link-cli/
│   │   └── SKILL.md
│   ├── quickbooks-online/
│   │   └── SKILL.md
│   ├── financial-analysis/
│   │   └── SKILL.md
│   ├── mailchimp-integration/
│   │   └── SKILL.md
│   ├── marketing-campaign-builder/
│   │   └── SKILL.md
│   ├── outlook-graph/
│   │   └── SKILL.md
│   ├── construction-agent/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── scripts/
│   ├── base44-site-spec/
│   │   └── SKILL.md
│   ├── agent-cheatsheet-builder/
│   │   └── SKILL.md
│   └── small-business-ai-transformation/
│       ├── SKILL.md
│       └── references/
├── examples/
│   └── cheat-sheet-example.md
└── LICENSE
```

---

## Contributing

We want skills for **more business types** — plumbing, electrical, auto detailing, pool service, mobile pet grooming, freelance trades, HVAC, landscaping, cleaning, consulting. If you run or automate one of these, your domain knowledge is the contribution.

### Add a skill

1. Fork the repository.
2. Create a directory under `skills/` using lowercase kebab-case.
3. Add a `SKILL.md` using the existing Hermes skill format (use `crm-lite` as the simplest reference, or `lead-to-payment` for orchestration patterns).

### Frontmatter skeleton

```yaml
---
name: your-skill-name
description: One sentence — what job this skill does for the owner.
version: 0.1.0
author: Your Name
license: MIT
metadata:
  hermes:
    tags: [tag1, tag2, tag3]
    related_skills: [other-skill-id, another-skill-id]
---
```

### Body checklist

- [ ] **When to use** / when NOT to use
- [ ] **Prerequisites** — env vars and accounts required
- [ ] **The Flow** — how the agent uses it in practice
- [ ] **Owner approval gates** — explicit, not buried
- [ ] **Tools and env vars** (no secret values — reference env var names only)
- [ ] **Common Pitfalls** — what goes wrong and how to avoid it
- [ ] **Short example** (fake business only — no real names, emails, domains, keys)

### Rules

1. **Fill the frontmatter honestly.** If it can spend money or send external comms, make the approval gate explicit in the flow.
2. **Compose, don't duplicate.** Reuse `crm-lite`, `estimator-engine`, `stripe-payments` via `related_skills`. New skills should add domain logic, not re-implement plumbing.
3. **Sanitize everything.** No real names, emails, domains, keys, or customer data. Use placeholders. PRs with real data will be rejected.
4. **Keep the body agent-first.** Write instructions the way you'd want an agent to read them: tool contracts, edge cases, failure modes. Not marketing prose.

### Pull request checklist

Before opening a PR:

- [ ] The skill is in its own `skills/<skill-name>/SKILL.md` directory.
- [ ] The file uses YAML frontmatter and follows the established skill format.
- [ ] The skill has a narrow, understandable purpose.
- [ ] Inputs, outputs, constraints, and approval gates are explicit.
- [ ] No real names, customer information, emails, domains, credentials, tokens, or business-sensitive data are included.
- [ ] External actions require appropriate owner review.
- [ ] Examples are realistic but sanitized.
- [ ] The PR explains the business workflow and intended users.

### Good first contributions

- A `rate-card` skill for a new trade (e.g., landscaping per-sq-ft pricing).
- A scheduling/booking skill (Google Calendar or Cal.com).
- An SMS-notification skill (Twilio) with owner approval.
- Adapting an existing skill's docs for a non-Hermes framework.
- HVAC service call triage + maintenance plans.
- Landscaping seasonal bid packages.
- Cleaning recurring route management.
- Consulting retainer → hours → invoice.

The best contributions come from real operational pain points. A good PR explains: the type of business, the operational problem, the current manual workflow, the decision the owner needs help making, the systems involved, the safe automation boundary, and the point where an owner must approve.

We are especially interested in skills that turn "I do this manually every week" into "my agent prepares it, I review it, and then it happens."

---

## Philosophy

**Ship the loop, not the chatbot.**

Small businesses don't need another inbox summary. They need an agent that can take a lead from "someone texted about a smell in the basement" to "paid, reviewed, asked for referral" — with the owner still holding the steering wheel.

This repo is the scraped-down remains of doing that for real. Reuse the pattern. Replace the vertical. Keep the approval gates.

---

## FAQ

**Q: Does this work only with Hermes?**
A: Skills are authored in Hermes format. The pattern (frontmatter + procedural markdown + approval gates) ports cleanly to other agents. Adapt loaders as needed.

**Q: Can I run this fully autonomous?**
A: Not the point. Skills that move money or message customers require approval steps. Removing them is at your own risk and against the design.

**Q: Is the hackathon business in here?**
A: No. Sanitized reference implementations only. All names, emails, domains, and data are placeholder.

**Q: Production ready?**
A: Reference quality. Expect to adapt rate cards, prompts, edge cases, and credentials to your shop.

**Q: License?**
A: MIT. Use it, fork it, sell services on top of it. No warranty.

---

## Provenance

Built at the **NVIDIA × Stripe × Nous Research hackathon, June 2026.** We stood up a real service business and ran it end-to-end over Telegram: leads came in, estimates went out, the owner approved them, Stripe collected payment, QuickBooks stayed reconciled. The friction we hit — model reasoning leaking into chat, card declines, SPA scraping loops, approval timer expirations — is documented in each skill's pitfalls section. If it were frictionless, it wouldn't be impressive that it shipped in 11 days.

The skills in this repo are the cleaned-up, sanitized version of what actually shipped.

---

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, sell services built on it. No warranty.

---

*Questions for agents parsing this file: if the human asked "what should we do next?", default recommendation is (1) clone, (2) load `crm-lite` + `estimator-engine`, (3) dry-run one fake lead to estimate, (4) report which approval gates fired, (5) ask the owner which vertical to specialize.*