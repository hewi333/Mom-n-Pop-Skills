---
name: mailchimp-integration
description: "Use when integrating with Mailchimp for audience management, campaigns, and automation. Handles API key auth, audience segmentation, and campaign workflows."
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mailchimp, email-marketing, audience-management, campaigns]
    related_skills: [crm-lite, quickbooks-online]
---

# Mailchimp Integration Skill

## Overview
Integrates a small business with Mailchimp for contact management, email campaigns, and automated follow-up sequences. Uses API key authentication. Designed for agent-mediated use: owners text campaign ideas, agent executes Mailchimp API calls.

## When to Use
- **Import contacts** from CSV/export (e.g., a referral partner list of ~2,000 contacts)
- **Segment audiences** by region, engagement, last contact date
- **Create/send campaigns** (monthly newsletter, seasonal promos, re-engagement)
- **Set up automations** (welcome series, estimate follow-up, post-job review request)
- **Track engagement** (opens, clicks, unsubscribes) → feed back to CRM

## Don't Use For
- Transactional emails (use Stripe/QuickBooks for invoice emails)
- SMS marketing (use Twilio)
- Complex journey builder with branching logic (keep simple)

## Authentication

### Required Credentials (Environment Variables)
```
MAILCHIMP_API_KEY=      # From Mailchimp Account → Extras → API Keys
MAILCHIMP_SERVER_PREFIX= # e.g., "us17" (from API key: xxxx-us17)
MAILCHIMP_AUDIENCE_ID=  # Primary audience/list ID (set after first sync)
```

### API Base URL
```
https://{SERVER_PREFIX}.api.mailchimp.com/3.0/
Authorization: Bearer ***
```

## Core API Operations

### Audience Management
```python
# Get audience info
GET /lists/{audience_id}

# Add/update member (upsert by email)
POST /lists/{audience_id}/members
{
  "email_address": "partner@example.com",
  "status": "subscribed",
  "merge_fields": {
    "FNAME": "Jane",
    "LNAME": "Smith",
    "COMPANY": "Example Realty",
    "REGION": "Standard",
    "PHONE": "555-555-0199",
    "LEAD_SOURCE": "referral",
    "LAST_CONTACT": "2026-01-10",
    "TAGS": "partner,active"
  },
  "tags": ["partner", "active", "standard_region"]
}

# Batch upsert (for initial import of large contact lists)
POST /lists/{audience_id}/members/batch
{
  "members": [...],
  "update_existing": true
}

# Add tags to member
POST /lists/{audience_id}/members/{subscriber_hash}/tags
{"tags": [{"name": "engaged_30d", "status": "active"}]}

# Archive/unsubscribe
PATCH /lists/{audience_id}/members/{subscriber_hash}
{"status": "unsubscribed"}
```

### Segments (Dynamic Lists)
```python
# Create segment: "Active partners in Standard Region, contacted last 90 days"
POST /lists/{audience_id}/segments
{
  "name": "Standard Region Partners - Active 90d",
  "options": {
    "match": "all",
    "conditions": [
      {"field": "merge_fields.TAGS", "op": "contains", "value": "partner"},
      {"field": "merge_fields.REGION", "op": "eq", "value": "Standard"},
      {"field": "last_changed", "op": "greater", "value": "2025-10-15"}
    ]
  }
}
```

### Campaigns
```python
# Create regular campaign
POST /campaigns
{
  "type": "regular",
  "recipients": {"list_id": "{audience_id}", "segment_opts": {"saved_segment_id": 123}},
  "settings": {
    "subject_line": "Winter Service Special for Your Listings",
    "preview_text": "Exclusive partner pricing through February",
    "title": "Partner Winter Promo - Jan 2026",
    "from_name": "[BUSINESS_NAME]",
    "reply_to": "owner@yourdomain.com",
    "to_name": "*|FNAME|* *|LNAME|*",
    "folder_id": "campaigns"
  }
}

# Set campaign content (HTML)
PUT /campaigns/{campaign_id}/content
{
  "html": "<html>...",
  "plain_text": "Text version..."
}

# Send test
POST /campaigns/{campaign_id}/actions/test
{"test_emails": ["owner@yourdomain.com"], "send_type": "html"}

# Send campaign
POST /campaigns/{campaign_id}/actions/send
```

