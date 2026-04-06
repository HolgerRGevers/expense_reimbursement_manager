# Governance Remediation Master Plan

Source: Governance Gap Report (06-Apr-2026) by Holger Gevers
Audited against: .ds export (06-Apr-2026), src/deluge/ scripts, config/roles-and-permissions.md

## Executive Summary

16 gaps identified. 15 resolved or implemented in .ds. 1 remaining (G-05 hardcoded emails -- requires config table design).

| Status | Count | Gaps |
|--------|-------|------|
| Resolved (pre-existing) | 3 | G-01, G-02, G-12 |
| Implemented in .ds (pending user import test) | 12 | G-03, G-04, G-06, G-07, G-08, G-09, G-10, G-11, G-13, G-14, G-15, G-16 |
| Open - requires design decision | 1 | G-05 (hardcoded emails -- needs config table or Creator approval notifications) |

## Implementation Phases

### Phase A: Critical (must fix before demo)
- G-07: Lock down LM status field

### Phase B: High (current sprint)
- G-03: Fix approval trigger condition
- G-04: Add Tier_Order to Approval_Thresholds
- G-05: Replace hardcoded emails
- G-09: Add retention date field
- G-11: Fix SLA audit trail Added_User

### Phase C: Medium (next iteration)
- G-06: VAT invoice type enforcement
- G-08: GL receipt_required default
- G-10: POPIA consent capture
- G-13: Remove gl_code "allow new entries"
- G-15: Duplicate claim detection

### Phase D: Low (if time permits)
- G-14: Remove department/client "allow new entries"
- G-16: Anti-bribery risk classification

---

## Resolved Gaps

### G-01 -- HoD Approval Process [RESOLVED]
**Principle**: P1 -- Segregation of Duties
**Original gap**: HoD approval stage missing from .ds.
**Current status**: The Line_Manager_Approval process has two levels -- Level 1 (LM) and Level 2 (HoD). Both exist in the .ds export with full On Approve / On Reject scripts.
**Evidence**: .ds lines 1348-1549, approval-scripts/hod_approval.on_approve.dg, hod_approval.on_reject.dg

### G-02 -- LM On Reject Script [RESOLVED]
**Principle**: P1 -- Segregation of Duties
**Original gap**: LM rejection had no audit trail.
**Current status**: Full rejection script exists with status update, approval_history insert, rejection reason capture, and employee notification.
**Evidence**: src/deluge/approval-scripts/lm_approval.on_reject.dg (30 lines, complete)

### G-12 -- Approval_History Direct Access [RESOLVED]
**Principle**: P15 -- Combined Assurance
**Original gap**: Employees could create fabricated audit records.
**Current status**: Employee, Line Manager, and HoD roles have no Create permission on approval_history. Only Deluge scripts can insert records.
**Evidence**: .ds share_settings -- approval_history has no `enabled= Create` for any non-admin role.

---

## Phase A: Critical

### G-07 -- Line Manager Status Field Override
**Principle**: P12 -- Technology Governance
**Severity**: CRITICAL
**Gap**: Line Manager role has `status` field set to `readonly:false`. LMs can manually change claim status, bypassing the entire approval workflow.
**Current state**: .ds share_settings Line Manager profile: `status{visibility:true,readonly:false}`
**Change type**: Creator UI (Share Settings) OR .ds structural edit

**Remediation steps**:
1. In Creator: Settings > Share > Line Manager > Expense Claims > Field Properties
2. Set `status` to Read-Only for Line Manager role
3. In .ds: Change `readonly:false` to `readonly:true` for status field in Line Manager profile

**Verification**:
- Log in as LM user
- Open an expense claim
- Confirm status field is not editable
- Confirm approval workflow still updates status correctly via scripts

---

## Phase B: High

