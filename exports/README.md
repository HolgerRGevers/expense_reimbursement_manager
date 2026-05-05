# Exports

This folder contains the **canonical deployment file** for the Zoho Creator application.

## Current Version

**[`Expense_Reimbursement_Management-stage.ds`](./Expense_Reimbursement_Management-stage.ds)** -- Import this file into Zoho Creator to deploy the app.

## Historic Version

**[`Expense_Reimbursement_Management-stage.v0.4.0-16067d6.historic.ds`](./Expense_Reimbursement_Management-stage.v0.4.0-16067d6.historic.ds)** -- v0.4.0 snapshot (commit `16067d6`), the last verified-good baseline two `.ds` steps before v0.5.0 first broke Creator import. Reference-only; do not deploy.

## How to deploy

1. Go to Zoho Creator > Settings > Import Application
2. Upload `Expense_Reimbursement_Management-stage.ds`
3. Review the import preview
4. Confirm import

## What's included

- 6 forms with 47+ fields and field descriptions
- 12 embedded Deluge scripts (workflows, approval process, scheduled tasks)
- 10 reports with conditional formatting
- 3 dashboard pages (Dashboard, Employee Dashboard, Management Dashboard)
- Role hierarchy and share_settings (CEO > HoD > LM > Employee)
- All v0.4.0 governance gap fixes (15 of 16 resolved)

## Other files

- `ERM.accdb` -- Microsoft Access database with tables, relationships, and seed data. Alternative import path for data + structure (no scripts/workflows).
