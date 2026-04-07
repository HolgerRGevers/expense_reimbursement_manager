# Zoho Creator REST API v2.1 Upload Guide

## Overview

The Zoho Creator REST API v2.1 allows programmatic record creation in existing applications. This guide covers OAuth setup, authentication flow, and batch upload patterns used by `tools/upload_to_creator.py`.

## Prerequisites

- Zoho Creator account (Standard plan or above for API access)
- Access to Zoho API Console (api-console.zoho.com)
- Python 3.8+ (for upload tool)

## Step 1: Register a Self Client

1. Go to [Zoho API Console](https://api-console.zoho.com)
2. Click **Add Client** > **Self Client**
3. Note your **Client ID** and **Client Secret**

## Step 2: Generate Grant Token

1. In the Self Client page, click **Generate Code**
2. Enter the required scope:
   ```
   ZohoCreator.report.CREATE,ZohoCreator.report.UPDATE,ZohoCreator.report.READ
   ```
3. Set scope duration (e.g., 10 minutes)
4. Provide a description (e.g., "ERM data import")
5. Click **Create** and copy the generated grant token

## Step 3: Exchange for Refresh Token

```bash
curl -X POST https://accounts.zoho.com/oauth/v2/token \
  -d "grant_type=authorization_code" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code=YOUR_GRANT_TOKEN"
```

Response:
```json
{
    "access_token": "1000.xxxx",
    "refresh_token": "1000.yyyy",
    "token_type": "Bearer",
    "expires_in": 3600
}
```

**Save the refresh token** -- it does not expire and is used to generate new access tokens.

## Step 4: Configure the Upload Tool

Create `config/zoho-api.yaml` (this file is in .gitignore):

```yaml
client_id: "1000.XXXXXXXXXXXXXXXXXXXX"
client_secret: "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
refresh_token: "1000.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
owner: "your_zoho_username"
app: "expense-reimbursement-management"
api_base: "https://creator.zoho.com/api/v2.1"
auth_base: "https://accounts.zoho.com"
```

**SECURITY**: Never commit this file to version control.

## Step 5: Run the Upload

### Mock Mode (default -- no API calls)

```bash
python tools/upload_to_creator.py --config config/zoho-api.yaml --csv-dir exports/csv/
```

Mock mode:
- Validates configuration file format
- Reads and parses all CSV files
- Checks field mappings against database
- Logs what WOULD be sent (record counts, field values)
- Does NOT make any API calls

### Live Mode

```bash
python tools/upload_to_creator.py --config config/zoho-api.yaml --csv-dir exports/csv/ --live
```

Live mode:
- Refreshes OAuth access token
- Uploads records in dependency order
- Batches up to 200 records per request
- Handles rate limiting with exponential backoff
- Logs all API responses

---

## API Reference

### Add Single Record

```
POST /api/v2.1/{owner}/{app}/form/{form_link_name}/record
Authorization: Zoho-oauthtoken {access_token}
Content-Type: application/json

{
    "data": {
        "Department_Name": "Finance",
        "Active": true
    }
}
```

### Add Multiple Records (up to 200)

```
POST /api/v2.1/{owner}/{app}/form/{form_link_name}/record
Authorization: Zoho-oauthtoken {access_token}
Content-Type: application/json

{
    "data": [
        {"Department_Name": "Finance", "Active": true},
        {"Department_Name": "Sales", "Active": true}
    ]
}
```

### Response (Success)

```json
{
    "code": 3000,
    "data": {
        "ID": "12345678901234"
    }
}
```

### Response (Error)

```json
{
    "code": 2892,
    "error": {
        "message": "Mandatory field is empty"
    }
}
```

## Token Refresh Flow

Access tokens expire after 1 hour. The upload tool automatically refreshes:

```
POST https://accounts.zoho.com/oauth/v2/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&client_id=YOUR_CLIENT_ID
&client_secret=YOUR_CLIENT_SECRET
&refresh_token=YOUR_REFRESH_TOKEN
```

## Rate Limits

| Plan | API Calls/Day | Records/Request |
|------|---------------|-----------------|
| Free | 1,000 | 200 |
| Standard | 25,000 | 200 |
| Professional | 50,000 | 200 |
| Enterprise | 100,000 | 200 |

When rate limited (HTTP 429):
- Wait for the `Retry-After` header duration
- If no header, use exponential backoff: 2s, 4s, 8s, 16s

## Upload Order for ERM

The upload tool processes tables in this order to satisfy FK dependencies:

1. **Departments** (no dependencies)
2. **Clients** (no dependencies)
3. **GL_Accounts** (no dependencies)
4. **Approval_Thresholds** (no dependencies)
5. **Expense_Claims** (depends on 1-3)
6. **Approval_History** (depends on 5)

## Common Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| 3000 | Success | -- |
| 2890 | Invalid OAuth token | Refresh access token |
| 2891 | Invalid scope | Check OAuth scope includes CREATE |
| 2892 | Mandatory field empty | Provide required field value |
| 2893 | Duplicate value | Unique constraint violated |
| 2894 | Invalid field value | Check data type and constraints |
| 4429 | Rate limit exceeded | Wait and retry with backoff |

## Troubleshooting

### "Invalid OAuth token"
Your access token has expired. The upload tool handles this automatically. If using manual API calls, regenerate the access token using the refresh token.

### "Mandatory field is empty"
Check which fields are mandatory in the target form. Some Zoho Creator fields (like Added_User) are auto-populated and should NOT be included in API payloads.

### "Record not added - Lookup value not found"
The FK reference value does not exist in the parent form. Ensure parent tables are uploaded first and the lookup value matches exactly.

### Timeout errors
For large batches, reduce the batch size (use `--batch-size` flag if available) or increase the timeout. The API has a default timeout of 30 seconds per request.
