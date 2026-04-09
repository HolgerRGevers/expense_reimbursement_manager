# Zoho Creator Custom API Builder — Research & Reference

## Overview

Zoho Creator's **Custom API Builder** is a microservices feature that lets you define custom REST API endpoints within your Creator application. Unlike the standard REST API v2.1 (which provides fixed CRUD operations on forms and reports), Custom APIs execute **arbitrary Deluge logic** — query multiple forms, compute values, call external services, and return structured JSON responses.

This is conceptually a **serverless function platform** embedded in Creator: you define the interface (request/response schema) and write the logic (Deluge script), and Creator hosts the endpoint with OAuth 2.0 authentication.

### How it differs from REST API v2.1

| Feature | REST API v2.1 | Custom API Builder |
|---------|---------------|-------------------|
| Purpose | CRUD on forms/reports | Arbitrary Deluge logic |
| Endpoints | Pre-defined (add/get/update/delete record) | User-defined |
| Logic | Fixed operations | Custom Deluge scripts |
| Response format | Zoho standard JSON | User-defined structure |
| Setup | Automatic for all forms | Manual via wizard |
| Use cases | Data import/export | Business logic, aggregations, integrations |

### Location in Creator UI

**Developer Guide > Microservices > Custom API**

Accessible from the Creator application settings panel under the developer/microservices section.

---

## The 5-Step Wizard

The Custom API Builder uses a guided wizard with 5 steps. The screenshot from the Creator UI confirms these steps in the left sidebar: Basic Details, Request, Response, Actions, Summary.

### Step 1: Basic Details

| Field | Description | Notes |
|-------|-------------|-------|
| **Display Name** | Human-readable name for the API | Descriptive, memorable |
| **Link Name** | Auto-generated from Display Name | Becomes the URL path segment. Uses underscores (e.g., `Fetch_Records`). Can be manually edited. |
| **Description** | Optional description | Max 200 characters |

**Hints from Creator UI** (visible in screenshot):
- "Ensure to name your custom API with terms that are descriptive, memorable, and reflective of their functionality."
- "The link name will be appended to the endpoint URL generated."

### Step 2: Request

Define the input parameters your API accepts:

| Parameter Property | Description |
|-------------------|-------------|
| **Parameter Name** | Name of the input parameter |
| **Data Type** | Text, Number, Boolean, Date, etc. |
| **Required/Optional** | Whether the parameter must be provided |

Parameters are passed in the API request body (POST) or query string (GET) and are accessible in the Actions Deluge script.

### Step 3: Response

Define the output structure your API returns:

| Response Property | Description |
|-------------------|-------------|
| **Key Name** | Name of the response field |
| **Data Type** | Text, Number, Boolean, Date, List, Map, etc. |

The response structure defines the JSON schema of successful API responses. Your Deluge script in the Actions step must populate these response keys.

### Step 4: Actions

Write the Deluge script that processes the request and builds the response.

**Key characteristics:**
- No `input.FieldName` — this is NOT a form context. Parameters come from the request definition.
- No `alert`, `cancel submit`, or other form-specific tasks — these are meaningless in API context.
- Must populate the response keys defined in Step 3.
- Can query any form/report in the application.
- Can use `invokeUrl` to call external services.
- Can perform `insert into`, updates, and record operations.
- Has access to `zoho.loginuser`, `zoho.currentdate`, etc.

**Example pattern (UNCERTAIN — needs verification in Creator):**
```
// Extract request parameters
// (exact syntax for parameter access NEEDS VERIFICATION)

// Business logic
pendingRecs = Expense_Claims[Status == "Pending for Approval"];
pendingCount = ifnull(pendingRecs.count(), 0);

approvedRecs = Expense_Claims[Status == "Approved"];
approvedCount = ifnull(approvedRecs.count(), 0);

// Build response (exact syntax NEEDS VERIFICATION)
// Response keys must match Step 3 definitions
```

### Step 5: Summary

Review all configuration (name, parameters, response, script) and publish the API.

---

## Endpoint URL Format

**UNCERTAIN**: The exact endpoint URL format could not be verified (Zoho help portal blocked direct access). Based on research, it likely follows one of these patterns:

```
https://www.zohoapis.com/creator/custom/v2.1/{owner}/{app}/{link_name}
```

or:

```
https://creator.zoho.com/api/v2.1/{owner}/{app}/custom/{link_name}
```

**NEEDS VERIFICATION**: Create a test Custom API in Creator and check the generated endpoint URL.

---

## Authentication

Custom APIs use the same **OAuth 2.0** authentication as the standard REST API v2.1:

```
Authorization: Zoho-oauthtoken {access_token}
```

### OAuth Scope

