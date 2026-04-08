# Two-Key Threshold Authorization System

## Overview

The Two-Key system requires two independent approvers for expense claims exceeding a configurable monetary threshold (default R5,000). No single individual can unilaterally authorize high-value expenditure. This strengthens King IV Principle 7 (Delegation of Authority), COSO segregation of duties controls, and ISO 37001 anti-bribery safeguards.

## Architecture: Sequential Dual-Approval via Native Level 3

Zoho Creator's approval process is inherently sequential (`on level 1`, `on level 2`, etc.). The Two-Key system adds `on level 3` with role = "Finance Director" as the second key. When the HoD (Key 1) approves a claim above the dual threshold, the claim routes to the Finance Director (Key 2) instead of being finalised.

## Configuration

All Two-Key settings are stored in the `Approval_Thresholds` table (Tier 3 record):

| Field | Value | Purpose |
|-------|-------|---------|
| `Tier_Name` | Tier 3 - Dual Approval | Identifier |
| `Max_Amount_ZAR` | 10,000.00 | Maximum claim amount for the system |
| `Approver_Role` | Finance Director | Key 2 approver role |
| `Tier_Order` | 3 | Position in escalation chain |
| `Active` | true | Feature toggle |
| `Requires_Dual_Approval` | true | Two-Key flag |
| `Dual_Approval_Role` | Finance Director | Key 2 role name |
| `Dual_Threshold_ZAR` | 5,000.00 | Amount above which Two-Key activates |

To change the threshold: update `Dual_Threshold_ZAR` in Creator UI. No code changes needed.
To disable Two-Key entirely: set `Active = false` on Tier 3. Claims revert to single HoD approval.

## Role Hierarchy

```
CEO
 +-- Finance Director  (Key 2 — Two-Key dual approval)
 +-- Head of Department (Key 1 — existing HoD role)
      +-- Line Manager
           +-- Employee
```

Finance Director is a **peer** of HoD under CEO, not a subordinate. This ensures structural independence between the two keys.

## Approval Flow

### Standard Flow (amount <= R5,000)

Unchanged from current system:

```
Employee -> LM -> [<= R999.99: Approved] or [> R999.99: HoD -> Approved]
```

### Two-Key Flow (amount > R5,000)

```
Employee submits
    |
LM approves (amount > R999.99, escalates to HoD)
    |
HoD approves (amount > R5,000 dual threshold)
    |
    +--> Status: "Pending Second Key"
    |    Key_1_Approver = HoD username
    |    Key_1_Timestamp = now
    |    GL code populated
    |    Finance Director notified
    |
Finance Director reviews
    |
    +--[Approves]--> Status: "Approved" (final, both keys signed)
    |                action_1 = "Approved (Key 2)"
    |                Employee notified
    |
    +--[Rejects]--> Status: "Key 2 Dispute"
                    action_1 = "Rejected (Key 2)"
                    HoD notified for reconsideration
```

### Key 2 Dispute Flow

When Finance Director (Key 2) rejects a claim that HoD (Key 1) approved:

```
Key 2 Dispute
    |
HoD reviews dispute
    |
    +--[Agrees with Key 2]--> Clicks Reject --> Status: "Rejected"
    |                         Employee can resubmit
    |
    +--[Overrides Key 2]----> Clicks Approve --> Status: "Pending Second Key"
                              action_1 = "Reconsidered (Key 1)"
                              New Key 2 cycle begins
                              Finance Director re-notified
```

This "rejection requires review" pattern ensures neither key can unilaterally finalise a high-value decision. The HoD must actively agree with or override the Key 2 rejection.

## Status Values

| Status | Meaning |
|--------|---------|
| Draft | Created but not submitted |
| Submitted | Passed validation, awaiting routing |
| Pending LM Approval | Awaiting Line Manager review |
| Pending HoD Approval | Awaiting HoD review (escalated or self-bypass) |
| **Pending Second Key** | Key 1 (HoD) approved, awaiting Key 2 (Finance Director) |
| **Key 2 Dispute** | Key 2 rejected, awaiting Key 1 reconsideration |
| Approved | Final approval (all required keys signed) |
| Rejected | Rejected by any approver (can resubmit) |
| Resubmitted | Employee corrected and resubmitted |

## Approval History Actions