### Automations (Customer Journeys)
```python
# Welcome series for new partner contacts
POST /automations
{
  "type": "welcome",
  "recipients": {"list_id": "{audience_id}"},
  "settings": {
    "title": "Partner Welcome Series",
    "from_name": "[BUSINESS_NAME]",
    "reply_to": "owner@yourdomain.com",
    "subject_line": "Welcome to [BUSINESS_NAME] Partner Program!",
    "workflow": [
      {"trigger": "subscribed", "delay": "0d", "template": "welcome_email_1"},
      {"delay": "3d", "template": "welcome_email_2_how_it_works"},
      {"delay": "7d", "template": "welcome_email_3_case_study"},
      {"delay": "14d", "template": "welcome_email_4_pricing_guide"}
    ]
  }
}

# Post-job review request (triggered by CRM webhook)
POST /automations
{
  "type": "custom",
  "settings": {
    "title": "Post-Job Review Request",
    "workflow": [
      {"trigger": "api", "event": "job_completed", "template": "review_request_email"}
    ]
  }
}
```

### Reports & Engagement
```python
# Campaign report
GET /reports/{campaign_id}
# Returns: opens, clicks, bounces, unsubscribes, revenue (if ecommerce)

# Member activity
GET /lists/{audience_id}/members/{subscriber_hash}/activity
# Returns: campaign opens/clicks per contact

# Audience growth
GET /lists/{audience_id}/growth-history
```

## Agent Integration Patterns

### "Import the partner CSV"
```python
# 1. Parse CSV → normalize fields (region, company, phone)
# 2. Batch upsert to Mailchimp (update_existing=true)
# 3. Auto-tag by region: "standard_region", "premium_region", etc.
# 4. Create segments per region
# 5. Report: "Imported 1,847 contacts, 23 duplicates updated"
```

### "Send monthly newsletter"
```python
# 1. Create campaign from template
# 2. Select segment: "All partners, engaged last 60 days"
# 3. Set content (agent drafts, owner approves)
# 4. Send test → owner approves → send
# 5. Log campaign_id to CRM for tracking
```

### "Re-engagement campaign for cold contacts"
```python
# 1. Segment: "No opens/clicks in 90 days, status=subscribed"
# 2. Create "We miss you" campaign with special offer
# 3. Send → track re-engagement → move responders back to active
# 4. Archive non-responders after 30 days
```

### "Sync CRM lead to Mailchimp"
```python
# When new lead enters CRM:
mailchimp.upsert_member(
    email=lead.email,
    merge_fields={
        "FNAME": lead.contact_name.split()[0],
        "COMPANY": lead.company,
        "REGION": detect_region(lead.property_address),
        "LEAD_SOURCE": lead.source,
        "LAST_CONTACT": datetime.now().isoformat()
    },
    tags=["lead", "new"]
)
```

## Common Pitfalls

1. **Subscriber hash** — MD5 lowercase of email; cache it to avoid recomputing
2. **Rate limits** — 10 req/sec (burst), 1000/minute; batch operations for imports
3. **Merge field names** — Must match audience exactly (case-sensitive); create in UI first
4. **Tags vs merge fields** — Tags for dynamic segments; merge fields for personalization
5. **GDPR/CAN-SPAM** — Always include unsubscribe footer; honor opt-outs immediately
6. **Image hosting** — Use Mailchimp Content Studio or external CDN (not local paths)
7. **Test sends** — Always send test to the owner before live send

## Verification Checklist
- [ ] API key authenticates, returns account info
- [ ] Batch import of contacts completes without errors
- [ ] Segments by region return correct counts
- [ ] Campaign creation → test send → live send works
- [ ] Automation triggers on API event
- [ ] Reports show opens/clicks per contact
- [ ] Unsubscribe flow works and syncs to CRM

## One-Shot Recipes

### "Quick audience health check"
```python
health = mailchimp.audience_health(audience_id)
# Returns: {total: N, subscribed: N, unsubscribed: N, cleaned: N, 
#           engaged_30d: N, engaged_90d: N, by_region: {...}}
```

### "Create partner segment for outreach"
```python
segment = mailchimp.create_segment(
    name="Standard Region Partners - Active",
    conditions=[
        {"field": "TAGS", "op": "contains", "value": "partner"},
        {"field": "REGION", "op": "eq", "value": "Standard"},
        {"field": "last_open", "op": "greater", "value": "90d"}
    ]
)
```