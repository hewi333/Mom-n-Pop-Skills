---
name: outlook-graph
description: Send and read emails, manage calendar events, and access contacts via Microsoft Graph API for Outlook/M365. Use when emailing customers, scheduling jobs, or managing partner communications.
---

# Outlook Graph Skill

## When to Use
- Sending estimates or invoices to customers via email
- Reading incoming leads or referrals from Outlook inbox
- Scheduling service jobs on calendar
- Looking up contact info for partners or customers
- Sending payment links (from stripe-payments skill) to customers
- Daily report emails to the owner

## ⚠️ Before You Begin: Verify This Is Actually M365

"Uses Outlook" ≠ "Has Microsoft 365." Many small businesses use the Outlook
desktop app as an IMAP client connected to a third-party email host (GoDaddy
Workspace Email, Rackspace, etc.). Before starting the Azure AD setup:

1. Try signing in at **portal.azure.com** with the business email address.
   If it says "account not found," the email is NOT on M365 — stop here.
2. Check where the domain's email is hosted: look at MX records
   (`dig MX domain.com`), or check the domain registrar's email product page
   (e.g., GoDaddy → My Products → Email section).
3. If the email is hosted on **GoDaddy Workspace Email** or another IMAP
   provider, use the `himalaya` skill (IMAP/SMTP) instead of this skill.
   Common GoDaddy IMAP settings: `imap.secureserver.net:993` TLS,
   `smtpout.secureserver.net:465` TLS.
4. GoDaddy-**resold** M365 also exists — the mailbox IS on Microsoft's servers
   but managed through GoDaddy's portal, not Azure directly. In that case,
   this skill may work but app registration must be done through the GoDaddy
   M365 admin portal, not portal.azure.com directly.

This skill only applies to businesses with a real Microsoft 365 / Azure AD
tenant where `portal.azure.com` accepts the business email login.

## Prerequisites
- Microsoft 365 tenant with Outlook (verified per the check above)
- Azure AD app registration (Application (client) ID, client secret)
- API permissions: Mail.ReadWrite, Mail.Send, Calendars.ReadWrite, Contacts.Read
- Environment variables: `MS_TENANT_ID`, `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MS_USER_EMAIL`

## Setup

### 1. Register Azure AD App
1. Go to Azure Portal (portal.azure.com) > Azure Active Directory > App Registrations
2. Click "New registration"
3. Name: "[BUSINESS_NAME] Agent"
4. Supported account types: "Accounts in this organizational directory only"
5. Redirect URI: leave blank (using client credentials flow)
6. Click Register

### 2. Get Client ID and Secret
1. Copy "Application (client) ID" -> this is `MS_CLIENT_ID`
2. Certificates & Secrets > New client secret
3. Copy the secret VALUE (not ID) -> this is `MS_CLIENT_SECRET`

### 3. Get Tenant ID
1. Overview page > Copy "Directory (tenant) ID" -> this is `MS_TENANT_ID`

### 4. Set API Permissions
1. API Permissions > Add a permission > Microsoft Graph > Application permissions
2. Add: Mail.ReadWrite, Mail.Send, Calendars.ReadWrite, Contacts.Read
3. Click "Grant admin consent" for each

### 5. Store Credentials
Add to `~/.hermes/.env`:
```
MS_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MS_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MS_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MS_USER_EMAIL=owner@yourdomain.com
```

## API Reference

Base URL: `https://graph.microsoft.com/v1.0`

### Get Access Token
```bash
TOKEN=$(curl -s https://login.microsoftonline.com/$MS_TENANT_ID/oauth2/v2.0/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=$MS_CLIENT_ID" \
  -d "client_secret=$MS_CLIENT_SECRET" \
  -d "scope=https://graph.microsoft.com/.default" \
  -d "grant_type=client_credentials" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### Send Email
```bash
curl -s "https://graph.microsoft.com/v1.0/users/$MS_USER_EMAIL/sendMail" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "subject": "Your [BUSINESS_NAME] Estimate",
      "body": {
        "contentType": "HTML",
        "content": "<h2>[BUSINESS_NAME]</h2><p>Dear John,</p><p>Your estimate for service is <strong>$2,800</strong>.</p><p>Payment link: <a href=\"https://buy.stripe.com/...\">Pay Now</a></p><p>Questions? Call [PHONE]</p>"
      },
      "toRecipients": [
        {"emailAddress": {"address": "customer@example.com"}}
      ]
    },
    "saveToSentItems": true
  }'
```

### Read Inbox (Recent Emails)
```bash
curl -s "https://graph.microsoft.com/v1.0/users/$MS_USER_EMAIL/messages?\$top=10&\$select=subject,from,bodyPreview,receivedDateTime" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### Search Inbox for Leads
```bash
curl -s "https://graph.microsoft.com/v1.0/users/$MS_USER_EMAIL/messages?\$search=\"service+estimate\"&\$top=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### Reply to Email
```bash
curl -s "https://graph.microsoft.com/v1.0/users/$MS_USER_EMAIL/messages/$MESSAGE_ID/reply" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comment":"Thank you for your interest! I can come out Tuesday at 10am for a free estimate. Does that work?"}'
```

### Create Calendar Event (Schedule a Job)
```bash
curl -s "https://graph.microsoft.com/v1.0/users/$MS_USER_EMAIL/calendar/events" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "[BUSINESS_NAME] - Smith Residence - Service",
    "body": {"contentType": "HTML", "content": "<p>Customer: John Smith</p><p>Address: 123 Main St, [CITY], [STATE]</p><p>Service: Residential service 2000sqft</p><p>Estimate: $2,800</p>"},
    "start": {"dateTime": "2026-06-28T09:00:00", "timeZone": "Eastern Standard Time"},
    "end": {"dateTime": "2026-06-28T13:00:00", "timeZone": "Eastern Standard Time"},
    "location": {"displayName": "123 Main St, [CITY], [STATE] [ZIP]"},
    "attendees": [{"emailAddress": {"address": "customer@example.com", "name": "John Smith"}, "type": "required"}]
  }'
