# Access-to-Zoho Creator Type Mapping Reference

## Data Type Crosswalk

| Access Type | Jet SQL Name | VBA Type | Zoho Creator Type | Size Limit | Data Loss Risk | Notes |
|-------------|-------------|----------|-------------------|------------|----------------|-------|
| AUTOINCREMENT | AUTOINCREMENT | Long | Autonumber | 4 bytes | None | Direct mapping, auto-generated |
| TEXT(n) | TEXT(n) | String | Text (Single Line) | Up to 255 chars | Low | Truncation if n > 255 in Zoho |
| MEMO | MEMO | String | Textarea (Multi-line) | ~1 GB | None | Multi-line text preserved |
| LONG | LONG | Long | Number | 4 bytes | None | 32-bit signed integer |
| INTEGER | INTEGER | Integer | Number | 2 bytes | None | 16-bit to 32-bit, no loss |
| SINGLE | SINGLE | Single | Decimal | 4 bytes | Low | Single precision may show rounding |
| DOUBLE | DOUBLE | Double | Decimal | 8 bytes | None | Double precision preserved |
| CURRENCY | CURRENCY | Currency | Currency / Decimal | 8 bytes (4dp) | None | Fixed-point, no rounding errors |
| BIT | BIT | Boolean | Checkbox | 1 bit | None | Access: -1/0 must convert to true/false |
| DATETIME | DATETIME | Date | DateTime | 8 bytes | Low | Access has no timezone awareness |
| BYTE | BYTE | Byte | Number | 1 byte (0-255) | None | Small integer preserved |
| GUID | GUID | String | Text | 16 bytes | None | Stored as 36-char string in Zoho |
| BINARY(n) | BINARY(n) | Byte() | (none) | Up to 510 bytes | **High** | No Zoho equivalent - exclude or convert |
| IMAGE/OLE | IMAGE | Byte() | File | ~1 GB | **Medium** | OLE Object extraction required |

## Boolean Conversion Detail

Access stores Boolean values as:
- **True**: `-1` (all bits set)
- **False**: `0`

Zoho Creator expects:
- **True**: `true` (lowercase string)
- **False**: `false` (lowercase string)

The `export_access_csv.py` tool handles this conversion automatically. If exporting manually, ensure BIT columns are converted before import.

## DateTime Conversion Detail

| Aspect | Access | Zoho Creator |
|--------|--------|-------------|
| Storage | OLE Automation Date (8-byte float) | Internal timestamp |
| Format | Locale-dependent display | yyyy-MM-dd HH:mm:ss |
| Timezone | None (naive datetime) | Server timezone (configurable) |
| Range | Jan 1, 100 to Dec 31, 9999 | Standard datetime range |

**Export format**: Always use ISO 8601 (`yyyy-MM-dd HH:mm:ss`) when exporting for Zoho import.

## Currency Conversion Detail

| Aspect | Access | Zoho Creator |
|--------|--------|-------------|
| Storage | 8-byte fixed-point | Decimal |
| Precision | Exactly 4 decimal places | Configurable decimal places |
| Symbol | Locale-dependent (R, $, etc.) | Field-level currency setting |
| Rounding | No rounding errors (fixed-point) | Standard decimal arithmetic |

**Export format**: Export as plain decimal string without currency symbols (e.g., `999.99` not `R999.99`).

## TEXT/MEMO Field Size Mapping

| Access Field | Access Max Length | Zoho Field Type | Zoho Max Length | Action Required |
|-------------|-------------------|-----------------|-----------------|-----------------|
| TEXT(20) | 20 chars | Text (Single Line) | 255 chars | None |
| TEXT(100) | 100 chars | Text (Single Line) | 255 chars | None |
| TEXT(200) | 200 chars | Text (Single Line) | 255 chars | None |
| TEXT(255) | 255 chars | Text (Single Line) | 255 chars | None |
| MEMO | ~1 GB | Textarea (Multi-line) | 50,000 chars | Check max length |

## ERM-Specific Field Type Mappings

### Departments Table

| Access Field | Access Type | Zoho Form | Zoho Field | Zoho Type |
|-------------|-------------|-----------|------------|-----------|
| ID | AUTOINCREMENT | departments | department_id | autonumber |
| Department_Name | TEXT(100) | departments | name | text |
| Active | BIT | departments | is_active | checkbox |

### Clients Table

| Access Field | Access Type | Zoho Form | Zoho Field | Zoho Type |
|-------------|-------------|-----------|------------|-----------|
| ID | AUTOINCREMENT | clients | client_id | autonumber |
| Client_Name | TEXT(100) | clients | name | text |
| Active | BIT | clients | is_active | checkbox |

