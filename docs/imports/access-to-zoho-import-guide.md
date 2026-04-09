# Access-to-Zoho Creator Import Guide

## Overview

This guide documents all available pathways for importing Microsoft Access data into an existing Zoho Creator application. Four import pathways are available, each suited to different scenarios.

## Import Pathway Comparison

| Pathway | Formats | Into Existing App | Automation | Max Size | Relationships |
|---------|---------|-------------------|------------|----------|---------------|
| UI Import | .csv, .xlsx, .accdb, .mdb, .json, .tsv, .ods | Yes (Add/Update) | Manual | CSV 2GB, others 100MB | No |
| MS Access Migration Tool | .mdb, .accdb | Yes ("Add data to Application") | Semi-auto | Table-dependent | Yes (preserved) |
| REST API v2.1 | JSON | Yes (POST per form) | Fully scriptable | 200 records/request | Manual (by ID) |
| .ds File Import | .ds | Yes (structural) | Manual | N/A | Schema-level only |

## Recommended Pathway by Use Case

| Use Case | Recommended Pathway | Reason |
|----------|---------------------|--------|
| Initial seed data (< 100 records) | UI Import (CSV) | Fastest, no setup |
| Large dataset migration | REST API v2.1 | Scriptable, error handling |
| Schema + data together | MS Access Migration Tool | Preserves relationships |
| Structure-only deployment | .ds File Import | Scripts + fields + reports |
| Recurring data sync | REST API v2.1 | Automated, repeatable |

---

## Pathway 1: UI Import (Report > Import Data)

### Supported Formats
.xls, .xlsx, .xlsm, .csv, .tsv, .ods, .accdb, .mdb, .json, .numbers

### Steps

1. Navigate to the target **report** in Zoho Creator
2. Click **More options** (three dots) in the top-right corner
3. Select **Import Data**
4. Choose data source:
   - **Local storage**: Upload a file from your computer
   - **URL**: Provide a publicly accessible direct download link
5. Configure import settings:
   - **First row is field labels**: Yes/No
   - **Import mode**: Add records / Update records
   - **Date format**: Select the format matching your data
   - **Error handling**: Skip row / Stop import
6. **Field mapping**: Map each column to the corresponding Zoho Creator form field
7. Click **Import**

### Import Modes

- **Add records**: Appends new records to the existing form data
- **Update records**: Overwrites existing records based on a unique field value
  - Only available if the form has at least one field with "No Duplicate Values" enabled
  - WARNING: Updates are irreversible -- backup data before using

### Limitations

- CSV files: max 2 GB
- All other formats: max 100 MB
- Access permission must be granted for the target form
- Lookup field relationships are NOT preserved (imported as plain text)
- No workflow triggers fire on imported records
- No approval process triggers on imported records

### Best Practice for ERM

Import lookup tables first (Departments, Clients, GL_Accounts, Approval_Thresholds), then transaction tables (Expense_Claims), then audit tables (Approval_History). This ensures FK references resolve correctly when using Update mode.

---

## Pathway 2: MS Access Migration Tool

### Prerequisites
- Windows OS
- Microsoft .NET Framework 2.0+
- Microsoft Access Database Engine (if Access is not installed)
- Zoho Creator account credentials

### Steps

1. Download the Zoho Migration Tool from Zoho Creator
2. Launch the tool and sign in with Zoho credentials
3. Select **File > Open** and choose your .accdb/.mdb file
4. The tool displays all tables with their relationships
5. To import into an **existing** application:
   - Select **File > Upload to Zoho Creator > Add data to Application**
   - Choose the target application
6. Map each Access table to a Zoho Creator form
7. Map each Access column to a Zoho Creator field
8. Click **Upload**

### What Gets Preserved
- Table relationships (imported as Zoho lookup fields)
- Data types (mapped to Zoho equivalents)
- Seed data values
- Table/field names (may be adjusted for Zoho naming rules)

### What Does NOT Get Preserved
- Access queries (no equivalent in Creator import)
- Access forms/reports (Creator has its own form/report system)
- VBA code/macros (must be rewritten as Deluge scripts)
- Access indexes (Creator manages indexes internally)