| Action | Actor | Meaning |
|--------|-------|---------|
| Submitted | Employee | Initial submission |
| Submitted (Self-approval bypass) | LM Employee | LM self-submitted, bypassed Tier 1 |
| Approved (LM) | Line Manager | Tier 1 approval (under R999.99 = final, over = escalate) |
| Approved (HoD) | HoD | Single-key final approval (amount <= dual threshold) |
| **Approved (Key 1)** | HoD | First key signed, routed to Key 2 |
| **Approved (Key 2)** | Finance Director | Second key signed, dual approval complete |
| **Rejected (Key 2)** | Finance Director | Key 2 disputes Key 1's approval |
| **Reconsidered (Key 1)** | HoD | HoD overrides Key 2 rejection, re-routes to Key 2 |
| Rejected | Any approver | Claim rejected (employee can resubmit) |
| Escalated (SLA Breach) | SYSTEM | Auto-escalation after SLA timeout |
| Warning | SYSTEM | SLA reminder or governance alert |
| Resubmitted | Employee | Corrected and resubmitted after rejection |

## New Fields

### Expense_Claims (private/hidden from employees)

| Field | Type | Purpose |
|-------|------|---------|
| `Requires_Dual_Approval` | Checkbox | Set by HoD approval script when claim exceeds dual threshold |
| `Key_1_Approver` | Text | Stores `zoho.loginuser` of Key 1 for same-person prevention |
| `Key_1_Timestamp` | DateTime | When Key 1 approved. Used for Key 2 SLA enforcement |

### Approval_Thresholds (Tier 3 record)

| Field | Type | Purpose |
|-------|------|---------|
| `Requires_Dual_Approval` | Checkbox | Flag: this tier triggers Two-Key requirement |
| `Dual_Approval_Role` | Text | Role name for Key 2 approver |
| `Dual_Threshold_ZAR` | Currency | Amount above which Two-Key applies |

## Governance Controls

### Same-Person Prevention (King IV P1 + COSO)
The `finance_approval.on_approve.dg` script compares `zoho.loginuser` against `input.Key_1_Approver`. If they match, the approval is blocked, the status remains "Pending Second Key", and a governance alert is logged and emailed to the admin.

### Self-Submission Prevention
If the original submitter holds the Finance Director role, they cannot serve as Key 2 for their own claim. The script checks the submitter identity against the current approver.

### SLA Enforcement
Key 2 SLA mirrors Key 1 SLA:
- **Day 2**: Reminder email to Finance Director (cc: admin)
- **Day 3**: Auto-escalation alert to CEO/admin. `action_1 = "Escalated (SLA Breach)"`

SLA timing is measured from `Key_1_Timestamp`, not `Submission_Date`.

### Resubmission Handling
When an employee resubmits after any rejection (including Key 2 disputes):
- `Requires_Dual_Approval`, `Key_1_Approver`, and `Key_1_Timestamp` are cleared
- The claim re-enters the full approval pipeline from the beginning
- If the amount still exceeds the dual threshold, Two-Key activates again

## Scripts

| Script | Change | Purpose |
|--------|--------|---------|
| `hod_approval.on_approve.dg` | Modified | Dual threshold check + Key 2 Dispute reconsideration |
| `finance_approval.on_approve.dg` | New | Key 2 approval with same-person prevention |
| `finance_approval.on_reject.dg` | New | Key 2 rejection → Key 2 Dispute (not Rejected) |
| `sla_enforcement_daily.dg` | Modified | Added Key 2 SLA loop |
| `expense_claim.on_edit.dg` | Modified | Clear dual-approval fields on resubmit |

## Edge Cases

| Scenario | Handling |
|----------|---------|
| Same person is both Key 1 and Key 2 | Blocked by same-person check in finance_approval.on_approve.dg |
| Submitter is Finance Director | Cannot be Key 2 for own claim |
| Key 2 rejects, Key 1 agrees with rejection | HoD clicks Reject on "Key 2 Dispute" → Rejected |
| Key 2 rejects, Key 1 overrides | HoD clicks Approve on "Key 2 Dispute" → re-routes to Key 2 |
| Amount changed after Key 1 | Impossible — amount_zar is read-only for approvers |
| No Tier 3 config exists | Feature is opt-in — HoD remains final approver |
| Resubmission after dispute | Dual fields cleared, full pipeline restart |
| SLA breach on Key 2 | 2-day reminder, 3-day escalation to CEO |
