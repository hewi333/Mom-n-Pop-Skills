# Intuit OAuth2 Flow for QuickBooks Online

## Overview
Intuit uses OAuth 2.0 with authorization code grant type. Tokens are scoped to a specific QuickBooks company (realm).

## Prerequisites
1. Intuit Developer Account: https://developer.intuit.com
2. Create App → Get Client ID + Client Secret
3. Set Redirect URI in app settings
4. Select scopes: `com.intuit.quickbooks.accounting`

## Step 1: Authorization Request
Redirect user to:
```
https://appcenter.intuit.com/connect/oauth2?
  client_id={CLIENT_ID}&
  redirect_uri={REDIRECT_URI}&
  scope=com.intuit.quickbooks.accounting&
  response_type=code&
  state={RANDOM_STATE_STRING}
```

### Parameters
| Param | Required | Description |
|-------|----------|-------------|
| client_id | Yes | From Intuit Developer Dashboard |
| redirect_uri | Yes | Must match exactly (including scheme) |
| scope | Yes | `com.intuit.quickbooks.accounting` |
| response_type | Yes | Must be `code` |
| state | Recommended | CSRF protection (random string) |

## Step 2: Callback Handling
Intuit redirects to your `redirect_uri` with:
```
https://your-domain.com/callback?
  code={AUTHORIZATION_CODE}&
  realmId={COMPANY_ID}&
  state={STATE}
```

### Validate
1. Verify `state` matches your stored value (CSRF protection)
2. Store `realmId` (company ID) for all API calls

## Step 3: Exchange Code for Tokens
```
POST https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer
Content-Type: application/x-www-form-urlencoded
Authorization: Basic base64(client_id:client_secret)

grant_type=authorization_code&
code={AUTHORIZATION_CODE}&
redirect_uri={REDIRECT_URI}
```

### Response
```json
{
  "access_token": "eyJraWQiOiI...",
  "refresh_token": "eyJraWQiOiI...",
  "expires_in": 3600,
  "token_type": "bearer",
  "x_refresh_token_expires_in": 8726400
}
```

### Store Securely
```json
{
  "realm_id": "1234567890",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "access_expires_at": "2026-06-25T10:00:00Z",
  "refresh_expires_at": "2026-09-15T10:00:00Z"
}
```

## Step 4: Using Access Token
All API requests:
```
Authorization: Bearer {access_token}
```

## Token Refresh (Automatic)
When access token expires (1 hour):
```
POST https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer
Content-Type: application/x-www-form-urlencoded
Authorization: Basic base64(client_id:client_secret)

grant_type=refresh_token&
refresh_token={REFRESH_TOKEN}
```

### Refresh Response
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",  // NEW refresh token!
  "expires_in": 3600,
  "token_type": "bearer",
  "x_refresh_token_expires_in": 8726400
}
```

**Critical**: Save the NEW refresh token! Old one is invalidated.

## Token Lifetimes
| Token | Lifetime | Refresh |
|-------|----------|---------|
| Access Token | 1 hour (3600s) | Auto via refresh_token |
| Refresh Token | 101 days (8,726,400s) | Requires re-auth |

## Error Handling
| Error | Cause | Resolution |
|-------|-------|------------|
| `invalid_grant` | Refresh token expired/revoked | Force re-auth (user must re-authorize) |
| `invalid_client` | Wrong client_id/secret | Check credentials |
| `redirect_uri_mismatch` | URI doesn't match app settings | Fix in Intuit Dashboard |
| `unauthorized_client` | App not approved for scope | Submit for review if needed |

## Sandbox vs Production
| Environment | Auth URL | Token URL | Base API URL |
|-------------|----------|-----------|--------------|
| Sandbox | appcenter.intuit.com | oauth.platform.intuit.com | sandbox-quickbooks.api.intuit.com |
| Production | appcenter.intuit.com | oauth.platform.intuit.com | quickbooks.api.intuit.com |

**Use same client_id/secret** — only base URLs differ.

## Implementation Checklist
- [ ] Generate cryptographically random `state` parameter
- [ ] Store `state` in session/cookie for callback validation
- [ ] Exchange code for tokens within 10 minutes (code expires)
- [ ] Store tokens encrypted (Fernet/AES-256)
- [ ] Implement automatic refresh on 401 responses
- [ ] Handle `invalid_grant` → force re-auth flow
- [ ] Log all token operations for audit
- [ ] Test full flow in sandbox before production

## Integration Points
- Owner initiates auth via Telegram command: `/qbo connect`
- Agent stores tokens in `~/.hermes/qbo_tokens.json` (encrypted)
- Agent auto-refreshes before each API call if needed
- On `invalid_grant`: notify owner "QuickBooks connection expired — run /qbo connect again"