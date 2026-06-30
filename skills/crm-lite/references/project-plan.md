# Project Plan — Reference for CRM-Lite

This reference captures the business context, implementation plan, and specific requirements that CRM-Lite must support.

## Business Profile (Example)

- **Company**: [BUSINESS_NAME] — service business
- **Owners**: [OWNER_NAME] (ops/field) & [OWNER_NAME] (marketing/relationships) — non-technical
- **Service Area**: Multiple regions: [CITY] → [CITY] → [CITY] → [CITY]
- **Avg Job**: $2,000–3,000 (priced by sqft)
- **Lead Sources**: ~80% referrals (seasonal turnover), some Google, insurance = unreliable
- **Current Stack**: Microsoft Outlook, QuickBooks invoicing, **no CRM**, no Stripe
- **Website**: yourdomain.com — WordPress, Services page 404, blog dead since 2024
- **Contact List**: ~2,000 contacts in Mailchimp, unused

## Pain Points CRM-Lite Must Address

1. **No lead capture after hours** — visitors bounce, calls go unanswered on jobs
2. **Contact list is dormant** — thousands of contacts, zero systematic outreach
3. **Insurance claims sporadic** — promised work is slow, no tracking/follow-up
4. **Revenue channel risk** — 80% reliant on referrals → market slowdown = business slowdown
5. **Everything is phone-driven** — no digital pipeline, no visibility into lead flow
6. **Owner is not technical** — needs things that work via text, not dashboards

## Core Loop CRM-Lite Must Support

```
Find Leads → Capture & Qualify → Estimate → Book → Bill → Report
     ↑                                                        |
     └────────────── Weekly Summary to Owners ←───────────────┘
```

## Implementation Plan

### Phase 1: Front Door (Days 1-3)
- [ ] Get website access (GoDaddy login from owner)
- [ ] Rebuild website — simple, mobile-first, fast
- [ ] Build square footage estimator (web form → instant range)
- [ ] Fix Services page (currently 404)
- [ ] Mobile-friendly contact form with service type checkboxes

### Phase 2: Agent Employee (Days 4-6)
- [ ] Set up separate VPS + Hermes instance for the business
- [ ] Build lead-qualifier skill (website chat → qualify → text owners)
- [ ] Set up Stripe account (test mode for demo)
- [ ] Build invoicer skill (estimate → Stripe Payment Link)
- [ ] Connect Twilio or Telegram for owner notifications

### Phase 3: Sales Engine (Days 7-8)
- [ ] Build lead-scanner skill (scrape listings for target properties)
- [ ] Build partner-outreach skill (draft personalized emails)
- [ ] Import owner's contact list (from Mailchimp)
- [ ] Set up pipeline tracker (Airtable or Google Sheets)

### Phase 4: Demo & Submit (Days 9-10)
- [ ] Build weekly-report cron job
- [ ] Test full loop: listing → outreach → qualification → estimate → invoice → report
- [ ] Record demo video (2-3 min)
- [ ] Submit to hackathon

## CRM-Lite Specific Requirements from Plan

### Lead Capture & Qualification
- Website form → instant estimator range → capture lead info → enter pipeline
- After-hours chat agent → qualifies visitor → texts owner immediately
- Referral contact import from Mailchimp (~2,000 contacts)

### Pipeline Tracking
- Lead statuses: new → qualified → estimate_sent → scheduled → won/lost
- Track: lead source, property details, sqft, ceiling height, service type, urgency
- Assign to owner, next action dates

### Estimate Management
- Auto-calculates based on sqft × rate + ceiling modifier + add-ons + travel distance
- Premium Region = hotel surcharge + mileage
- Gives a range (order of magnitude) — not a binding quote
- Estimate → Stripe Payment Link for deposit

### Booking & Scheduling
- Checks shared calendar availability
- Schedules job → confirms with customer
- Sends owner the job details

### Billing (Stripe Integration)
- Stripe invoice or payment link for deposit
- Final invoice after job completion
- Real money, real invoice, real business

### Weekly Reporting (Cron)
- Every Monday morning: text summary to the owner(s)
- Leads contacted, responses, estimates sent, jobs booked, revenue collected
- They read it on their phone. That's it.

## Pricing Model (For Estimator Integration)

| Component | Rate | Unit | Notes |
|-----------|------|------|-------|
| Base treatment | $0.50 | /sqft | Example base rate |
| High ceiling (>9ft) | $0.60 | /sqft | Additional chemical volume + setup time |
| Pet fees | TBD | add-on | Configure per your business |
| Travel surcharge | TBD | flat or % | Premium Region (hotel + mileage) |
| Severity tiers | TBD | multiplier | Light vs heavy damage |

**Minimums**: Residential $1,500, Commercial $2,500 (examples — configure per your business)

## Prerequisites / Items Needed

### From Developer
- [ ] GoDaddy/website access — IN PROGRESS
- [ ] Exact pricing formula — IN PROGRESS
- [ ] Owner's contact list — IN PROGRESS (exporting from Mailchimp)
- [ ] Owner's email list — IN PROGRESS (Mailchimp)
- [ ] Confirm Google Business Profile access
- [ ] What are they paying $100-200/mo for on Google?
- [ ] QuickBooks access

### From Owner
- [x] Green light on the concept — CONFIRMED
- [ ] Willingness to text an agent for pipeline/status
- [ ] Shared Google Calendar for scheduling
- [ ] Stripe account setup

### Infrastructure
- [ ] New VPS for business Hermes instance (developer to set up manually)
- [ ] Twilio or Telegram for owner notifications
- [ ] Stripe account
- [ ] Airtable or Google Sheets for pipeline tracking
- [ ] Domain DNS access (GoDaddy)

## VPS Setup Checklist (Manual — ~30 min)
1. Provision VPS — Ubuntu 22.04/24.04 LTS, 2 vCPU, 4GB RAM, 40GB disk
2. SSH Access — Add SSH key, disable password auth, create non-root user
3. Install Hermes — Clone, venv, pip install, `hermes setup`, `hermes doctor`
4. Telegram Gateway — New bot via @BotFather, add token to config, systemd service
5. Tailscale — Install for easy SSH access
6. Business Config — Profile, skills, cron jobs, Stripe keys, owner notification IDs

## Hackathon Context
- **Event**: Hermes Agent Accelerated Business Hackathon (NVIDIA × Stripe × Nous Research)
- **Deadline**: June 30, 2026
- **Theme**: "Agents that can earn, spend, and run real operations at any scale"
- **Story**: "I gave a small business an AI employee. It found 12 referral leads this week, qualified 5, sent estimates, booked a $2,400 job, and collected the deposit via Stripe. The owner saw it all in a text message."