### G-03 -- LM Approval Trigger Condition
**Principle**: P1 -- Segregation of Duties
**Severity**: HIGH (downgraded from CRITICAL after audit -- HoD level exists)
**Gap**: Approval trigger uses `Parent_Claim_ID.status == "Pending LM Approval"` instead of the record's own `status` field. This may cause the approval process to not fire for standard (non-resubmitted) submissions.
**Current state**: .ds line 1353: `form = expense_claims[Parent_Claim_ID.status == "Pending LM Approval"]`
**Change type**: Creator UI (Approval Process settings) OR .ds structural edit

**Remediation steps**:
1. In Creator: Approval Process > Line Manager Approval > Edit filter condition
2. Change from `Parent_Claim_ID.status == "Pending LM Approval"` to `status == "Pending LM Approval"`
3. In .ds: Replace the trigger line

**Verification**:
- Submit a new claim as Employee (no parent claim)
- Confirm it enters LM approval queue
- Submit a resubmitted claim
- Confirm it also enters LM approval queue

**UNCERTAIN**: Whether changing the filter in the .ds file directly will be accepted on import. The approval process filter syntax may have internal references. This is a candidate for the .ds edit experiment.

---

### G-04 -- Tier_Order Field Missing
**Principle**: P7 -- DoA Tiers
**Severity**: HIGH
**Gap**: Approval_Thresholds form has no Tier_Order field. Multi-tier routing requires explicit ordering.
**Current state**: Form has: tier_name, max_amount_zar, approver_role, Active. No ordering field.
**Change type**: Creator UI (form builder) + seed data update + script update

**Remediation steps**:
1. Add `Tier_Order` field (Number type) to Approval_Thresholds form in Creator
2. Update seed data:
   ```json
   { "Tier_Name": "Tier 1 - Line Manager", "Max_Amount_ZAR": 999.99, "Tier_Order": 1, ... }
   { "Tier_Name": "Tier 2 - Head of Department", "Max_Amount_ZAR": 10000.00, "Tier_Order": 2, ... }
   ```
3. Update lm_approval.on_approve.dg threshold query to sort by Tier_Order
4. Update config/seed-data/approval_thresholds.json
5. Update build_deluge_db.py form_fields to include new field
6. Run linter

**Verification**:
- Query Approval_Thresholds sorted by Tier_Order
- Confirm Tier 1 (LM) returns before Tier 2 (HoD)
- Submit claims at various amounts and verify correct tier routing

---

### G-05 -- Hardcoded Email Addresses
**Principle**: P7 -- DoA Tiers
**Severity**: HIGH
**Gap**: 8 hardcoded demo emails across 6 .dg files. Not scalable, not production-ready.
**Current state**: `hod.demo@yourdomain.com` (4x), `linemanager.demo@yourdomain.com` (4x). Linter flags all as DG015 warnings.
**Change type**: Deluge script changes (all sendmail blocks)

**Remediation options** (choose one):
- **Option A (Simple)**: Query a config table or role-based user lookup for approver emails
- **Option B (Best)**: Use Creator's built-in approval task email routing (removes sendmail entirely for approval notifications)
- **Option C (Interim)**: Centralise emails in a Config form with a single record, query at runtime

**UNCERTAIN**: Whether Zoho Creator's approval process has built-in notification settings that would make manual sendmail redundant. Need to verify in Creator UI.

**Remediation steps (Option C -- interim)**:
1. Create or reuse a config record with LM_Email and HoD_Email fields
2. In each script, query the config record instead of hardcoding
3. Replace `"hod.demo@yourdomain.com"` with `configRec.HoD_Email`
4. Update email-templates.yaml to reflect dynamic lookup

**Verification**:
- Change email in config table
- Submit a claim
- Confirm notification goes to the new email address

---

### G-09 -- Record Retention (SARS Tax Administration Act S29)
**Principle**: P13 -- Compliance
**Severity**: HIGH
**Gap**: No retention date, no archival flag, no purge prevention. Tax Admin Act requires 5-year retention.
**Current state**: No retention fields on expense_claims.
**Change type**: Creator UI (form builder) + new scheduled workflow + On Delete validation

