# Expense Reimbursement Manager

A governance-first expense reimbursement system built on **Zoho Creator** for the Both& practical assessment. Digitises the full expense claim lifecycle -- submission, validation, multi-tier approval, GL code mapping, and audit trail -- with enforceable controls aligned to South African governance and tax requirements.

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Governance Framework](#governance-framework)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Deluge Scripts](#deluge-scripts)
- [Data Model](#data-model)
- [Approval Flow](#approval-flow)
- [Tooling](#tooling)
- [Getting Started](#getting-started)
- [Build Status](#build-status)
- [Key Documents](#key-documents)
- [License](#license)

## Why This Exists

Zoho Creator has **no structural deployment API** -- code cannot be pushed to Creator programmatically. This repository serves as:

1. **Version archive** -- All Deluge scripts tracked in Git with full history
2. **Documentation hub** -- Architecture, compliance, and build documentation
3. **Disaster recovery** -- `.ds` export snapshots that can rebuild the entire app
4. **Seed data source of truth** -- JSON files for all lookup/config tables
5. **Static analysis** -- A Python linter that validates Deluge scripts before they are pasted into Creator

Code is applied manually in the Creator UI. The one exception is Widgets (built via the `zet` CLI), which support external development.

## Governance Framework

This is not optional flavour -- governance drives architectural decisions throughout the system.

### King IV Principles

| Principle | Description | System Control |
|-----------|-------------|----------------|
| P1 | Ethical leadership | Self-approval prevention -- LM submitters bypass their own approval tier |
| P7 | Delegation of authority | Two-tier threshold-based approval (LM R999.99 / HoD R10,000) |
| P11 | Risk management | Risk-based routing -- higher amounts escalate to senior authority |
| P12 | Technology governance | Automated workflows, configurable thresholds, audit logging |
| P13 | Compliance | SARS S11(a) validation (receipts, 90-day window, positive amounts) |
| P15 | Combined assurance | Comprehensive audit trail in Approval_History with every state change |

### SARS Compliance

- **S11(a)** -- Mandatory receipt upload and business purpose for every claim
- **VAT thresholds** -- R50 (simplified invoice) / R5,000 (full tax invoice)
- **Retention** -- 5-year record retention per Tax Administration Act S29
- **S8(1)(a)** -- Travel allowance provisions for long-distance travel

### Segregation of Duties

If a submitter holds the Line Manager role, the system automatically bypasses that approval tier and routes directly to the Head of Department, with full audit trail evidence of the bypass.

## Architecture

```
Platform:    Zoho Creator (Free Trial -> Standard plan)
Scripting:   Deluge (event-driven, server-side)
Timezone:    Africa/Johannesburg
Data model:  6 forms (4 config/lookup + 1 transaction + 1 audit)
Approval:    Two separate processes coordinated via Status field
Email:       Zoho Mail integration via sendmail
```

### Component Map

```
+-----------------------------+
|      Zoho Creator App       |
|-----------------------------|
|  FORMS (6)                  |
|  - Departments (lookup)     |
|  - Clients (lookup)         |
|  - GL_Accounts (lookup)     |
|  - Approval_Thresholds      |
|  - Expense_Claims (txn)     |
|  - Approval_History (audit) |
|-----------------------------|
|  WORKFLOWS (6)              |
|  - On Validate (hard stops) |
|  - On Success (routing)     |
|  - On Edit (resubmission)   |
|  - On Load (auto-populate)  |
|  - Shadow field fill        |
|  - Claim ref generation     |
|-----------------------------|
|  APPROVAL PROCESSES (2)     |
|  - Line Manager (Stage 1)   |
|  - HoD (Stage 2)            |
|-----------------------------|
|  SCHEDULED TASKS (1)        |
|  - SLA Enforcement (daily)  |
|-----------------------------|
|  REPORTS (12)               |
|  - My Claims                |
|  - Pending Approvals Mgr    |
|  - Audit Trail              |
|  - Expense Summary          |
|  + 8 standard CRUD reports  |
|-----------------------------|
|  PAGES (2)                  |
|  - Dashboard                |
|  - Employee Dashboard       |
+-----------------------------+
```

## Repository Structure

```
expense_reimbursement_manager/
|-- README.md                          # This file
|-- LICENSE                            # MIT
|-- CHANGELOG.md                       # Keep a Changelog format
|-- CLAUDE.md                          # AI assistant project rules + Deluge quick-ref
|-- .gitignore
|
|-- src/deluge/                        # All Deluge scripts (.dg files)
|   |-- form-workflows/               # On Validate, On Success, On Edit, On Load
|   |-- approval-scripts/             # LM and HoD approve/reject handlers
|   +-- scheduled/                    # SLA enforcement daily job
|
|-- docs/
|   |-- architecture/                 # Data model, state machine, approval routing
|   |-- compliance/                   # King IV mapping, SARS requirements
|   |-- build-guide/                  # 19-step build sequence, field link names
|   +-- testing/                      # Test scenarios, demo script
|
|-- config/
|   |-- seed-data/                    # JSON source of truth for lookup tables
|   |-- roles-and-permissions.md      # Role matrix + field-level permissions
|   +-- deluge-reference.md           # Comprehensive Deluge language reference
|
|-- tools/
|   |-- lint_deluge.py                # Static analysis linter (18 rules)
|   +-- build_deluge_db.py           # Builds SQLite language DB for the linter
|
|-- tests/                            # Linter test fixtures
|-- exports/                          # .ds snapshots from Creator (disaster recovery)
+-- enhancements/                     # Future specs (Two-Key auth, OmegaScript, roadmap)
```

## Deluge Scripts

10 scripts covering the full claim lifecycle, organised by Creator UI location:

### Form Workflows (`src/deluge/form-workflows/`)

| Script | Trigger | Purpose |
|--------|---------|---------|
| `expense_claim.on_validate.dg` | Before save | Hard-stop validation: future dates, 90-day window, positive amount, mandatory receipt |
| `expense_claim.on_success.dg` | After save | Self-approval prevention, routing, audit trail, LM notification |
| `expense_claim.on_edit.dg` | On edit | Resubmission handler: version increment, status reset, self-approval re-check |
| `expense_claim.on_load.auto_populate.dg` | Form load | Auto-populates Employee_Name and Email from logged-in user |
| `expense_claim.on_success.generate_ref.dg` | After save | Generates claim reference (EXP-0001 format) |
| `expense_claim.on_success.fill_shadows.dg` | After save | Populates denormalized Department_Shadow and Client_Shadow fields |

### Approval Scripts (`src/deluge/approval-scripts/`)

| Script | Purpose |
|--------|---------|
| `lm_approval.on_approve.dg` | Threshold-based routing: under R999.99 = final approval + GL code; over = escalate to HoD |
| `lm_approval.on_reject.dg` | Sets Rejected status, logs audit trail, notifies employee |
| `hod_approval.on_approve.dg` | Final approval, GL code auto-population, audit trail |
| `hod_approval.on_reject.dg` | Sets Rejected status, logs audit trail, notifies employee |

### Scheduled (`src/deluge/scheduled/`)

| Script | Purpose |
|--------|---------|
| `sla_enforcement_daily.dg` | 2-day reminder to LM, 3-day auto-escalation to HoD (v2.1 targets) |

## Data Model

6 forms with explicit relationships:

```
Departments ----+
                |  1:N
Clients --------+-------> Expense_Claims -------> Approval_History
                |         (transaction)           (audit trail)
GL_Accounts ----+
                          Approval_Thresholds
                          (config, queried at runtime)
```

### Expense_Claims (20 fields)

Core fields: Employee_Name1, Email, claim_id, Claim_Reference, department, client, category, Expense_Date, amount_zar, Supporting_Documents, description, status, gl_code, Version, Rejection_Reason

Status values: `Draft` | `Submitted` | `Pending LM Approval` | `Pending HoD Approval` | `Approved` | `Rejected` | `Resubmitted`

Full field specifications: [docs/architecture/data-model.md](docs/architecture/data-model.md)

## Approval Flow

```
Employee submits
       |
  [On Validate: hard stops]
       |
  [On Success: route]
       |
       +--[Employee is LM?]--YES--> Pending HoD Approval (self-approval bypass)
       |
       NO
       |
   Pending LM Approval
       |
       +--[LM Approves]
       |      |
       |      +--[<= R999.99]--> Approved (GL code populated)
       |      |
       |      +--[> R999.99]---> Pending HoD Approval
       |
       +--[LM Rejects]---------> Rejected (can resubmit)
       |
       +--[3 days no action]---> Pending HoD Approval (SLA auto-escalation)

   Pending HoD Approval
       |
       +--[HoD Approves]-------> Approved (GL code populated)
       |
       +--[HoD Rejects]--------> Rejected (can resubmit)
```

Every state transition is logged in Approval_History with actor, timestamp, and comments.

## Tooling

### Deluge Linter (`tools/lint_deluge.py`)

Static analysis tool with 18 rules that validates `.dg` files before they are applied in Creator:

```bash
python tools/lint_deluge.py src/deluge/           # lint all scripts
python tools/lint_deluge.py path/to/file.dg       # lint one file
```

Exit codes: `0` = clean, `1` = warnings only, `2` = errors found.

#### Rules

| Code | Severity | What it catches |
|------|----------|-----------------|
| DG001 | ERROR | Banned functions (`lpad`, `rpad`) |
| DG002 | ERROR | Banned variable (`zoho.loginuserrole`) |
| DG003 | ERROR | `hoursBetween` in scheduled scripts (Free Trial limitation) |
| DG004 | ERROR | Unknown `input.FieldName` reference |
| DG005 | ERROR | Query result used without null guard |
| DG006 | ERROR | Missing `Added_User` in approval_history insert |
| DG007 | ERROR | Wrong `Added_User` value |
| DG008 | ERROR | Single quotes for text strings |
| DG009 | ERROR | `:` instead of `=` in insert blocks |
| DG010 | ERROR | Missing required sendmail/invokeUrl params |
| DG011 | WARN | Unknown status value |
| DG012 | WARN | Unknown action_1 value in audit trail |
| DG013 | WARN | Mixed `&&`/`||` without parentheses (Creator precedence) |
| DG014 | WARN | Threshold fallback not 999.99 |
| DG015 | WARN | Hardcoded demo/placeholder email |
| DG016 | INFO | Any hardcoded email address |
| DG017 | ERROR | Reserved word used as variable name |
| DG018 | WARN | Unknown Zoho system variable |

### Language Database (`tools/build_deluge_db.py`)

Builds a SQLite database (`deluge_lang.db`) with all Deluge language data for the linter:

```bash
python tools/build_deluge_db.py           # build (or update)
python tools/build_deluge_db.py --force   # recreate from scratch
```

Contains 232 built-in functions, 42 form fields, 20 operators, 11 Zoho system variables, 15 error message patterns, and all valid status/action values.

## Getting Started

### Prerequisites

- Python 3.8+ (for the linter)
- Git
- Access to a Zoho Creator account (Free Trial or Standard)

### Setup

```bash
git clone https://github.com/holgergevers-hub/expense_reimbursement_manager.git
cd expense_reimbursement_manager

# Build the linter database
python tools/build_deluge_db.py

# Verify linter works
python tools/lint_deluge.py src/deluge/
```

### Applying Scripts to Creator

1. Open the target form/workflow in Zoho Creator
2. Copy the `.dg` file content from this repo
3. Paste into the Creator script editor
4. Save and test

### Seed Data

Import the JSON files from `config/seed-data/` into their respective Creator forms:
- `departments.json` -- 5 departments (Sales, Customer Service, Finance, Operations, IT)
- `clients.json` -- 5 clients (MTN, Vodacom, Cell C, Telkom, Internal)
- `gl_accounts.json` -- 7 GL codes with SARS provisions
- `approval_thresholds.json` -- 2 tiers (LM: R999.99, HoD: R10,000)

## Build Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1-2 | Forms, lookups, seed data | Complete |
| 3 | Approval process (LM + HoD) | In Progress |
| 4 | Reports + conditional formatting | Pending |
| 5 | Dashboards + KPI pages | Partial (Employee Dashboard built) |
| 6 | Testing + demo prep | Pending |

## Versioning

`v0.0` (Launchpad Generated) -> `v0.1` (Scaffold Remediation) -> `v1.0` (Demo Ready)

Current: **v0.2.1** -- Linter refactored with SQLite-backed lookups and 18 rules.

## Key Documents

| Document | Description |
|----------|-------------|
| [Data Model](docs/architecture/data-model.md) | Full form specs, field types, ERD |
| [State Machine](docs/architecture/state-machine.md) | Claim lifecycle states and transitions |
| [Approval Routing](docs/architecture/approval-routing.md) | Threshold logic, self-approval bypass, SLA |
| [System Overview](docs/architecture/system-overview.md) | Architecture narrative + component map |
| [King IV Mapping](docs/compliance/king-iv-mapping.md) | Governance principles mapped to controls |
| [SARS Requirements](docs/compliance/sars-requirements.md) | S11(a), VAT, retention rules |
| [Build Sequence](docs/build-guide/build-sequence.md) | 19-step dependency-ordered build plan |
| [Remediation Plan](docs/build-guide/remediation-plan.md) | Fix-Forward v2.1 (Steps 13-22) |
| [Field Link Names](docs/build-guide/field-link-names.md) | Verified .ds field name mapping |
| [Test Scenarios](docs/testing/test-scenarios.md) | 5 end-to-end test cases |
| [Demo Script](docs/testing/demo-script.md) | 3-act demo walkthrough |
| [Roles & Permissions](config/roles-and-permissions.md) | Role matrix + field-level access |
| [Deluge Reference](config/deluge-reference.md) | Comprehensive language reference |
| [Changelog](CHANGELOG.md) | All notable changes |

## License

[MIT](LICENSE)
