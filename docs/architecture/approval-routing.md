# Approval Routing

## Overview

Two-tier approval process coordinated via the Status field on Expense_Claims. Each tier has its own Zoho Creator approval process with On Approve / On Reject Deluge scripts.

## Tier Structure

| Tier | Role | Max Authority | Condition |
|------|------|--------------|-----------|
| Tier 1 | Line Manager | R999.99 | All claims from Employees |
| Tier 2 | Head of Department | R10,000.00 | Claims exceeding Tier 1 threshold OR self-approval bypass |

## Routing Logic

### Normal Flow (Employee submits)
1. On Success: status -> "Pending LM Approval", notify LM
2. LM Approve:
   - If amount <= R999.99: status -> "Approved" (final), populate GL code
   - If amount > R999.99: status -> "Pending HoD Approval", notify HoD
3. HoD Approve: status -> "Approved" (final), populate GL code

### Self-Approval Bypass (King IV Principle 1)
1. If submitter holds "Line Manager" role:
   - Skip LM tier entirely
   - status -> "Pending HoD Approval", notify HoD directly
   - Audit trail records: "Submitted (Self-approval bypass)"
2. Same bypass logic applies on resubmission

### SLA Enforcement
- **v2.1 targets** (in .dg scripts): 2-day reminder, 3-day auto-escalation
- **Current .ds deployment**: 1-day reminder, 2-day auto-escalation
- On breach: status -> "Pending HoD Approval", actor = "SYSTEM"

## Threshold Configuration

Thresholds are stored in the `approval_thresholds` config table and queried at runtime. If the config record is missing, scripts fall back to R999.99 (matching seed data) and log a warning to approval_history.

## GL Code Auto-Population

On final approval (either LM or HoD), the system:
1. Queries `gl_accounts[expense_category == input.category && Active == true]`
2. Null guard: `glRec != null && glRec.count() > 0`
3. If match found: populates `gl_code` field
4. If no match: logs "UNMAPPED" in audit trail

## Rejection Flow

Both LM and HoD rejection:
1. status -> "Rejected"
2. Captures Rejection_Reason (with ifnull guard)
3. Logs to approval_history
4. Notifies employee via email
5. Employee can edit and resubmit (triggers version increment)
