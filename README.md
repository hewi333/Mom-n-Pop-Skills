# Small Business Agent Skills

A collection of [Hermes Agent](https://hermes-agent.nousresearch.com) skills built for real small business operations — lead intake, estimates, payments, marketing, financial analysis, and owner onboarding. Every skill is owner-gated: the agent drafts and proposes, the human approves, then the agent executes.

Built during the NVIDIA × Stripe × Nous Research hackathon (June 2026). These skills ran a real service business end-to-end through Telegram — the same app the owners already use to text. Real leads, real estimates, real money, real marketing — all with the owners approving every action.

## Why This Exists

Small businesses don't need another dashboard. They need help with the 3+ hours of daily manual work that nobody signed up for — estimating, following up, sending payment links, tracking who paid, and figuring out whether the last job actually made money.

These skills turn an AI agent into a business assistant that works through a chat app. No new software to learn. No computer required. Just text.

## The Pattern

Every skill follows the same philosophy:

1. **Agent drafts** — the agent does the work (estimate, email, campaign, analysis)
2. **Owner approves** — the owner gets a Telegram message, taps "yes" or "no"
3. **Agent executes** — only after approval does anything go out or get charged

This isn't a limitation. It's the product. Owners who've never touched AI will use it every day if they trust it. They trust it because nothing happens without their OK.

## Skills

### Core Business Operations

| Skill | What it does |
|-------|-------------|
| **estimator-engine** | Config-driven pricing calculator — square footage, service type, region tiers, severity multipliers, add-ons. Replace the example rates with your own. |
| **crm-lite** | Lightweight SQLite CRM — contacts, leads, estimates, activities, communications. No SaaS subscription required. |
| **stripe-payments** | Revenue — creates Stripe checkout sessions, payment links, invoices, and customers. The "earn" rail. |
| **lead-to-payment** | Master orchestrator — lead arrives → qualify → estimate → owner approval → payment link → draft email → track payment. Ties everything together. |

### Spending

| Skill | What it does |
|-------|-------------|
| **stripe-link-cli** | Agent-initiated spend via Stripe Link — requests purchases, issues virtual cards, owner approves in the Link app. The "spend" rail. |

### Marketing & Growth

| Skill | What it does |
|-------|-------------|
| **mailchimp-integration** | Mailchimp API integration — audience management, segments, campaigns, reports. Connect your Mailchimp account. |
| **marketing-campaign-builder** | AI-drafted email campaigns — agent writes content + subject line variants, creates A/B tests, schedules sends at optimal times. Owner approves before anything goes out. |

### Financial Intelligence

| Skill | What it does |
|-------|-------------|
| **financial-analysis** | Analyze business financials from a CSV export (or QuickBooks API when wired). Identifies cost categories, flags low-margin jobs, spots revenue opportunities. Delivers plain-English insights, not spreadsheets. |

### Onboarding

| Skill | What it does |
|-------|-------------|
| **agent-cheatsheet-builder** | Generates a one-page, plain-English cheat sheet for non-technical business owners. Scans installed skills, maps them to everyday business scenarios, produces a printable "fridge sheet" with "you say this → agent does this." |

### Reference / Templates

| Skill | What it does |
|-------|-------------|
| **base44-site-spec** | Website architecture spec for a no-code rebuild (Base44 or similar). Page structure, copy guidelines, estimator widget HTML, SEO requirements, DNS migration notes. Not a deploy tool — a planning reference. |
| **outlook-graph** | Microsoft Graph API integration template for businesses with a real M365 tenant. Email, calendar, contacts via Azure AD app registration. Includes diagnostic to verify whether a business actually has M365 or is using a third-party IMAP host. |
| **quickbooks-online** | QuickBooks Online integration — OAuth 2.0 setup, token refresh, invoice/estimate/customer creation. Requires Intuit Developer app registration. |

### Email

The [GoDaddy Workspace Email reference](references/godaddy-workspace-email.md) documents IMAP/SMTP setup for the extremely common small business setup: domain email hosted on GoDaddy, accessed via Outlook desktop as an IMAP client (NOT Microsoft 365). Includes verified server settings, config file template, and password storage pattern.

## Setup

### Prerequisites
- [Hermes Agent](https://hermes-agent.nousresearch.com) installed and running
- A Telegram bot connected (or other chat gateway)
- Environment variables for your integrations (see each skill's Prerequisites section)

### Installation
```bash
# Copy skills to your Hermes skills directory
cp -r skills/* ~/.hermes/skills/productivity/

# Add your credentials to ~/.hermes/.env
# (see each skill's SKILL.md for required env vars)

# Restart your Hermes gateway
```

### Configuration
Each skill has a `SKILL.md` file with:
- **Prerequisites** — what env vars and accounts you need
- **Setup steps** — how to wire it up
- **The Flow** — how the agent uses it in practice
- **Common Pitfalls** — what goes wrong and how to avoid it

Start with `estimator-engine` and `crm-lite` — those are the foundation. Then add `stripe-payments` and `lead-to-payment` for the full earn loop. Add marketing and financial analysis when you're ready.

## Architecture

```
Lead arrives (email / Telegram / website form)
    ↓
Agent qualifies + summarizes
    ↓
Agent runs estimator-engine → produces estimate
    ↓
Owner approves in Telegram
    ↓
Agent creates Stripe payment link (stripe-payments)
    ↓
Agent drafts customer email (himalaya / outlook-graph)
    ↓
Owner approves email → agent sends
    ↓
Customer pays → agent confirms → CRM updated (crm-lite)
    ↓
Agent syncs to Mailchimp for future campaigns (mailchimp-integration)
    ↓
Owner runs financial analysis quarterly (financial-analysis)
```

Every arrow point is a place where the owner can say "no" or "change this."

## Tech Stack
- **Agent framework:** [Hermes Agent](https://hermes-agent.nousresearch.com) by Nous Research
- **Model:** GLM-5.2 via Together AI
- **Payments:** Stripe (revenue) + Stripe Link (agent spend)
- **Email:** Himalaya CLI (IMAP/SMTP) or Microsoft Graph API
- **Marketing:** Mailchimp API
- **Accounting:** QuickBooks Online API (optional) or CSV import
- **CRM:** SQLite (no SaaS needed)
- **Interface:** Telegram (or any chat gateway Hermes supports)

## License

MIT — use these for your business, your clients, your hackathon. Just don't blame us if something breaks.

## Acknowledgments

Built during the NVIDIA × Stripe × Nous Research hackathon, June 2026. Thanks to:
- **Nous Research** — Hermes Agent framework
- **Stripe** — payments infrastructure + Stripe Link for agent-initiated spend
- **NVIDIA** — compute and model infrastructure

These skills were built for a real service business with real owners, real leads, and real money. The friction we hit — model reasoning leaking into chat, card declines, SPA scraping loops, approval timer expiries — is documented in each skill's pitfalls section. If it were frictionless, it wouldn't be impressive that it shipped in 11 days.

## Contributing

Found a bug? Want to add a skill? Open a PR.

If you build a skill for a different business type (HVAC, landscaping, cleaning, consulting), the pattern transfers: encode the expertise in the skill, gate everything behind owner approval, deliver through chat.