**UNCERTAIN**: The exact OAuth scope required for Custom API execution needs verification. Possibilities:
- May use existing scope: `ZohoCreator.report.READ` (if read-only)
- May require a dedicated scope like `ZohoCreator.custom_api.EXECUTE`
- May require `ZohoCreator.report.CREATE` if the API performs write operations

**NEEDS VERIFICATION**: Check Zoho API Console scope options when creating a Self Client.

### Existing OAuth Configuration

The project already has OAuth infrastructure in place:
- `config/zoho-api.yaml.template` — credential template
- `tools/upload_to_creator.py` — TokenManager class with automatic refresh
- `docs/imports/api-upload-guide.md` — full OAuth setup guide

Custom API calls can reuse this same OAuth flow. The `TokenManager` in `upload_to_creator.py` could be extracted into a shared utility for both standard API and Custom API calls.

---

## Invocation Methods

### 1. From Widgets (JS API v2)

```javascript
var config = {
    // Configuration parameters (UNCERTAIN — exact schema needs verification)
    api_name: "Get_Dashboard_Summary",
    // request parameters here
};

ZOHO.CREATOR.DATA.invokeCustomApi(config)
    .then(function(response) {
        console.log(response);
    });
```

Requires `ZOHO.CREATOR.init()` to be called first. Only works within Creator widgets embedded in the application.

### 2. From External Applications (REST)

```bash
curl -X POST \
  "https://www.zohoapis.com/creator/custom/v2.1/{owner}/{app}/{link_name}" \
  -H "Authorization: Zoho-oauthtoken {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"param1": "value1", "param2": "value2"}'
```

**UNCERTAIN**: The exact URL and request body format need verification.

### 3. From Other Deluge Scripts (invokeUrl)

```
response = invokeUrl
[
    url : "https://www.zohoapis.com/creator/custom/v2.1/{owner}/{app}/{link_name}"
    type : POST
    headers : {"Authorization": "Zoho-oauthtoken " + accessToken}
    parameters : paramMap
];
```

---

## Plan Tier Availability

| Feature | Free Trial | Standard | Professional | Enterprise |
|---------|-----------|----------|-------------|------------|
| REST API v2.1 | Limited (1,000 calls/day) | 25,000 calls/day | 50,000 calls/day | 100,000 calls/day |
| Custom API Builder | **UNCERTAIN** (likely NO) | **Yes** | Yes | Yes |
| Rate limit per minute | 50 calls/user | 50 calls/user | 50 calls/user | 50 calls/user |
| Concurrent API calls | 6 per account | 6 per account | 6 per account | 6 per account |

**UNCERTAIN**: Whether the Free Trial has any Custom API Builder access. The feature is documented under paid plan features, but Creator trials often include all features for evaluation.

The project is transitioning from **Free Trial to Standard**, which should include Custom API Builder access.

---

## ERM Use Cases

Custom APIs that would add value to the Expense Reimbursement Manager:

### High Priority

#### 1. Get_Dashboard_Summary
**Purpose**: Return aggregated claim statistics for external dashboards or embedded widgets.

**Request parameters**: `department` (optional filter), `date_from` (optional), `date_to` (optional)

**Response**: `pending_count`, `approved_count`, `rejected_count`, `total_amount_pending`, `total_amount_approved`, `avg_processing_days`

**Alignment**: Extends the existing Sustainability Dashboard with external data access.

#### 2. Get_Claim_Status
**Purpose**: Allow external systems to query claim status by reference number.

**Request parameters**: `claim_reference` (required, e.g., "EXP-0042")

**Response**: `status`, `amount_zar`, `department`, `category`, `submitted_date`, `last_action`, `last_action_date`

**Alignment**: Enables employee self-service portals and mobile apps to check claim status without Creator UI access.

### Medium Priority

#### 3. Get_ESG_Summary
**Purpose**: Return carbon estimates and ESG category breakdowns for sustainability reporting tools.

**Request parameters**: `date_from` (optional), `date_to` (optional), `department` (optional)

**Response**: `total_carbon_kg`, `category_breakdown` (list), `department_breakdown` (list), `claim_count`

**Alignment**: Supports ISSB/GRI reporting requirements (v0.7.0 ESG tracking).

#### 4. Create_Journal_Entry
**Purpose**: On approval, push GL-mapped journal entry data to Zoho Books or external accounting system.

**Request parameters**: `claim_id` (required)

**Response**: `journal_entry_id`, `gl_code`, `amount`, `status`

**Alignment**: Directly supports the mid-term Zoho Books integration on the future roadmap.

#### 5. Get_SLA_Breaches
**Purpose**: Return claims approaching or past SLA deadlines for proactive management.

**Request parameters**: `threshold_days` (optional, default 2), `department` (optional)

**Response**: `breached_claims` (list with reference, assignee, days_pending), `at_risk_claims` (list)

