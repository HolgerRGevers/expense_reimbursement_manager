# Data Model

## Forms Overview

6 forms total: 4 config/lookup + 1 transaction + 1 audit.

## Form 1: Departments (Lookup)

| Field Link Name | Display Name | Type | Notes |
|----------------|--------------|------|-------|
| department_id | Department ID | Autonumber | Start index 1 |
| name | Name | Text | |
| is_active | Active | Checkbox | Default: true |

## Form 2: Clients (Lookup)

| Field Link Name | Display Name | Type | Notes |
|----------------|--------------|------|-------|
| client_id | Client ID | Autonumber | Start index 1 |
| name | Name | Text | |
| is_active | Active | Checkbox | Default: true |

## Form 3: GL_Accounts (Lookup)

| Field Link Name | Display Name | Type | Notes |
|----------------|--------------|------|-------|
| gl_code | GL Code | Text | |
| account_name | Account Name | Text | |
| expense_category | Expense Category | Picklist | Travel, Accommodation, Meals & Entertainment, Office Supplies, Communication, Professional Services, Other |
| receipt_required | Receipt Required | Checkbox | Default: false |
| SARS_Provision | SARS Provision | Text | Help: "Maps each GL code to SARS deduction provision" |
| Active | Active | Checkbox | Default: true |

## Form 4: Approval_Thresholds (Config)

| Field Link Name | Display Name | Type | Notes |
|----------------|--------------|------|-------|
| tier_name | Tier Name | Text | |
| max_amount_zar | Max Amount ZAR | Currency (ZAR) | |
| approver_role | Approver Role | Text | |
| Active | Active | Checkbox | Default: true |

## Form 5: Expense_Claims (Transaction)

| Field Link Name | Display Name | Type | Notes |
|----------------|--------------|------|-------|
| Employee_Name1 | Employee Name | Name | Mandatory. Prefix/suffix hidden. Personal data. |
| Email | Email | Picklist (users module) | Mandatory. Display: emailid. Personal data. |
| Submission_Date | Submission Date | Datetime | Mandatory. Auto-set on submit. |
| claim_id | Claim ID | Autonumber | Start index 1 |
| department | Department | List (departments.ID) | Display: name |
| Claim_Reference | Claim Reference | Text | Mandatory. Auto-generated "EXP-0001" |
| client | Client | List (clients.ID) | Display: name. Allow new entries. |
| Expense_Date | Expense Date | Date | |
| Department_Shadow | Department Shadow | Text | Private (hidden). Denormalized dept name. |
| category | Category | Picklist | Travel, Accommodation, Meals & Entertainment, Office Supplies, Communication, Professional Services, Other |
| Client_Shadow | Client Shadow | Text | Private (hidden). Denormalized client name. |
| amount_zar | Amount ZAR | Currency (ZAR) | |
| Supporting_Documents | Supporting Documents | File Upload | Mandatory. Max 10 files. |
| description | Description | Textarea | 100px height |
| status | Status | Picklist | Draft, Submitted, Pending LM Approval, Pending HoD Approval, Approved, Rejected, Resubmitted |
| Rejection_Reason | Rejection Reason | Textarea | 100px height |
| Version | Version | Number | Default: 1 |
| Parent_Claim_ID | Parent Claim ID | Picklist (expense_claims.ID) | Private. Display: claim_id |
| gl_code | GL Code | List (gl_accounts.ID) | Display: gl_code. Allow new entries. |

## Form 6: Approval_History (Audit)

| Field Link Name | Display Name | Type | Notes |
|----------------|--------------|------|-------|
| claim | Claim | List (expense_claims.ID) | Display: claim_id. Allow new entries. |
| action_1 | Action | Picklist | Submitted, Approved (LM), Approved (HoD), Rejected, Escalated (SLA Breach), Resubmitted |
| actor | Actor | Text | |
| timestamp | Timestamp | Datetime | Display: hh:mm:ss |
| comments | Comments | Textarea | 100px height |

## Entity Relationship Diagram

```
+------------------+       +------------------+       +-------------------+
|   Departments    |       |     Clients      |       |   GL_Accounts     |
|------------------|       |------------------|       |-------------------|
| department_id PK |       | client_id PK     |       | gl_code           |
| name             |       | name             |       | account_name      |
| is_active        |       | is_active        |       | expense_category  |
+--------+---------+       +--------+---------+       | receipt_required  |
         |                          |                  | SARS_Provision    |
         | 1:N                      | 1:N              | Active            |
         |                          |                  +--------+----------+
+--------+--------------------------+--------------------------+|
|                     Expense_Claims                            |
|---------------------------------------------------------------|
| claim_id PK (autonumber)                                     |
| Employee_Name1, Email, Submission_Date                        |
| department FK -> Departments                                  |
| client FK -> Clients                                          |
| Claim_Reference, Expense_Date, category                       |
| amount_zar, Supporting_Documents, description                 |
| status, Rejection_Reason, Version                             |
| gl_code FK -> GL_Accounts                                     |
| Parent_Claim_ID FK -> Expense_Claims (self-ref)              |
| Department_Shadow, Client_Shadow (denormalized)               |
+----------------------------+----------------------------------+
                             |
                             | 1:N
                             |
              +--------------+----------------+
              |       Approval_History        |
              |-------------------------------|
              | claim FK -> Expense_Claims    |
              | action_1                      |
              | actor                         |
              | timestamp                     |
              | comments                      |
              +-------------------------------+

+---------------------+
| Approval_Thresholds |
|---------------------|
| tier_name           |
| max_amount_zar      |     (Config table - referenced
| approver_role       |      by approval scripts at runtime)
| Active              |
+---------------------+
```

## Reports (from .ds export)

| Report Name | Type | Source | Key Features |
|-------------|------|--------|-------------|
| All Expense Claims | List | expense_claims | Amount aggregates, category conditional formatting |
| Categories | Kanban | expense_claims | Grouped by category |
| All GL Accounts | List | gl_accounts | Category conditional formatting |
| Expense Categories | Kanban | gl_accounts | Grouped by expense_category |
| All Approval Histories | List | approval_history | Action conditional formatting |
| Actions | Kanban | approval_history | Grouped by action_1 |
| All Approval Thresholds | List | approval_thresholds | Amount aggregates |
| All Clients | List | clients | Standard CRUD |
| All Departments | List | departments | Standard CRUD |
| Audit Trail | List | approval_history | Grouped by action + actor, sorted by timestamp |
| Pending Approvals Manager | List | expense_claims | Filtered: Pending LM or HoD. Grouped by status/dept/employee/category |
| My Claims | List | expense_claims | Filtered: Added_User == zoho.loginuser. Status conditional formatting |
| Expense Summary | Summary | expense_claims | Dashboard layout |
