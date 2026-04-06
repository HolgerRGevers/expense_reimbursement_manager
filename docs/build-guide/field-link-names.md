# Field Link Names

## Overview

Verified field link name mapping extracted from the `.ds` export. These are the actual Deluge-accessible field identifiers used in scripts.

## Expense_Claims

| Link Name | Display Name | Type |
|-----------|-------------|------|
| Employee_Name1 | Employee Name | Name (first_name, last_name) |
| Email | Email | Picklist (users module) |
| Submission_Date | Submission Date | Datetime |
| claim_id | Claim ID | Autonumber |
| department | Department | List -> departments.ID |
| Claim_Reference | Claim Reference | Text |
| client | Client | List -> clients.ID |
| Expense_Date | Expense Date | Date |
| Department_Shadow | Department Shadow | Text (private) |
| category | Category | Picklist |
| Client_Shadow | Client Shadow | Text (private) |
| amount_zar | Amount ZAR | Currency (ZAR) |
| Supporting_Documents | Supporting Documents | File Upload |
| description | Description | Textarea |
| status | Status | Picklist |
| Rejection_Reason | Rejection Reason | Textarea |
| Version | Version | Number |
| Parent_Claim_ID | Parent Claim ID | Picklist -> expense_claims.ID |
| gl_code | GL Code | List -> gl_accounts.ID |

## Approval_History

| Link Name | Display Name | Type |
|-----------|-------------|------|
| claim | Claim | List -> expense_claims.ID |
| action_1 | Action | Picklist |
| actor | Actor | Text |
| timestamp | Timestamp | Datetime |
| comments | Comments | Textarea |

## Approval_Thresholds

| Link Name | Display Name | Type |
|-----------|-------------|------|
| tier_name | Tier Name | Text |
| max_amount_zar | Max Amount ZAR | Currency (ZAR) |
| approver_role | Approver Role | Text |
| Active | Active | Checkbox |

## GL_Accounts

| Link Name | Display Name | Type |
|-----------|-------------|------|
| gl_code | GL Code | Text |
| account_name | Account Name | Text |
| expense_category | Expense Category | Picklist |
| receipt_required | Receipt Required | Checkbox |
| SARS_Provision | SARS Provision | Text |
| Active | Active | Checkbox |

## Departments

| Link Name | Display Name | Type |
|-----------|-------------|------|
| department_id | Department ID | Autonumber |
| name | Name | Text |
| is_active | Active | Checkbox |

## Clients

| Link Name | Display Name | Type |
|-----------|-------------|------|
| client_id | Client ID | Autonumber |
| name | Name | Text |
| is_active | Active | Checkbox |

## Notes

- Field link names are case-sensitive in Deluge
- `action_1` (not `action`) is the link name for the Action field in Approval_History
- `Employee_Name1` is the composite name field (access subfields via `.first_name`, `.last_name`)
- Private fields (Department_Shadow, Client_Shadow, Parent_Claim_ID) are hidden from end users