**Alignment**: Complements the existing `sla_enforcement_daily` scheduled task.

### Low Priority

#### 6. Submit_Expense_Claim
**Purpose**: Accept claim data from external apps (bypasses Creator form UI).

**Governance concern**: Must replicate all `on_validate` rules (future date check, 90-day window, positive amount, receipt requirement). Risk of validation bypass if not carefully implemented.

#### 7. Approve_Claim
**Purpose**: External system triggers approval action.

**Governance concern**: High risk — self-approval prevention, segregation of duties, Two-Key authorization all depend on Creator's native approval process context. Exposing approval via API would require replicating the entire governance chain. **Not recommended** without thorough security review.

---

## Relationship to Existing Tooling

### What already works for Custom APIs

| Tool | Reusable? | Notes |
|------|-----------|-------|
| `config/zoho-api.yaml` | Yes | Same OAuth credentials |
| `tools/upload_to_creator.py` TokenManager | Yes | Token refresh logic is reusable |
| `tools/lint_deluge.py` | Partially | Line rules work; need new context-specific rules |
| `tools/scaffold_deluge.py` | Needs extension | New `custom-api` context and template |
| `config/deluge-manifest.yaml` | Needs extension | New `custom-api` entries |

### What needs to be added

1. **Manifest context**: `custom-api` alongside `form-workflow`, `approval-script`, `scheduled`
2. **Scaffold template**: Header with API metadata, request extraction, response map construction
3. **Linter rules**: DG020 (response map required), DG021 (no form-specific tasks in API context)
4. **Deluge reference**: Custom API section in `config/deluge-reference.md`
5. **API caller tool**: Future — a `tools/call_custom_api.py` for testing Custom APIs (similar to upload_to_creator.py)

---

## .ds Export Behavior

**UNCERTAIN**: Whether Custom APIs appear in .ds file exports.

Based on the project's .ds import capability matrix (see `docs/discovery-log.md` DL-003):
- Form structures: YES
- Workflow scripts: YES
- Approval processes: YES
- Scheduled tasks: YES
- Custom APIs: **UNKNOWN** — needs testing

If Custom APIs DO appear in .ds exports, the `parse_ds_export.py` tool would need to be extended to extract them. If they do NOT, Custom API Deluge scripts would need to be managed purely through the scaffold/manifest system and manually applied in the Creator UI.

**NEEDS VERIFICATION**: Export a .ds file from an app that has a Custom API and inspect the structure.

---

## Testing Strategy

### 1. Manual Testing (Creator UI)
Create a simple test Custom API (e.g., `Test_Ping` that returns a static message) and verify:
- Wizard completion
- Endpoint URL generated
- Response format

### 2. Postman/curl Testing
```bash
# Test Custom API call (URL format NEEDS VERIFICATION)
curl -X POST \
  "https://www.zohoapis.com/creator/custom/v2.1/{owner}/{app}/Test_Ping" \
  -H "Authorization: Zoho-oauthtoken {access_token}" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 3. Widget Testing
Create a simple widget that calls the Custom API using `ZOHO.CREATOR.DATA.invokeCustomApi()` and displays the result.

---

## Open Questions for Creator Verification

1. **Endpoint URL format**: What is the exact URL generated by the Custom API Builder?
2. **OAuth scope**: What scope is needed for Custom API execution?
3. **Parameter access**: How are request parameters accessed in the Actions Deluge script?
4. **Response construction**: How is the response map populated in the Actions Deluge script?
5. **Error handling**: How are errors returned from Custom APIs?
6. **.ds export**: Do Custom APIs appear in .ds exports?
7. **Free Trial access**: Is the Custom API Builder available on Free Trial?
8. **Rate limits**: Do Custom API calls share the same daily quota as standard API calls?
9. **Logging/monitoring**: Is there a built-in execution log for Custom API calls?

---

## Sources

- [Zoho Creator Custom API Knowledge Base](https://help.zoho.com/portal/en/kb/creator/developer-guide/microservices/custom-api)
- [Understand Custom APIs](https://help.zoho.com/portal/en/kb/creator/developer-guide/microservices/custom-api/articles/understand-custom-apis)
- [Creating and Managing Custom APIs](https://help.zoho.com/portal/en/kb/creator/developer-guide/microservices/custom-api/articles/create-and-manage-custom-apis)
- [Custom API Builder Landing Page](https://www.zoho.com/creator/api-integration-building-software/)
- [JS API v2 — invokeCustomApi](https://www.zoho.com/creator/help/js-api/v2/custom-api.html)
- [Unlocking the Power of Custom APIs in Zoho Creator](https://www.nurturespark.com/blog/unlocking-the-power-of-custom-apis-in-zoho-creator)
- [API Limits](https://www.zoho.com/creator/help/api/v2.1/api-limits.html)
