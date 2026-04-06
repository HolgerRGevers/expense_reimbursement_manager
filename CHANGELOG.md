# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.4.0] - 2026-04-06

### Added
- Governance gap remediation: 12 of 16 gaps implemented in .ds export
  - G-03: Fixed approval trigger from Parent_Claim_ID.status to status
  - G-04: Added Tier_Order field to Approval_Thresholds form
  - G-06: Added VAT_Invoice_Type picklist + On Validate enforcement (SARS R5,000 threshold)
  - G-09: Added Retention_Expiry_Date field (SARS S29 5-year retention)
  - G-10: Added POPIA_Consent checkbox with privacy notice + On Validate enforcement
  - G-11: Fixed SLA Added_User from zoho.loginuser to zoho.adminuserid
  - G-15: Added duplicate claim detection to On Validate (COSO fraud risk)
  - G-16: Added Risk_Level picklist to GL_Accounts (ISO 37001 anti-bribery)
- New fields in seed data: Tier_Order (approval_thresholds), Risk_Level (gl_accounts)
- On Validate script expanded from 5 to 8 validation checks

### Changed
- Linter DG007 rule now accepts zoho.adminuserid for scheduled task scripts
- Linter DB expanded to 47 form fields (was 42)
- expense_claim.on_validate.dg updated to v3.0 (Governance Gap Remediation)

## [0.3.0] - 2026-04-06

### Added
- `.ds` export parser (`tools/parse_ds_export.py`) — extracts forms, fields, and embedded scripts from Creator exports
  - Auto-generates `docs/build-guide/field-link-names.md` from .ds metadata
  - Extracts embedded Deluge workflow scripts to standalone .dg files
  - Outputs field data as JSON for database integration
- Script scaffolder (`tools/scaffold_deluge.py`) — generates .dg boilerplate from manifest
  - Pre-fills: header, audit trail blocks, sendmail blocks, self-approval checks, GL lookups, threshold patterns
  - Reads from `config/deluge-manifest.yaml` for script metadata
- Linter auto-fix mode (`--fix` flag) — automatically repairs DG006, DG007, DG008
  - Adds missing `Added_User = zoho.loginuser` to approval_history inserts
  - Corrects wrong Added_User values
  - Converts single-quoted text strings to double quotes
- Configuration files:
  - `config/deluge-manifest.yaml` — script metadata for scaffolder
  - `config/email-templates.yaml` — centralised email template definitions

## [0.2.1] - 2026-04-06

### Changed
- Rewrote linter with Pylance-compliant type annotations (`from __future__ import annotations`, enums, `str | None`)
- Refactored linter to use SQLite-backed lookups instead of hardcoded constants
- Added `tools/build_deluge_db.py` — builds `deluge_lang.db` with 232 functions, 42 form fields, 11 zoho variables, 20 operators, 15 error messages, 11 data types, banned patterns, and all valid values

### Added
- DG017: Reserved word used as variable name (true, false, null, void, return)
- DG018: Unknown zoho system variable validation (zoho.X against known set)
- invokeUrl block extraction and required-param validation (DG010)
- SQLite database schema with 11 tables for Deluge language data

## [0.2.0] - 2026-04-06

### Added
- Deluge linter (`tools/lint_deluge.py`) — 16 static analysis rules for .dg files
  - 10 ERROR rules: banned functions, field validation, null guards, audit trail, syntax
  - 5 WARN rules: status/action values, operator precedence, thresholds, demo emails
  - 1 INFO rule: hardcoded email detection
- Test fixtures (`tests/lint_test_bad.dg`, `tests/scheduled/lint_test_dg003.dg`)
- Linter usage instructions in CLAUDE.md

## [0.1.1] - 2026-04-06

### Added
- Comprehensive Deluge language reference (`config/deluge-reference.md`) extracted from official Zoho docs: data types, operators, variables, control flow, system variables, 200+ built-in functions, tasks, record operations, error messages, Creator-specific features
- Deluge quick-reference section in CLAUDE.md for inline context
- OmegaScript vision summary (`enhancements/omega-script-vision.md`)

## [0.1.0] - 2026-04-06

### Added
- Repository scaffold with documentation structure
- All v2.1 Deluge scripts (10 files): On Validate, On Success, On Edit, LM Approve/Reject, HoD Approve/Reject, SLA Enforcement, Generate Claim Reference, Auto-Populate Employee, Fill Shadow Fields
- Seed data JSON for Departments, Clients, GL_Accounts, Approval_Thresholds
- Architecture documentation: data model, state machine, approval routing, system overview
- Compliance documentation: King IV mapping, SARS requirements, Delegation of Authority
- Build guide: 19-step sequence, remediation plan v2.1, field link name mapping
- Test scenarios and demo script
- .ds export snapshot in exports/

### Fixed
- Corrected `zoho.loginuserrole` to `thisapp.permissions.isUserInRole()` across all scripts
- Corrected SLA timer from `hoursBetween` to `daysBetween` for Free Trial daily schedule
- Corrected threshold fallback from 1000 to 999.99 to match seed data
- Added `Added_User = zoho.loginuser` to all `insert into approval_history` blocks
- Added null guard on GL query: `glRec != null && glRec.count() > 0`

## [0.0.0] - 2026-04-06

### Added
- Initial commit with README.md
