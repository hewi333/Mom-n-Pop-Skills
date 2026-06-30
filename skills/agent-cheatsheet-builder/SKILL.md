---
name: agent-cheatsheet-builder
description: "Generate a one-page, plain-English cheat sheet for non-technical business owners using a Hermes agent. Scans installed skills, identifies what's wired vs documented, and produces a printable PDF/doc tailored to the business owner's actual capabilities. Written for 60-somethings who've never used AI."
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [onboarding, documentation, cheat-sheet, non-technical, small-business]
    related_skills: [lead-to-payment, crm-lite, estimator-engine]
---

# Agent Cheat Sheet Builder

## What This Does
Generates a one-page cheat sheet for a non-technical business owner so they know
exactly what their Hermes agent can do, how to ask for things, and what the agent
will never do without their approval. Designed for owners in their 60s who have
never used AI — plain English, large print, no jargon.

## When to Use
- Onboarding a non-technical owner to their agent for the first time
- After wiring a new integration (email, payments, CRM, marketing) — regenerate
- Part of a hackathon demo or handoff package
- Any small business using Hermes that needs a "fridge sheet" for the owner

## How It Works

### Step 1: Scan Installed Skills
```bash
ls ~/.hermes/skills/productivity/ ~/.hermes/skills/email/ ~/.hermes/skills/payments/
```
For each skill, read the SKILL.md frontmatter (name + description) to understand
what the agent can actually do. Categorize each as:
- **Wired** — has env vars set, verified working (check .env + verification checklist)
- **Documented** — skill exists but not wired (checkmarks in verification section)
- **Not applicable** — skill installed but not relevant to this business

### Step 2: Identify the Owner's Real Flows
Map skills to everyday business scenarios the owner recognizes. Examples:
- "When a new lead comes in" → lead-to-payment + email (himalaya)
- "When you need to send a payment link" → stripe-payments
- "When you want to check your contacts" → crm-lite
- "When you want to send a marketing email" → mailchimp-integration

### Step 3: Generate the Cheat Sheet
Use the template below. Fill in the business name, owner names, and real flows
from the scan. The sheet should be:
- **One page** (printable on 8.5x11 or A4)
- **Large font** (14-16pt minimum, headings 18-20pt)
- **Plain English** — no technical terms without explaining them
- **Action-oriented** — "Say this → Agent does this"
- **Honest about limits** — "Agent CANNOT do X" is as important as what it can do

### Step 4: Export
Generate as markdown → convert to PDF using `pandoc` or print directly. Also
save a plain-text version for Telegram delivery.

## Cheat Sheet Template

```markdown
# [BUSINESS NAME] — Your Agent Cheat Sheet

*Keep this by your phone. This is what your agent can do for you.*

---

## How to Talk to Your Agent

Just text it in Telegram — the same way you text anyone else.
No special commands. No apps to install. Just type what you need.

**Examples of what to say:**
- "Check the email for new leads"
- "I have a new lead: Jane Doe, 2400 sqft house in [CITY], cigarette smoke"
- "What's the estimate for a 3000 sqft home in [CITY], light smoke?"
- "Send a payment link to john@example.com for $2,800"
- "Show me my recent leads"
- "Send a marketing email to all realtors about our summer special"

---

## What Your Agent Can Do

### 📬 Read Your Email
**Say:** "Check the email" or "Any new leads in the inbox?"
**Agent does:** Reads your inbox, finds new messages, identifies which ones
are real leads vs junk. Shows you a summary.

### 💰 Create Estimates
**Say:** "New lead: [name], [sqft] [property type] in [city], [odor type]"
**Agent does:** Calculates the real price using your actual rate card.
Shows you the estimate for approval before anything goes out.

### ✅ Get Your Approval
**Agent will always ask you before:**
- Sending an estimate to a customer
- Sending a payment link
- Sending any email on your behalf
- Spending any money

**You just reply "yes" or "approve" in Telegram. That's it.**

### 💳 Send Payment Links
**Say:** "Send a payment link to [customer] for $[amount]"
**Agent does:** Creates a Stripe payment link and shows it to you.
After you approve, it sends the link to the customer.

### 📇 Track Your Leads & Customers
**Say:** "Show me my recent leads" or "What's the status on Jane Doe?"
**Agent does:** Looks up the customer in the CRM, shows you their status,
estimate amount, and whether they've paid.

### 📧 Send Marketing Emails
**Say:** "Send a campaign to all realtors about [topic]"
**Agent does:** Creates a Mailchimp campaign, shows you a draft for approval,
sends a test to you first. You approve → it goes out to your list.

### 🌐 Your Website
**Agent can:** Pay for website tools (with your approval) and help plan
website updates. The agent cannot edit the website directly — that's done
in the Base44 builder by a person.

---

## What Your Agent CANNOT Do

- ❌ It will NOT send anything to a customer without your OK
- ❌ It will NOT spend money without your approval
- ❌ It will NOT make phone calls
- ❌ It will NOT delete or change your email
- ❌ It cannot edit the website directly (no Base44 automation)
- ❌ It cannot access QuickBooks yet (coming later)

---

## If Something Looks Wrong

Just say **"stop"** and the agent will stop what it's doing.
Then call [FAMILY CONTACT] and describe what happened.

The agent is a helper, not a boss. You're always in charge.

---

## Quick Reference

| You say... | Agent does... |
|------------|--------------|
| "Check email" | Reads inbox, summarizes leads |
| "New lead: [details]" | Creates estimate, asks for approval |
| "Send payment link to [email]" | Creates Stripe link, asks for OK |
| "Show recent leads" | Lists leads from CRM with status |
| "Send campaign about [topic]" | Drafts Mailchimp email for approval |
| "stop" | Stops whatever it's doing |

---

*Your agent runs on Telegram. It's available whenever you need it.
No computer required — just your phone.*

*Built with [Hermes Agent](https://hermes-agent.nousresearch.com)*
```

## Customization Rules

1. **Owner names:** Use real first names (e.g., the owner's actual first name) not "the owner"
2. **Business specifics:** Replace [BUSINESS NAME], [sqft], [odor type] with
   examples that match the actual business
3. **Wired vs documented:** Only list capabilities that actually work.
   If QuickBooks isn't wired, don't list it as a capability — list it under
   "Coming Later"
4. **Contact info:** Put the real family contact or IT support person
5. **Tone:** Friendly, direct, respectful. These are smart adults who just
   haven't used AI before. Don't dumb it down — just keep it plain
6. **Length:** One page. If it's too long, cut capabilities that aren't
   wired yet. The sheet should only show what works TODAY.

## Common Pitfalls

- **Don't list unwired features as available.** If it can't do it today, it goes
  under "Coming Later" or gets cut entirely. Trust is built on accurate expectations.
- **Don't use technical terms.** "CRM" is fine if you explain it. "SQLite database"
  is not. "API" is not. "Integration" is borderline — say "connection" instead.
- **Don't overwhelm.** One page, 7-10 capabilities max. If there are more, group
  them into broader categories.
- **Test with the actual owner.** The cheat sheet isn't done until the owner
  can read it and know what to do without asking a question.
- **Update when things change.** When a new integration is wired, regenerate.
  Don't let the sheet go stale — that's worse than not having one.

## Verification Checklist
- [ ] Installed skills scanned
- [ ] Wired vs documented categorization complete
- [ ] Cheat sheet generated from template
- [ ] Only wired capabilities listed as available
- [ ] Owner names and business specifics filled in
- [ ] Contact info included for support
- [ ] Fits on one page when printed
- [ ] Owner can read it and know what to do without asking
```