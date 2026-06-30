# GoDaddy Workspace Email — Himalaya Configuration

## When to Use
- Small business email hosted through GoDaddy Workspace Email (not Microsoft 365)
- GoDaddy-managed domain with IMAP/SMTP mailboxes
- User checks email via Outlook desktop app (IMAP client), not a Microsoft account

## How to Identify GoDaddy Workspace Email
- Microsoft login returns "account not found" for the business email address
- GoDaddy portal shows the mailboxes under My Products > Email
- GoDaddy webmail accessible at `email.godaddy.com` or `sso.godaddy.com`
- Login ID may be numeric (e.g. `123456789`) but IMAP auth uses the full email address

## GoDaddy IMAP/SMTP Settings

| Protocol | Host | Port | Encryption |
|----------|------|------|------------|
| IMAP (incoming) | `imap.secureserver.net` | 993 | TLS |
| SMTP (outgoing) | `smtpout.secureserver.net` | 465 | TLS |
| SMTP (alt) | `smtpout.secureserver.net` | 587 | STARTTLS |

## Config File (`~/.config/himalaya/config.toml`)

```toml
[accounts.godaddy]
email = "user@business.com"
display-name = "User Name - Business Name"
default = true

backend.type = "imap"
backend.host = "imap.secureserver.net"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "user@business.com"
backend.auth.type = "password"
backend.auth.cmd = "cat ~/.config/himalaya/.business-pw"

message.send.backend.type = "smtp"
message.send.backend.host = "smtpout.secureserver.net"
message.send.backend.port = 465
message.send.backend.encryption.type = "tls"
message.send.backend.login = "user@business.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "cat ~/.config/himalaya/.business-pw"

folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
```

## Password Storage
```bash
echo -n 'EMAIL_PASSWORD' > ~/.config/himalaya/.business-pw
chmod 600 ~/.config/himalaya/.business-pw
```

## Verified Working (June 27, 2026)
- IMAP read: `himalaya envelope list` — pulled 20 real emails from inbox
- SMTP send: `himalaya template send` — test email delivered to own inbox
- Draft save: `himalaya message save --folder Drafts` — draft visible in GoDaddy webmail Drafts
- Folder listing: `himalaya envelope list --folder Drafts` — confirmed draft saved correctly

## What's NOT Available via IMAP (vs Microsoft Graph)
- Calendar API — no scheduling through IMAP
- Contacts API — no contact sync through IMAP
- These require a separate integration (Google Calendar, CalDAV, etc.)