```

### List Calendar Events (Upcoming)
```bash
curl -s "https://graph.microsoft.com/v1.0/users/$MS_USER_EMAIL/calendar/events?\$top=10&\$select=subject,start,end,location&\$orderby=start/dateTime" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### List Contacts
```bash
curl -s "https://graph.microsoft.com/v1.0/users/$MS_USER_EMAIL/contacts?\$top=50&\$select=displayName,emailAddresses,phones" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### Create Contact
```bash
curl -s "https://graph.microsoft.com/v1.0/users/$MS_USER_EMAIL/contacts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "displayName": "John Smith - Partner",
    "emailAddresses": [{"address": "john@example.com", "name": "John Smith"}],
    "phones": [{"number": "555-555-1234", "type": "mobile"}],
    "companyName": "Example Realty Group",
    "categories": ["Partner", "Referral Source"]
  }'
```

### Forward Email (to the owner)
```bash
curl -s "https://graph.microsoft.com/v1.0/users/$MS_USER_EMAIL/messages/$MESSAGE_ID/forward" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"toRecipients":[{"emailAddress":{"address":"owner@yourdomain.com"}}],"comment":"New lead from partner - can you follow up?"}'
```

## Integration Patterns

### Pattern 1: New Lead Intake (Email -> CRM -> Estimate)
1. Agent reads inbox, finds new email from partner
2. Agent extracts lead info (name, address, sqft, service type)
3. Agent creates lead record in CRM (crm-lite)
4. Agent runs estimator-engine to calculate price
5. Agent replies with estimate and asks for preferred dates

### Pattern 2: Estimate -> Payment Flow
1. Agent sends estimate email with payment link (from stripe-payments skill)
2. Agent monitors inbox for reply or payment confirmation
3. When paid, agent creates calendar event for the job
4. Agent updates CRM lead status to "Booked"

### Pattern 3: Partner Outreach Campaign
1. Agent reads Mailchimp partner contact list
2. For each partner, agent sends personalized email from Outlook
3. Agent logs activity in CRM
4. Agent schedules follow-up reminders as calendar events

### Pattern 4: Daily Report to Owners
1. Agent compiles CRM stats (new leads, estimates sent, jobs booked, payments received)
2. Agent sends daily summary email to the owner
3. Could be automated via cron job

## Token Management

Tokens expire after ~1 hour. For cron jobs, fetch fresh token each run:
```python
import os, requests, json

def get_token():
    r = requests.post(
        f"https://login.microsoftonline.com/{os.environ['MS_TENANT_ID']}/oauth2/v2.0/token",
        data={
            "client_id": os.environ["MS_CLIENT_ID"],
            "client_secret": os.environ["MS_CLIENT_SECRET"],
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }
    )
    return r.json()["access_token"]
```

## When NOT to Use This Skill (Critical Diagnostic)
- **"Uses Outlook" ≠ "Has Microsoft 365".** Many small businesses use the Outlook
  desktop app as an IMAP client for third-party email hosting (GoDaddy Workspace
  Email, Google Workspace, etc.). The mailbox lives on the third-party's servers,
  not Microsoft's. The Outlook app is just a client.
- **Diagnostic test:** Try signing in at `portal.azure.com` with the business email
  address. If Microsoft says "We couldn't find an account with that username,"
  the email is NOT on M365 — this skill does not apply. Use IMAP/SMTP via the
  `himalaya` skill instead.
- **GoDaddy Workspace Email** is the most common case for US small businesses.
  Standard settings: IMAP `imap.secureserver.net:993` TLS, SMTP
  `smtpout.secureserver.net:465` TLS. Login is the email address + the email
  password (not the GoDaddy account login ID).
- This skill remains valid for businesses with a real M365 tenant (Azure AD,
  Exchange Online, or GoDaddy-resold M365 where the mailbox IS on Microsoft
  servers but billing goes through GoDaddy). When in doubt, check the Azure
  portal first before starting the app registration.

## Common Pitfalls
- **Client credentials flow = app-only access**: No user must sign in, but admin must grant consent
- **$ in URL query params**: Must be escaped in bash as `\$` to prevent variable expansion
- **Token expiry**: 60 min lifetime — refresh for long-running operations
- **Email body HTML**: Use contentType "HTML" for formatted emails, "Text" for plain
- **Timezone in calendar events**: Use the appropriate timezone string for your region (e.g., "Eastern Standard Time" handles EDT/EST automatically)
- **Graph API throttling**: 10,000 requests/10min per app per tenant — more than enough
- **SaveToSentItems**: Set to true so owners can see what the agent sent
- **User email in URL path**: Must be the actual mailbox email, not the app registration email
- **Attachments**: Not covered here — if needed, use multipart with /messages/{id}/attachments

## Verification Checklist
- [ ] MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET set in environment
- [ ] MS_USER_EMAIL set to business Outlook address
- [ ] Can get access token (client credentials flow)
- [ ] Can read inbox (GET messages)
- [ ] Can send test email (POST sendMail)
- [ ] Can create calendar event
- [ ] Can list contacts
- [ ] Admin consent granted for all API permissions
- [ ] Email integration with stripe-payments (send payment links)
- [ ] Email integration with crm-lite (log sent emails as activities)