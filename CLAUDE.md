# Expense Reimbursement Manager — Project Memory

## What this repo is
Version archive and documentation hub for a Zoho Creator expense reimbursement app. 
No CI/CD — Creator has no structural deployment API. Code is applied manually in Creator UI.

## Tech stack
- **Platform**: Zoho Creator (Free Trial → Standard)
- **Scripting**: Deluge (event-driven, not general-purpose)
- **File convention**: `.dg` = Deluge script files (plain text)

## Key Deluge rules (always follow these)
- `zoho.loginuserrole` does NOT exist — use `thisapp.permissions.isUserInRole("Role Name")`
- `lpad()` does not exist in Deluge
- `hoursBetween` not available on Free Trial daily schedules — use `daysBetween`
- All `insert into approval_history` blocks MUST include `Added_User = zoho.loginuser`
- Threshold fallback value is `999.99` (matches seed data), not `1000`
- GL query always needs null guard: `glRec != null && glRec.count() > 0`
- Strings use double quotes only (never single quotes)
- `ifnull(value, fallback)` for every query result

## Repo structure convention
- `src/deluge/` — scripts organised by Creator UI location (form-workflows, approval-scripts, scheduled)
- `docs/` — architecture, compliance, build-guide, testing
- `config/seed-data/` — JSON source of truth for lookup/config tables
- `exports/` — manual .ds snapshots from Creator

## Governance context
South African compliance: King IV principles, SARS S11(a), segregation of duties.
This is not optional flavour — it drives architectural decisions (self-approval prevention, audit trail writes, configurable thresholds).

## Version convention
v0.0 (Launchpad Generated) → v0.1 (Scaffold Remediation) → v1.0 (Demo Ready)

