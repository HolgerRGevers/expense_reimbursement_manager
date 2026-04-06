# System Overview

## Architecture Narrative

The Expense Reimbursement Manager is a Zoho Creator application that digitises the expense claim lifecycle for a South African consultancy. It enforces governance controls through event-driven Deluge scripting, configurable approval workflows, and a comprehensive audit trail.

## Component Map

```
+-----------------------------+
|      Zoho Creator App       |
|-----------------------------|
|  FORMS                      |
|  - Departments (lookup)     |
|  - Clients (lookup)         |
|  - GL_Accounts (lookup)     |
|  - Approval_Thresholds      |
|  - Expense_Claims (txn)     |
|  - Approval_History (audit) |
|-----------------------------|
|  WORKFLOWS                  |
|  - On Validate (hard stops) |
|  - On Success (routing)     |
|  - On Edit (resubmission)   |
|  - On Load (auto-populate)  |
|  - Shadow field fill        |
|  - Claim ref generation     |
|-----------------------------|
|  APPROVAL PROCESSES         |
|  - Line Manager (Stage 1)   |
|  - HoD (Stage 2)            |
|-----------------------------|
|  SCHEDULED TASKS            |
|  - SLA Enforcement (daily)  |
|-----------------------------|
|  REPORTS                    |
|  - My Claims                |
|  - Pending Approvals Mgr    |
|  - Audit Trail              |
|  - Expense Summary          |
|  - Standard CRUD reports    |
|-----------------------------|
|  PAGES (3)                  |
|  - Dashboard                |
|  - Employee Dashboard       |
|  - Management Dashboard     |
+-----------------------------+
```

## Technology Stack

- **Platform**: Zoho Creator (Free Trial, targeting Standard plan)
- **Scripting**: Deluge (event-driven, server-side)
- **Email**: Zoho Mail integration via sendmail
- **Future**: Zoho Books integration, zet CLI widgets

## Deployment Model

No CI/CD pipeline -- Zoho Creator has no structural deployment API. Code is maintained in this Git repository and applied manually in the Creator UI. The `.ds` export in `exports/` provides disaster recovery snapshots.
