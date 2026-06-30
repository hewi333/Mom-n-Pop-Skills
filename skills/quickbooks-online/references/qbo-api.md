# QuickBooks Online API v3 Reference

## Base URLs
- **Sandbox**: `https://sandbox-quickbooks.api.intuit.com`
- **Production**: `https://quickbooks.api.intuit.com`

## Authentication
All requests require:
```
Authorization: Bearer {access_token}
Accept: application/json
Content-Type: application/json
Minorversion: 75
```

## Core Endpoints

### Company Info
```
GET /v3/company/{realmId}/companyinfo/{realmId}
```

### Customers
```
POST   /v3/company/{realmId}/customer                    # Create
GET    /v3/company/{realmId}/customer/{id}               # Read
PUT    /v3/company/{realmId}/customer/{id}               # Update (sparse)
GET    /v3/company/{realmId}/query?query=SELECT * FROM Customer WHERE DisplayName='{name}'
```

### Estimates
```
POST   /v3/company/{realmId}/estimate                    # Create
GET    /v3/company/{realmId}/estimate/{id}               # Read
PUT    /v3/company/{realmId}/estimate/{id}               # Update (sparse)
POST   /v3/company/{realmId}/estimate/{id}/send?sendTo={email}  # Email
GET    /v3/company/{realmId}/estimate/{id}/pdf           # PDF download
GET    /v3/company/{realmId}/query?query=SELECT * FROM Estimate WHERE CustomerRef={id}
```

### Invoices
```
POST   /v3/company/{realmId}/invoice                     # Create
GET    /v3/company/{realmId}/invoice/{id}                # Read
PUT    /v3/company/{realmId}/invoice/{id}                # Update (sparse)
POST   /v3/company/{realmId}/invoice/{id}/send?sendTo={email}  # Email
GET    /v3/company/{realmId}/invoice/{id}/pdf            # PDF download
GET    /v3/company/{realmId}/query?query=SELECT * FROM Invoice WHERE CustomerRef={id} AND Balance > 0
```

### Payments
```
POST   /v3/company/{realmId}/payment                     # Create
GET    /v3/company/{realmId}/payment/{id}                # Read
PUT    /v3/company/{realmId}/payment/{id}                # Update (sparse)
GET    /v3/company/{realmId}/query?query=SELECT * FROM Payment WHERE CustomerRef={id}
```

### Items (Products/Services)
```
POST   /v3/company/{realmId}/item                        # Create
GET    /v3/company/{realmId}/item/{id}                   # Read
GET    /v3/company/{realmId}/query?query=SELECT * FROM Item WHERE Type='Service'
```

### Reports
```
GET /v3/company/{realmId}/reports/AgedReceivables?minorversion=75
GET /v3/company/{realmId}/reports/ProfitAndLoss?minorversion=75
GET /v3/company/{realmId}/reports/BalanceSheet?minorversion=75
```

## OAuth2 Token Refresh
```
POST https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(client_id:client_secret)}

grant_type=refresh_token&refresh_token={refresh_token}
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 3600,
  "token_type": "bearer",
  "x_refresh_token_expires_in": 8726400
}
```

## Error Codes
| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad Request | Check request body |
| 401 | Unauthorized | Refresh token, retry once |
| 403 | Forbidden | Check scopes/permissions |
| 404 | Not Found | Verify realmId + resource ID |
| 409 | Conflict | Duplicate (use RequestId header) |
| 429 | Rate Limited | Exponential backoff (max 500/min) |
| 500 | Server Error | Retry with backoff |

## Idempotency
Always include `RequestId` header (UUID) for create operations:
```
RequestId: 550e8400-e29b-41d4-a716-446655440000
```

## Service Business Mappings
| Business Concept | QB Entity | Notes |
|-----------------|-----------|-------|
| Job/Lead | Customer | DisplayName = "Last, First" |
| Estimate | Estimate | Line items from estimator-engine |
| Invoice | Invoice | Created from accepted estimate |
| Payment | Payment | Linked to invoice via LinkedTxn |
| Treatment sqft | Item (Service) | UnitPrice = $/sqft |
| Surcharges | Item (Service) | Each = separate line item |
| Deposit | Invoice.Deposit | 50% at scheduling |

## Rate Limits
- **500 requests/minute** per company
- **Throttling**: 429 response with `Retry-After` header
- Implement exponential backoff: 1s, 2s, 4s, 8s, 16s...