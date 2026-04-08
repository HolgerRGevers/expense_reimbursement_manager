# Field Link Names

Auto-generated from `.ds` export by `tools/parse_ds_export.py`.

## Overview

Verified field link name mapping extracted from the `.ds` export. These are the actual Deluge-accessible field identifiers used in scripts.

## Approval History (`approval_history`)

| Link Name | Display Name | Type | Notes |
|-----------|-------------|------|-------|
| claim | Add New | list |  |
| action_1 | Action | picklist |  |
| actor | Actor | text |  |
| timestamp | Timestamp | datetime |  |
| comments | Comments | textarea |  |

## Approval Thresholds (`approval_thresholds`)

| Link Name | Display Name | Type | Notes |
|-----------|-------------|------|-------|
| tier_name | Tier Name | text |  |
| max_amount_zar | Max Amount ZAR | ZAR |  |
| approver_role | Approver Role | text |  |
| Active | Active | checkbox | default: true |

## Clients (`clients`)

| Link Name | Display Name | Type | Notes |
|-----------|-------------|------|-------|
| client_id | Client ID | autonumber |  |
| name | Name | text |  |
| is_active | Active | checkbox | default: true |

## Departments (`departments`)

| Link Name | Display Name | Type | Notes |
|-----------|-------------|------|-------|
| department_id | Department ID | autonumber |  |
| name | Name | text |  |
| is_active | Active | checkbox | default: true |

## Expense Claims (`expense_claims`)

| Link Name | Display Name | Type | Notes |
|-----------|-------------|------|-------|
| Employee_Name1 | Suffix | suffix | personal data |
| prefix | Prefix | prefix |  |
| first_name | First Name | first_name |  |
| last_name | Last Name | last_name |  |
| suffix | Suffix | suffix |  |
| Email | Email | help_text | personal data |
| Submission_Date | Submission Date | datetime |  |
| claim_id | Claim ID | autonumber |  |
| department | Department | list |  |
| Claim_Reference | Claim Reference | text |  |
| client | Add New | list |  |
| Expense_Date | Expense Date | date |  |
| Department_Shadow | Department Shadow | text | private/hidden |
| category | Category | picklist |  |
| Client_Shadow | Client Shadow | text | private/hidden |
| amount_zar | Amount ZAR | ZAR |  |
| Supporting_Documents | Supporting Documents | upload file |  |
| description | Description | textarea |  |
| status | Status | picklist |  |
| Rejection_Reason | Rejection Reason | textarea |  |
| Version | Version | number | default: 1 |
| Parent_Claim_ID | Parent Claim ID | picklist | private/hidden |
| gl_code | Add New | list |  |
| Requires_Dual_Approval | Requires Dual Approval | checkbox | Two-Key flag |
| Key_1_Approver | Key 1 Approver | text | Stores Key 1 approver username |
| Key_1_Timestamp | Key 1 Timestamp | datetime | When Key 1 approved |
| Key_2_Approver | Key 2 Approver | text | Stores Key 2 approver username |
| Key_2_Timestamp | Key 2 Timestamp | datetime | When Key 2 approved |

## GL Accounts (`gl_accounts`)

| Link Name | Display Name | Type | Notes |
|-----------|-------------|------|-------|
| gl_code | GL Code | text |  |
| account_name | Account Name | text |  |
| expense_category | Expense Category | picklist |  |
| receipt_required | Receipt Required | checkbox | default: false |
| SARS_Provision | SARS Provision | help_text |  |
| Active | Active | checkbox | default: true |

## Notes

- Field link names are case-sensitive in Deluge
- `action_1` (not `action`) is the link name for the Action field in Approval_History
- `Employee_Name1` is the composite name field (access subfields via `.first_name`, `.last_name`)
- Private fields (Department_Shadow, Client_Shadow, Parent_Claim_ID) are hidden from end users
