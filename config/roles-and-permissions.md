# Roles and Permissions

## Role Hierarchy

```
CEO
 +-- Finance Director  (Key 2 — Two-Key dual approval)
 +-- Head of Department (HoD)
      +-- Line Manager
           +-- Employee
```

Hierarchy applied to: approval_history, expense_claims

Note: Finance Director is a **peer** of HoD under CEO, not a subordinate. This ensures the two keys are structurally independent (King IV P7, COSO segregation of duties).

## Role Matrix

| Role | Can Add | Can View | Can Approve | Notes |
|------|---------|----------|-------------|-------|
| Employee | Expense_Claim | Own claims only | No | Base role for all staff |
| Line Manager | Expense_Claim | Pending LM claims + own | Stage 1 | Self-approval prevention applies |
| Head of Dept | Expense_Claim | Pending HoD claims + all | Stage 2 / Key 1 | Final authority (or Key 1 for dual-approval claims) |
| Finance Director | -- | Pending Second Key claims + all | Key 2 | Two-Key second approver. Cannot be same person as Key 1 |
| Finance Accountant | -- | All claims + GL accounts | No | Full GL account CRUD, export |
| System Administrator | All forms | All records | -- | Full CRUD + import/export |
| Developer | -- | -- | -- | Development access |

## Customer Portal Roles

| Role | Access |
|------|--------|
| Client Representative | View clients, expense_claims, approval_history |
| Vendor | View clients, expense_claims, approval_history |
| Customer | Default portal profile |

## Field Permissions

| Field | Employee | Line Manager | HoD | Finance Director | Finance/Admin |
|-------|----------|-------------|-----|-----------------|---------------|
| Status | Read-only | Read-only | Read-only | Read-only | Editable |
| GL_Code | Hidden | Read-only | Read-only | Read-only | Editable |
| Rejection_Reason | Read-only | Editable | Editable | Editable | Editable |
| Amount | Editable (on create) | Read-only | Read-only | Read-only | Read-only |
| Key_1_Approver | Hidden | Hidden | Hidden | Read-only | Hidden (private) |
| Key_1_Timestamp | Hidden | Hidden | Hidden | Read-only | Hidden (private) |
| Requires_Dual_Approval | Hidden | Hidden | Hidden | Read-only | Hidden (private) |
| Department_Shadow | Hidden | Hidden | Hidden | Hidden | Hidden (private) |
| Client_Shadow | Hidden | Hidden | Hidden | Hidden | Hidden (private) |
| Parent_Claim_ID | Hidden | Hidden | Hidden | Hidden | Hidden (private) |

## Profile Details (from .ds export)

### Employee Profile
- Expense Claims: View/Edit/Delete own records
- Lookup tables (Departments, Clients, GL Accounts, Thresholds): View only
- Approval History: View only

### Line Manager Profile
- Expense Claims: View/Edit/Delete (filtered by pending LM status)
- Approval Thresholds: View only
- GL Accounts, Clients: View only
- Departments: View only
- Approval History: Full access

### HoD Profile
- Expense Claims: View/Edit/Delete (all pending + escalated)
- All lookup tables: View only
- Approval History: Full access

### Finance Accountant Profile
- GL Accounts: Full CRUD + export
- Expense Claims: View/Edit/Delete + export
- Other tables: View only

### System Administrator Profile
- All modules: Full CRUD + import/export
- Create, Viewall, Modifyall permissions across all forms

## Dummy Test Users

Use Gmail +alias trick -- all land in one inbox.

| Role | Email |
|------|-------|
| Employee 1 | youremail+employee1@gmail.com |
| Employee 2 | youremail+employee2@gmail.com |
| Line Manager | youremail+lm@gmail.com |
| Head of Department | youremail+hod@gmail.com |
| Finance Director | youremail+fd@gmail.com |
