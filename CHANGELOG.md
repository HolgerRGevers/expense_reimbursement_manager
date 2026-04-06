# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