**Remediation steps**:
1. Add fields to Expense_Claims:
   - `Retention_Expiry_Date` (Date, formula: `addYear(Submission_Date, 5)`)
   - `Archived` (Checkbox, default: false)
2. Add On Delete validation script:
   ```deluge
   if (input.Retention_Expiry_Date > zoho.currentdate)
   {
       alert "This record is within the 5-year SARS retention window and cannot be deleted.";
       cancel delete;
   }
   ```
3. Optional: Add scheduled workflow to flag records approaching expiry (90 days before)

**Verification**:
- Create a claim dated today
- Attempt to delete it
- Confirm deletion is blocked with retention message
- Create a claim with Submission_Date > 5 years ago
- Confirm deletion is allowed

**UNCERTAIN ABOUT SYNTAX**: `cancel delete;` -- need to verify this is valid Deluge syntax for On Delete events. The reference doc confirms `cancel submit;` for On Validate, but `cancel delete;` is not explicitly documented.

---

### G-11 -- SLA Audit Trail Added_User
**Principle**: P15 -- Combined Assurance
**Severity**: HIGH
**Gap**: `Added_User = zoho.loginuser` in SLA scheduled workflow logs the system scheduler's identity, not meaningful audit data.
**Current state**: sla_enforcement_daily.dg line 28: `Added_User = zoho.loginuser`
**Change type**: Deluge script change

**Remediation steps**:
1. Change `Added_User = zoho.loginuser` to `Added_User = zoho.adminuserid` in sla_enforcement_daily.dg
2. The `actor` field is already correctly set to `"SYSTEM"` (line 25)

**UNCERTAIN**: Whether `Added_User` is a system-required field that must equal `zoho.loginuser` for Creator to accept the insert, or if it can be any valid email. If Creator enforces `Added_User = zoho.loginuser`, this fix may cause a runtime error. Test in Creator.

**Verification**:
- Wait for scheduled task to fire (or trigger manually if possible)
- Check approval_history record
- Confirm Added_User shows admin email, not blank/error

---

## Phase C: Medium

### G-06 -- VAT Invoice Type Enforcement
**Principle**: P11 -- Risk Controls
**Severity**: MEDIUM
**Gap**: No VAT invoice type differentiation. SARS requires full tax invoices above R5,000.
**Change type**: Creator form + On Validate script

**Remediation steps**:
1. Add `VAT_Invoice_Type` picklist to Expense_Claims: `None`, `Abbreviated (< R5,000)`, `Full Tax Invoice (>= R5,000)`
2. Add On Validate rule:
   ```deluge
   if (input.amount_zar >= 5000 && input.VAT_Invoice_Type != "Full Tax Invoice (>= R5,000)")
   {
       alert "Claims of R5,000 or more require a Full Tax Invoice. Please update the VAT Invoice Type.";
       cancel submit;
   }
   ```
3. Update field-link-names.md and build_deluge_db.py

**Verification**:
- Submit claim for R6,000 without Full Tax Invoice selection -- should be blocked
- Submit claim for R6,000 with Full Tax Invoice -- should succeed
- Submit claim for R200 without selection -- should succeed

---

### G-08 -- GL receipt_required Default
**Principle**: P12 -- Technology Governance
**Severity**: MEDIUM
**Gap**: `receipt_required` defaults to false. SARS S11(a) mandates receipts for all deductible expenses.
**Change type**: Creator form OR .ds structural edit

**Remediation steps**:
1. In Creator: GL_Accounts form > receipt_required field > Set default value to `true`
2. In .ds: Add `initial value = true` to receipt_required field definition
3. Update existing GL records to set receipt_required = true

**Verification**:
- Create new GL Account record
- Confirm receipt_required is pre-checked (true)

---

### G-10 -- POPIA Consent Capture
**Principle**: P13 -- Compliance (POPIA)
**Severity**: MEDIUM
**Gap**: Employee_Name and Email are marked `personal data = true` but no consent mechanism exists.
**Change type**: Creator form + On Validate script

