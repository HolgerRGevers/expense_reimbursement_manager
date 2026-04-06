# Expense Reimbursement Manager

A governance-first expense reimbursement system built on **Zoho Creator** for the Both& practical assessment.

## Purpose

Digitises the expense claim lifecycle -- submission, validation, multi-tier approval, GL code mapping, and audit trail -- with enforceable controls aligned to South African governance and tax requirements.

## Governance Framework

- **King IV**: Principles 1 (ethical leadership / segregation of duties), 7 (delegation of authority tiers), 11 (risk-based routing), 12 (technology governance), 13 (compliance), 15 (combined assurance via audit trail)
- **SARS**: S11(a) substantiation (mandatory receipts + business purpose), VAT invoice thresholds (R50/R5,000), 5-year retention per Tax Administration Act S29
- **Segregation of Duties**: Self-approval prevention -- if submitter holds an approver role, system bypasses that tier automatically with audit trail evidence

## Architecture

- **Platform**: Zoho Creator (Free Trial -> Standard plan)
- **Scripting**: Deluge (event-driven workflows)
- **Data model**: 6 forms -- Departments, Clients, GL_Accounts, Approval_Thresholds (config), Expense_Claim (transaction), Approval_History (audit)
- **Approval**: Two separate approval processes coordinated via Status field (LM -> HoD conditional escalation)

## Repository Role

This repo is a **version archive and documentation hub**. Zoho Creator has no structural deployment API -- code is applied manually in the Creator UI. The repo provides:

1. Version-controlled Deluge scripts (`.dg` files)
2. Architecture and compliance documentation
3. Seed data for lookup/config tables
4. Build guide for reproducing the application from scratch
5. `.ds` export snapshots (disaster recovery)

## Build Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1-2 | Forms, lookups, seed data | Complete |
| 3 | Approval process (LM + HoD) | In Progress |
| 4 | Reports + conditional formatting | Pending |
| 5 | Dashboards + KPI pages | Partial (Employee Dashboard built) |
| 6 | Testing + demo prep | Pending |

## Versioning Convention

`v0.0` (Launchpad Generated) -> `v0.1` (Scaffold Remediation) -> `v1.0` (Demo Ready)

## Key Documents

- [Build Sequence](docs/build-guide/build-sequence.md) -- 19-step dependency-ordered plan
- [Data Model](docs/architecture/data-model.md) -- Form specs + ERD
- [State Machine](docs/architecture/state-machine.md) -- Claim lifecycle
- [Test Scenarios](docs/testing/test-scenarios.md) -- 5 end-to-end cases
