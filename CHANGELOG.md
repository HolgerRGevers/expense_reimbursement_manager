# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.7.0] - 2026-04-12

### Added
- International standards alignment: ISSB IFRS S1/S2, GRI 205/301/302/305, ISO 26000, ISO 37000, ISSA 5000
- ESG tracking: GL accounts carry ESG_Category and Carbon_Factor; approved claims carry Estimated_Carbon_KG
- Compliance_Config form: org-type-specific controls (PRIVATE, JSE_LISTED, SOE, MULTINATIONAL)
- Sustainability Dashboard page with ESG reporting components
- `ds_editor.py apply-esg` subcommand for programmatic ESG schema deployment
- Compliance documentation: international-standards-mapping.md, esg-reporting-guide.md, companies-act-alignment.md
- Custom API Builder research (docs/zoho-custom-api-builder-research.md) with 5 priority APIs defined
- Linter rules DG020 (Custom API must build response Map) and DG021 (no form tasks in Custom API context)
- Scaffold `custom-api` context with response Map boilerplate
- ForgeDS extraction guide (docs/forgeds-extraction-guide.md) and forgeds.yaml project config
- Discovery log entry DL-007: Custom API Builder initial research

### Changed
- Linter expanded from 20 to 21 rules (DG001-DG021)
- Scaffold supports 4 contexts: form-workflow, approval-script, scheduled, custom-api
- Enhancement specs updated to reflect completed features (Two-Key, Import Pipeline, ESG)
- Seed data: gl_accounts.json now includes ESG_Category and Carbon_Factor fields
- Seed data: compliance_config.json added (8 configuration entries)

## [0.6.0] - 2026-04-07

### Added
- Access-to-Zoho import pipeline: export_access_csv.py, validate_import_data.py, upload_to_creator.py
- Hybrid cross-environment linter (lint_hybrid.py): 14 rules validating Access-to-Zoho integration
- Access/VBA language database (build_access_vba_db.py): 12 tables, 505 rows
- Access SQL linter (lint_access.py): 8 rules (AV001-AV008)
- Access database builder (build_access_db.py): creates .accdb with seed data
- Mock data generator (generate_mock_data.py): 7 personas, 175 claims, Two-Key approval paths
- Lindiwe Mahlangu persona for Two-Key dual-approval testing
- Import documentation: access-to-zoho-import-guide.md, type-mapping-reference.md, api-upload-guide.md
- Mapping seed data extracted to JSON: type_mappings.json, field_name_mappings.json, access_table_fields.json

### Changed
- Two-Key threshold authorization fully implemented:
  - 3-tier approval: LM (R999.99) -> HoD (R10,000) -> Finance Director (R5,000+ Two-Key)
  - finance_approval.on_approve.dg and finance_approval.on_reject.dg scripts
  - hod_approval.on_approve.dg expanded with Two-Key routing and ESG population
  - sla_enforcement_daily.dg expanded with Key 2 SLA enforcement loop
  - expense_claim.on_edit.dg clears dual-approval fields on resubmission
  - ds_editor.py apply-two-key subcommand for programmatic .ds deployment
  - Key_1_Approver, Key_1_Timestamp, Key_2_Approver, Key_2_Timestamp tracking fields
  - approval_thresholds.json: 3 tiers with Requires_Dual_Approval flag
- Deluge scripts expanded from 11 to 13 (693 LOC)
- Employee Dashboard redesigned with native Zoho Creator components
- Tool names consolidated with first-principles naming

## [0.5.0] - 2026-04-07

### Added
- Field descriptions (help text) on 42 of 49 fields across all 6 forms (was 5)
  - Every user-facing field now has hover/tooltip guidance
  - Descriptions explain purpose, format requirements, and compliance context
  - Private/system fields (Department_Shadow, Client_Shadow, Parent_Claim_ID) excluded

### Removed
- `expense_claims_by_category` kanban report (Launchpad boilerplate, duplicated list view)
- `approval_history_by_action_1` kanban report (generic grouping, no governance value)
- All menu references and permission entries for deleted reports

### Changed
- Restricted report menus on reference/audit reports (approval_thresholds, clients, departments, approval_history) to view-only (removed Edit/Duplicate/Delete/Import/Export)
- Kept full menus on expense_claims_Report, My_Claims, pending_approvals_manager (users need Edit)

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