**Remediation steps**:
1. Add `POPIA_Consent` (Decision Box / Checkbox) to Expense_Claims
2. Add privacy notice text as field description
3. Add On Validate rule: `if (!input.POPIA_Consent) { alert "..."; cancel submit; }`
4. Log consent in approval_history on first submission

**Verification**:
- Submit claim without POPIA consent -- blocked
- Submit with consent -- succeeds
- Check approval_history for consent timestamp

---

### G-13 -- GL Code "Allow New Entries"
**Principle**: P12 -- Technology Governance
**Severity**: MEDIUM
**Gap**: Any user can create GL Account records inline from the Expense_Claims form.
**Change type**: Creator form builder OR .ds structural edit

**Remediation steps**:
1. In Creator: Expense_Claims form > gl_code field > Uncheck "Allow new entries"
2. In .ds: Remove the `allow new entries [ displayname = "Add New" ]` block from gl_code field definition

**Verification**:
- Open Expense_Claims form as Employee
- Confirm gl_code dropdown shows existing records only, no "Add New" option

---

### G-15 -- Duplicate Claim Detection
**Principle**: COSO Internal Control
**Severity**: MEDIUM
**Gap**: No duplicate detection. Same expense could be submitted multiple times.
**Change type**: Deluge On Validate script

**Remediation steps**:
1. Add to expense_claim.on_validate.dg:
   ```deluge
   duplicates = expense_claims[Expense_Date == input.Expense_Date && amount_zar == input.amount_zar && Added_User == zoho.loginuser && ID != input.ID];
   if (duplicates != null && duplicates.count() > 0)
   {
       alert "Potential duplicate claim detected: same date, amount, and submitter. Please verify this is not a duplicate.";
   }
   ```
2. Note: This is a warning alert, not a cancel submit -- allows user to proceed if intentional

**UNCERTAIN**: Whether `Added_User` is the correct field to identify the submitter, or if a different field (like a custom Submitter_Email) should be used. `Added_User` is system-populated and may represent the form adder.

**Verification**:
- Submit claim for R500 on 2026-04-06
- Submit second claim for same amount and date
- Confirm duplicate warning appears

---

## Phase D: Low

### G-14 -- Department/Client "Allow New Entries"
**Principle**: P12 -- Technology Governance
**Severity**: LOW
**Gap**: Users can create department/client records inline.
**Change type**: Creator form builder OR .ds structural edit

**Remediation steps**:
1. Remove `allow new entries` from department and client fields in Creator
2. Or: Remove in .ds file

**Verification**: Confirm no "Add New" option in dropdowns.

---

### G-16 -- Anti-Bribery Risk Classification
**Principle**: ISO 37001
**Severity**: LOW
**Gap**: No risk level on GL accounts for enhanced scrutiny of bribery-prone categories.
**Change type**: Creator form + approval script modification

**Remediation steps**:
1. Add `Risk_Level` picklist to GL_Accounts: `Standard`, `Elevated`, `High`
2. Set Meals & Entertainment = High, Client Entertainment = High, Professional Services = Elevated
3. Modify lm_approval.on_approve.dg: if Risk_Level == "High", escalate to HoD regardless of amount
4. Update seed data and build_deluge_db.py

**Verification**:
- Submit R100 Meals & Entertainment claim (under LM threshold)
- Confirm it escalates to HoD despite low amount

---

## .ds Edit Experiment Candidates

The following gaps can be tested as direct .ds file edits:

| Gap | Edit | Risk | Lines to change |
|-----|------|------|----------------|
| G-08 | Add `initial value = true` to receipt_required | Very Low | 1 line add |
| G-13 | Remove `allow new entries` from gl_code | Low | 4 lines delete |
| G-14 | Remove `allow new entries` from department/client | Low | 8 lines delete |
| G-07 | Change `readonly:false` to `readonly:true` for LM status | Low | 1 line edit |
| G-03 | Change approval trigger filter | Medium | 1 line edit |

Start with G-08 (simplest), escalate to G-07 (most impactful) if imports succeed.