### GL_Accounts Table

| Access Field | Access Type | Zoho Form | Zoho Field | Zoho Type |
|-------------|-------------|-----------|------------|-----------|
| ID | AUTOINCREMENT | gl_accounts | (system ID) | autonumber |
| GL_Code | TEXT(20) | gl_accounts | gl_code | text |
| Account_Name | TEXT(200) | gl_accounts | account_name | text |
| Expense_Category | TEXT(100) | gl_accounts | expense_category | picklist |
| Receipt_Required | BIT | gl_accounts | receipt_required | checkbox |
| SARS_Provision | TEXT(100) | gl_accounts | SARS_Provision | text |
| Risk_Level | TEXT(20) | gl_accounts | Risk_Level | picklist |
| Active | BIT | gl_accounts | Active | checkbox |

### Approval_Thresholds Table

| Access Field | Access Type | Zoho Form | Zoho Field | Zoho Type |
|-------------|-------------|-----------|------------|-----------|
| ID | AUTOINCREMENT | approval_thresholds | (system ID) | autonumber |
| Tier_Name | TEXT(100) | approval_thresholds | tier_name | text |
| Max_Amount_ZAR | CURRENCY | approval_thresholds | max_amount_zar | currency |
| Approver_Role | TEXT(100) | approval_thresholds | approver_role | text |
| Tier_Order | INTEGER | approval_thresholds | Tier_Order | number |
| Active | BIT | approval_thresholds | Active | checkbox |

### Expense_Claims Table

| Access Field | Access Type | Zoho Form | Zoho Field | Zoho Type |
|-------------|-------------|-----------|------------|-----------|
| ID | AUTOINCREMENT | expense_claims | ID | autonumber |
| Employee_Name | TEXT(200) | expense_claims | Employee_Name1 | name |
| Email | TEXT(200) | expense_claims | Email | picklist |
| Submission_Date | DATETIME | expense_claims | Submission_Date | datetime |
| Claim_Reference | TEXT(20) | expense_claims | Claim_Reference | text |
| Department_ID | LONG | expense_claims | department | list (lookup) |
| Client_ID | LONG | expense_claims | client | list (lookup) |
| Expense_Date | DATETIME | expense_claims | Expense_Date | date |
| Category | TEXT(100) | expense_claims | category | picklist |
| Amount_ZAR | CURRENCY | expense_claims | amount_zar | currency |
| Description | MEMO | expense_claims | description | textarea |
| VAT_Invoice_Type | TEXT(100) | expense_claims | VAT_Invoice_Type | picklist |
| POPIA_Consent | BIT | expense_claims | POPIA_Consent | checkbox |
| Status | TEXT(50) | expense_claims | status | picklist |
| Rejection_Reason | MEMO | expense_claims | Rejection_Reason | textarea |
| Version | INTEGER | expense_claims | Version | number |
| Retention_Expiry_Date | DATETIME | expense_claims | Retention_Expiry_Date | date |
| GL_Code_ID | LONG | expense_claims | gl_code | list (lookup) |

### Approval_History Table

| Access Field | Access Type | Zoho Form | Zoho Field | Zoho Type |
|-------------|-------------|-----------|------------|-----------|
| ID | AUTOINCREMENT | approval_history | (system ID) | autonumber |
| Claim_ID | LONG | approval_history | claim | list (lookup) |
| Action_Type | TEXT(100) | approval_history | action_1 | picklist |
| Actor | TEXT(200) | approval_history | actor | text |
| Action_Timestamp | DATETIME | approval_history | timestamp | datetime |
| Comments | MEMO | approval_history | comments | textarea |

**IMPORTANT**: The Zoho field for Action_Type is `action_1` (not `action`). This is a known Creator naming convention -- see DL-001 in `docs/discovery-log.md`.

## Relationship Mapping

| Access Relationship | Access FK | Zoho Lookup |
|--------------------|-----------|-------------|
| FK_EC_Dept | Expense_Claims.Department_ID -> Departments.ID | expense_claims.department -> departments |
| FK_EC_Client | Expense_Claims.Client_ID -> Clients.ID | expense_claims.client -> clients |
| FK_EC_GL | Expense_Claims.GL_Code_ID -> GL_Accounts.ID | expense_claims.gl_code -> gl_accounts |
| FK_AH_Claim | Approval_History.Claim_ID -> Expense_Claims.ID | approval_history.claim -> expense_claims |