### Known Issues
- Tool requires Windows (no macOS/Linux support)
- Large databases may timeout during upload
- Some complex data types (OLE Object, Hyperlink) may not map cleanly

---

## Pathway 3: REST API v2.1

### Overview
Fully scriptable import using Zoho Creator's REST API. Best for automated, repeatable imports with error handling and logging.

### Authentication: OAuth 2.0

1. Go to **Zoho API Console** (api-console.zoho.com)
2. Create a **Self Client**
3. Generate a grant token with scope: `ZohoCreator.report.CREATE,ZohoCreator.report.UPDATE`
4. Exchange the grant token for refresh + access tokens
5. Store the refresh token securely (it does not expire)

See `docs/imports/api-upload-guide.md` for detailed setup instructions.

### Endpoint

```
POST https://creator.zoho.com/api/v2.1/{owner}/{app}/form/{form_link_name}/record
```

### Request Format

```json
{
    "data": {
        "field_link_name_1": "value1",
        "field_link_name_2": "value2"
    }
}
```

### Batch Import (up to 200 records)

```json
{
    "data": [
        {"field_1": "val1", "field_2": "val2"},
        {"field_1": "val3", "field_2": "val4"}
    ]
}
```

### Rate Limits
- Max 200 records per request
- Rate limits vary by Zoho Creator plan
- HTTP 429 = rate limited (implement exponential backoff)

### Import Order (for ERM)

1. Departments (no dependencies)
2. Clients (no dependencies)
3. GL_Accounts (no dependencies)
4. Approval_Thresholds (no dependencies)
5. Expense_Claims (depends on Departments, Clients, GL_Accounts)
6. Approval_History (depends on Expense_Claims)

### Tooling

This project provides `tools/upload_to_creator.py` for automated API uploads:
```bash
python tools/upload_to_creator.py --config config/zoho-api.yaml --csv-dir exports/csv/           # mock mode
python tools/upload_to_creator.py --config config/zoho-api.yaml --csv-dir exports/csv/ --live     # live mode
```

---

## Pathway 4: .ds File Import

### Purpose
Structural deployment (forms, fields, scripts, reports, permissions). Not designed for bulk data import.

### What It Imports
- Form definitions and field schemas
- Embedded Deluge scripts (workflows, approval processes, scheduled tasks)
- Report configurations and conditional formatting
- Role hierarchy and share settings
- Dashboard pages

### What It Does NOT Import
- Record data (use Pathways 1-3 for data)
- User accounts
- Connection/integration settings

### Usage
- Settings > Developer Space > Import Application
- Apply ONE type of change at a time (see CLAUDE.md deployment rules)

---

## Data Preparation Checklist

Before importing Access data to Zoho Creator:

- [ ] Export Access tables to CSV using `tools/export_access_csv.py`
- [ ] Run hybrid linter: `python tools/lint_hybrid.py --data exports/csv/ --scripts src/deluge/`
- [ ] Run data validator: `python tools/validate_import_data.py exports/csv/`
- [ ] Verify BIT fields converted to true/false (not -1/0)
- [ ] Verify DATETIME fields in ISO 8601 format
- [ ] Verify CURRENCY values as decimal strings (not locale-formatted)
- [ ] Verify TEXT fields do not exceed 255 characters for Single Line fields
- [ ] Verify referential integrity (FK values exist in parent tables)
- [ ] Verify picklist values match Zoho valid sets (Status, Category, etc.)
- [ ] Backup existing Zoho Creator data before Update mode imports

## Error Recovery

| Error | Cause | Fix |
|-------|-------|-----|
| "Field validation failed" | Value doesn't match field type/constraints | Check type_mappings, convert value |
| "Duplicate value" | Unique field constraint violated | Use Update mode or remove duplicate |
| "Mandatory field empty" | Required field has no value | Provide value or set default |
| "Lookup value not found" | FK reference doesn't exist in parent form | Import parent table first |
| "File size exceeds limit" | File > 100MB (non-CSV) or > 2GB (CSV) | Split into smaller files |
| "Rate limit exceeded" (API) | Too many API requests | Implement exponential backoff |
