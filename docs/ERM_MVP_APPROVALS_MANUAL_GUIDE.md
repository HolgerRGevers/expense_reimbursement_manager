# ERM MVP Approvals — Manual Build Guide

**What you're building:** a working two-tier expense-approval loop inside the
Zoho Creator "Expense Reimbursement Management" app. At the end of this
guide, an Employee can submit a claim, a Line Manager can approve it (which
either finalises it or escalates to Head of Department depending on amount),
and the Head of Department can approve or reject it. Every state change
lands in an audit-trail row. All state changes are visible as advancing
stages on a lifecycle blueprint.

**How the work is split.** This guide is three passes. You can stop after
each pass and have a working, demo-runnable system at that point. Each pass
layers onto the previous one — no rework.

- **Pass 1 — Core approval loop.** Amount-based routing (LM → HoD),
  audit trail, blueprint lifecycle visibility. **No** emails, **no** SLA,
  **no** self-approval bypass, **no** dual-key control.
- **Pass 2 — Governance additions.** Self-approval bypass (if the submitter
  *is* a Line Manager, skip the LM tier) and SLA scheduled enforcement
  (reminder at day 2, auto-escalate LM → HoD at day 3).
- **Pass 3 (deferred, not designed here).** Dual-approval enforcement
  (Key 1 ≠ Key 2) for claims above a configurable threshold.

**Audience.** Someone working inside the Zoho Creator builder. You don't
need to be a Deluge expert. Every code block below is ready to paste; I
walk through what it does in plain English after each one. You do need
access to the app in builder mode.

**How to read path references.** When I say
**Workflow → Form Actions → expense_claims → On Add → On Validate**,
I mean: open the Creator builder, click the "Workflow" panel in the left
sidebar, find "Form Actions", find the `expense_claims` form, choose
"On Add" (the event-group tab), then "On Validate" (the event within the
group). If a panel name doesn't match exactly — Zoho has renamed things
between release waves — the concept is identical; a two-sentence glossary
is in the Appendix.

**Case sensitivity is real.** Every field link name (e.g. `amount_zar`,
`Email`, `Department_ID`, `Key_1_Approver`, `Claim_Reference`) is literal.
`input.amount_zar` and `input.Amount_ZAR` are different fields as far as
Creator is concerned. Do not "fix" casing that looks wrong — it matches
the link names in the imported `.ds`.

**Screenshots.** Where visual orientation helps, I describe the panel in
words first, then leave a placeholder like
`![Screenshot: On Validate panel](./screenshots/on-validate.png)` for you
to drop a real screenshot in later. The text alone is sufficient to
execute the guide; the screenshots make future-you's life easier when you
come back to this doc in three months.

---

# Part A — Pass 1: Core approval loop

By the end of Part A, the following will be true in your app:

- Submitting a claim validates required fields and hard-stops on missing
  ones.
- Submitting a claim auto-computes the `Claim_Reference`, the retention
  expiry date, and routes to `Pending LM Approval` or `Pending HoD Approval`
  based on amount (using thresholds stored in config, not hard-coded).
- An approval-history audit row is written on submit.
- Four buttons appear inside claim records: **LM Approve**, **HoD Approve**,
  **Reject**, **Request Clarification**. Each is visibility-gated to the
  right status and records an audit row when clicked.
- The blueprint lifecycle chart advances as the claim's status changes.

The three governance rules wired in Pass 1:

1. **Amount-based routing.** Claims ≤ R999.99 → LM has final say. Claims
   > R999.99 → must reach HoD.
2. **Append-only audit trail.** Every state change writes one row to
   `approval_history`; nothing is ever overwritten or deleted.
3. **Lifecycle visibility.** The blueprint shows real-time state without
   users needing to read the `status` dropdown.

---

## A.0. Schema gap — add the missing fields first

**Reality check before Deluge.** Comparing the guide's Deluge against the
`expense_claims` form as it currently exists in
`Expense_Reimbursement_Management-development.ds`: the form today has only
ten fields, and several of the business-critical ones (most importantly
the **amount** field the whole tier-routing flow pivots on) are missing.
You cannot paste the Pass 1 Deluge and expect it to run — it will fail to
save, citing unresolved field references.

This section lists exactly what's there, what's missing, and how to add
the missing ones before touching any workflow.

**Navigate to:** **Design (left sidebar) → Forms → expense_claims**. The
right-hand panel lists every field on the form with its Link Name and
Type. That list is what you're auditing.

![Screenshot: expense_claims form with field list panel](./screenshots/a0-expense-claims-fields.png)

### A.0.1. Already on the form (verify these exist)

These ten fields are already declared in `-development.ds`. Confirm each
one with its exact Link Name and Type before proceeding. (Click each
field in the Design canvas; the Link Name and Type show in the
properties panel.)

| Field link name | Type | Purpose in this guide |
|---|---|---|
| `Email` | Email | Who submitted |
| `Submission_Date` | Date | Logical claim date |
| `Claim_Submission_Timestamp` | Date-Time | Save time (set by workflow) |
| `Claim_Reference` | Single Line | Auto-generated `EXP-<ID>` string |
| `status` | Dropdown | Routing state |
| `category` | Dropdown | Expense category |
| `VAT_Invoice_Type` | Dropdown | VAT treatment |
| `gl_code` | Lookup → `gl_accounts` | Optional GL code (unused in MVP) |
| `Supporting_Documents` | Single Line | Attachment placeholder |
| `Retention_Expiry_Date` | Date | Set by workflow (Submission_Date + 5y) |

**Status picklist values already declared:** `Submitted`, `Draft`,
`Pending HoD Approval`, `Pending Second Key`, `Key 2 Dispute`, `Approved`,
`Rejected`, `Resubmitted`, `Pending LM Approval`. All the values this
guide needs are present. `Pending Second Key` and `Key 2 Dispute` are
Pass-3-only; leave them in place.

### A.0.2. Missing from the form — add these before proceeding

**Every field below must be added** before the Deluge in A.2 and later
sections will run. Path for each: **Design → expense_claims → drag the
matching field type from the left palette onto the canvas → set the
Display Name → verify the Link Name matches the table**. If Creator's
auto-derived Link Name doesn't match, rename it while the field is still
new (Field Properties → Advanced → Link Name).

| Link name to set | Type | Default value | Why we need it |
|---|---|---|---|
| `amount_zar` | **Currency (ZAR)** | (blank) | The amount — the input to tier routing in A.2 |
| `Department_ID` | **Lookup** → `departments` | (blank) | Required on every claim; referenced in A.2 validation |
| `Client_ID` | **Lookup** → `clients` | (blank) | Optional; a placeholder for clients-billing later |
| `approval_comments` | **Multi Line** | (blank) | Rejection reason / clarification request text (A.6, A.7) |
| `Key_1_Approver` | **Single Line** | (blank) | Captured in A.4 LM_Approve / A.5 HoD_Approve; becomes the SoD anchor in Pass 3 |
| `Key_2_Approver` | **Single Line** | (blank) | Set in Pass 3 — add now so schema is stable |
| `Version` | **Number** | `1` | Resubmission counter (used in Pass 2 B.3) |

> **Naming convention.** The capitalisation above is deliberate and
> matches how the CORE workflows doc and the BRD refer to these fields.
> Don't let Creator convert `amount_zar` to `Amount_ZAR` — override the
> Link Name at creation time if needed.

**After adding each field, save the form** (top-right Save button). The
field is now available for Deluge reference as `input.<link_name>`.

### A.0.3. Sanity re-check before moving on

Re-open the `expense_claims` form in Design mode. The field list on the
right should show 17 fields total (10 original + 7 added). Every name in
both tables above should be visible. If any Link Name is wrong, rename
now — renaming after Deluge is written means updating every script.

---

## A.1. Seed the `approval_thresholds` table

**What this step does and why.** The tier thresholds (R999.99 for LM, R10,000
for HoD) are not hard-coded in any Deluge. They live as rows in the
`approval_thresholds` form, and the routing Deluge reads them at run time.
This means you can change a threshold in the future by editing a record,
not by editing code. We also seed a **dormant** Dual Threshold row so the
schema is Pass-3-ready without Pass-1-time changes.

**Navigate to:** switch from **Builder** mode to **View** mode (toggle at
top-right of the builder). You're now in the live app view. From the left
menu select **Approval Thresholds**. Click **+ Add New** (or the "+" icon
above the list).

![Screenshot: Approval Thresholds add-new form](./screenshots/a1-thresholds-add.png)

**Add these three records, one at a time.** The `tier_name` column values
are literal keys — the Deluge below will look up rows by this string.
Rename any and you must update the Deluge string in lockstep.

| `tier_name` | `approver_role` | `max_amount_zar` | `Tier_Order` | `Requires_Dual_Approval` | `Dual_Threshold_ZAR` | `Active` |
|---|---|---|---|---|---|---|
| Tier 1 | LM | 999.99 | 1 | false (☐) | 0 | true (☑) |
| Tier 2 | HoD | 10000 | 2 | false (☐) | 0 | true (☑) |
| Dual Threshold | Finance | 0 | 99 | true (☑) | 100000 | **false (☐)** |

**Why Dual Threshold is inactive.** The routing Deluge filters rows with
`Active == true` before reading them, so the R100,000 dual-threshold value
is silently ignored in Pass 1 — the record exists as a placeholder only.
In Pass 3 you'll flip its `Active` flag to true and the dual logic
activates without any schema change.

**Verify.** After saving all three, navigate to the Approval Thresholds
list view. You should see three rows. Tier 1 and Tier 2 rows show a green
Active indicator (or the Active column shows `true`); the Dual Threshold
row shows inactive / `false`.

---

## A.2. Form Action — On Add → On Validate

**What this step does and why.** Creator fires the "On Validate" workflow
*before* the record is saved to the database. This is the only place where
you can reject a submission with a clean error message and keep the user
on the form. We use it for three things:

1. **Required-field guards.** Hard-stop if `Email`, `Submission_Date`,
   `amount_zar`, or `Department_ID` is missing or zero.
2. **Submission metadata.** Set `Claim_Submission_Timestamp` (the moment
   of save, not the logical claim date) and `Retention_Expiry_Date`
   (Submission_Date + 5 years for tax/audit record-retention).
3. **Tier routing.** Read the threshold config and set `status` to
   `Pending LM Approval` or `Pending HoD Approval` based on `amount_zar`.

Validation and initial routing have to happen in On Validate (not On
Success) because `status` must be correct the moment the record is saved;
if we wait until On Success, the record briefly exists with the wrong
status and any audit row we write lies.

**Navigate to:** **Workflow (left sidebar) → Form Actions → expense_claims**.
You'll see a top tab row with "On Add" and "On Edit". Click **On Add**.
Below that, three sub-panels labelled **On Load**, **On Validate**,
**On Success**. Click **On Validate → Click to write Deluge → Free-flow
script**.

![Screenshot: On Add → On Validate panel ready for Deluge](./screenshots/a2-on-validate.png)

**Paste this exactly:**

```deluge
// --- Required-field checks --------------------------------------------
if(input.Email == null || input.Email == "")
{
    alert "Email is required.";
    cancel submit;
}
if(input.Submission_Date == null)
{
    alert "Submission Date is required.";
    cancel submit;
}
if(input.amount_zar == null || input.amount_zar <= 0)
{
    alert "Amount (ZAR) must be greater than zero.";
    cancel submit;
}
if(input.Department_ID == null)
{
    alert "Department is required.";
    cancel submit;
}

// --- Submission metadata ----------------------------------------------
input.Claim_Submission_Timestamp = zoho.currenttime;
input.Retention_Expiry_Date      = input.Submission_Date.addYear(5);

// --- Tier routing by amount -------------------------------------------
t1 = approval_thresholds[tier_name == "Tier 1" && Active == true];
t2 = approval_thresholds[tier_name == "Tier 2" && Active == true];

t1_max = if(t1.count() > 0, t1.max_amount_zar, 0.0);
t2_max = if(t2.count() > 0, t2.max_amount_zar, 0.0);

if(input.amount_zar <= t1_max)
{
    input.status = "Pending LM Approval";
}
else if(input.amount_zar <= t2_max)
{
    input.status = "Pending HoD Approval";
}
else
{
    // Above T2 max in Pass 1 — still HoD's responsibility
    input.status = "Pending HoD Approval";
}
```

**Save the Deluge.** Click "Save Script" (or equivalent) and then **Save**
at the top of the Form Actions panel.

**Walkthrough in plain English.**

- The four `if` blocks at the top short-circuit the submit if any
  mandatory field is empty. `cancel submit` is the magic word — it stops
  the save and keeps the user on the form with the `alert` text visible.
- `Claim_Submission_Timestamp = zoho.currenttime` captures the save time.
  We keep this separate from `Submission_Date` because `Submission_Date`
  is what the Employee types (the logical date the expense happened or
  was submitted against), while the timestamp is the technical "when the
  record got written".
- `Retention_Expiry_Date = input.Submission_Date.addYear(5)` sets the
  audit-retention window to five years from the claim's logical date.
  (Your organisation's retention policy may differ; change the `5` to
  match.)
- The routing block pulls both threshold rows by their literal `tier_name`
  and filters on `Active == true`, then extracts `max_amount_zar` via a
  null-safe `if(count > 0, value, 0.0)` pattern. If the config rows are
  missing, both maxes fall back to `0.0` and every claim routes to
  `Pending HoD Approval` — not ideal but not broken.
- The final `if / else if / else` chain assigns `status`. `<= t1_max`
  (i.e. R999.99) stays at LM; between R999.99 and R10,000 jumps to HoD;
  anything bigger also jumps to HoD (in Pass 3 the "anything bigger"
  branch gets replaced with the dual-key routing).

---

## A.3. Form Action — On Add → On Success

**What this step does and why.** "On Success" fires *after* the record is
saved to the database. This is the right place for two post-save chores:

1. Generate `Claim_Reference` in the form `EXP-<ID>`. We couldn't do this
   in On Validate because the record has no ID yet — `input.ID` is only
   populated once the row is persisted.
2. Write the opening audit row to `approval_history`. Same reason —
   `approval_history.claim` is a lookup to `expense_claims.ID`, and the
   ID doesn't exist until post-save.

**Navigate to:** **Workflow → Form Actions → expense_claims → On Add →
On Success → Click to write Deluge → Free-flow script**.

**Paste this exactly:**

```deluge
// --- Auto-generate claim reference in form EXP-<ID> -------------------
if(input.Claim_Reference == null || input.Claim_Reference == "")
{
    input.Claim_Reference = "EXP-" + input.ID.toString();
}

// --- Seed audit trail --------------------------------------------------
insert into approval_history
[
    added_user = zoho.loginuser
    claim      = input.ID
    action_1   = "Submitted"
    timestamp  = zoho.currenttime
    actor_role = zoho.loginuser
    notes      = "Claim submitted. Routed to: " + input.status
];
```

**Save.**

**Walkthrough in plain English.**

- `input.ID` is Creator's auto-generated primary key; it's a numeric
  value like `4,500,000,000,123`. `toString()` converts it to the
  string form, and we prefix it with `EXP-` to get a human-readable
  reference.
- The `if` guard means: if the user already set a Claim_Reference by
  some other path (e.g. imported data), respect it; otherwise generate
  ours.
- `insert into approval_history [ ... ]` is Creator's equivalent of SQL
  `INSERT`. The square brackets enclose key-value pairs (one per field
  you want to populate; unnamed fields get their default values).
  `added_user` is Creator's built-in tracking field for "which user
  created this row". `claim` is the lookup back to the parent
  expense_claims record.
- `action_1` is a picklist on `approval_history`. `"Submitted"` is one
  of its existing choices.
- `notes` captures the derived routing outcome — Approved flow, LM
  approvers, and auditors reading this history later will see why the
  claim went where it went.

**Verify.** Enter View mode, add a new claim with valid values (Email
filled, Submission_Date set, amount_zar = 500, Department_ID = any
active department). On save, open the claim — `Claim_Reference` should
show `EXP-<id>`, `status` should be `Pending LM Approval`, and if you
open **Approval History** in the left menu you should see one new row
with `action_1 = "Submitted"` and `notes` mentioning the routing.

---

## A.4. Custom Action — `LM_Approve`

**What this step does and why.** Custom Actions are the buttons users
click to move a claim through its lifecycle. Unlike "Workflows" which
fire on record events (add/edit), Custom Actions fire when a user
explicitly clicks a button. This is where approve/reject decisions get
captured — the user is acting with authority, and the click is the
record of their authorising action.

We use Custom Actions (instead of Creator's native Approval Process
feature) for two reasons:

- **Deluge flexibility.** Approval Process runs a fixed Deluge shape
  (On Approve / On Reject per tier); Custom Actions let us run arbitrary
  logic including threshold checks that decide whether to finalise or
  escalate.
- **Unified model.** All user-initiated transitions become Custom Actions
  — one concept to learn, one place to look when debugging.

`LM_Approve` is the first of four buttons. It's visible only when
`status == "Pending LM Approval"`. When clicked, it either finalises the
claim (if amount is ≤ the HoD threshold i.e. R10,000 — LM has authority)
or escalates to HoD.

> **Aside — why does LM authority reach R10,000 here?** In Part A's
> simplest form, "Tier 2 max" means "the largest amount LM can approve
> without escalating to HoD at all". If your policy is "LM finalises
> up to R999.99, anything above always goes to HoD", set `t2_max` in
> the Deluge below to `999.99`. The threshold table separates
> **routing thresholds at submit** from **approval authority at click
> time**, so tune them independently. For Pass 1 we use the simplest
> read of the config: LM authority = Tier 2 max.

**Navigate to:** **Workflow → Custom Actions → expense_claims → + Add New
Custom Action**.

![Screenshot: new Custom Action dialog](./screenshots/a4-custom-action-new.png)

**Set these values in the dialog:**

- **Display Name:** `LM Approve`
- **Link Name:** `LM_Approve` (Creator auto-derives from Display Name;
  verify it matches exactly — this name is what you'll see in Report
  layout configuration later)
- **Show In:** check both **Report** and **Form Details** (button appears
  as a row-action in any Report listing claims, and as a button inside
  the record view)
- **Criteria:** `status == "Pending LM Approval"` (the button only appears
  when the claim is in this exact status — this is the visibility gate)
- **Success Message:** `LM approval recorded.` (shown as a toast when the
  action completes)
- **Script:** click **Click to write Deluge → Free-flow script** and paste:

```deluge
// Pull Tier 2 max so we know whether LM can finalise
t2 = approval_thresholds[tier_name == "Tier 2" && Active == true];
t2_max = if(t2.count() > 0, t2.max_amount_zar, 0.0);

// Record the approver identity (used by Pass 3 dual-key control too)
input.Key_1_Approver = zoho.loginuser;

// Audit row — the LM's action of approving, regardless of outcome
insert into approval_history
[
    added_user = zoho.loginuser
    claim      = input.ID
    action_1   = "Approved (LM)"
    timestamp  = zoho.currenttime
    actor_role = zoho.loginuser
    notes      = "Line manager approval"
];

// Decide whether this finalises or escalates
if(input.amount_zar > t2_max)
{
    input.status = "Pending HoD Approval";
}
else
{
    input.status = "Approved";
}
```

**Save the action.**

**Walkthrough in plain English.**

- We always write the `Approved (LM)` audit row first. Even if the claim
  escalates to HoD on the next line, the history must show "LM did
  approve, then it escalated". Approving is a distinct event from
  finalising.
- `Key_1_Approver = zoho.loginuser` captures *who* gave the first
  approval. In Pass 1 this is informational only; in Pass 3 it becomes
  the "you can't approve Key 2 on a claim you already approved as Key 1"
  control.
- The `if(amount > t2_max)` branch: over R10,000 escalates to HoD; at or
  below R10,000 goes straight to `Approved` (LM has final say).

**Verify.** Enter View mode, open a `Pending LM Approval` claim you
created earlier, and look for an **LM Approve** button (either at the
top of the record view or as a row action in the Claims list). Click it.

- For a claim with `amount_zar = 500`: status should flip to `Approved`,
  a new audit row should show `Approved (LM)`, `Key_1_Approver` should
  be your username.
- For a claim with `amount_zar = 5000`: status flips to
  `Pending HoD Approval`, audit row shows `Approved (LM)`, the
  **LM Approve** button disappears (criteria no longer matches) and an
  **HoD Approve** button appears in its place (you're about to set it
  up in A.5).

---

## A.5. Custom Action — `HoD_Approve`

**What this step does and why.** The final-approval button for claims
that have escalated past the LM tier. In Pass 1 there is no further tier
above HoD, so every successful HoD_Approve click results in `Approved`.

**Navigate to:** **Workflow → Custom Actions → expense_claims → + Add New
Custom Action**.

**Values:**

- **Display Name:** `HoD Approve`
- **Link Name:** `HoD_Approve`
- **Show In:** Report + Form Details
- **Criteria:** `status == "Pending HoD Approval"`
- **Success Message:** `HoD approval recorded. Claim approved.`
- **Script:**

```deluge
// If the claim reached HoD without an LM approval (e.g. it routed
// directly to HoD because amount_zar was above the LM authority on
// submit), record the HoD as the Key 1 approver too — this keeps the
// Pass 3 dual-key invariant well-formed (there's always a Key 1).
if(input.Key_1_Approver == null || input.Key_1_Approver == "")
{
    input.Key_1_Approver = zoho.loginuser;
}

// Audit row
insert into approval_history
[
    added_user = zoho.loginuser
    claim      = input.ID
    action_1   = "Approved (HoD)"
    timestamp  = zoho.currenttime
    actor_role = zoho.loginuser
    notes      = "Head of Department approval"
];

// HoD is the highest tier in Pass 1 — always finalise
input.status = "Approved";
```

**Save.**

**Walkthrough in plain English.**

- The `if(Key_1_Approver == null ...)` block handles the case where a
  claim reached HoD without ever going through LM (amount above
  R999.99 at submit time). We want *some* user recorded as Key 1 for
  Pass 3's dual-key check to have something to compare against; if
  there's no LM approver on record, the HoD fills that slot.
- The audit row and status flip are straightforward.

**Verify.** Take a claim that's in `Pending HoD Approval` and click
**HoD Approve**. Status becomes `Approved`. Audit shows two rows
(`Submitted`, `Approved (HoD)`) or three (`Submitted`, `Approved (LM)`,
`Approved (HoD)`) depending on whether it passed through LM.

---

## A.6. Custom Action — `Reject_Claim`

**What this step does and why.** A rejection button that's visible at
either approval tier. The rejecting user must first fill in
`approval_comments` on the claim (that's the rejection reason), then
click Reject. The claim transitions to `Rejected` and the reason is
captured in the audit row.

**Navigate to:** **Workflow → Custom Actions → expense_claims → + Add New
Custom Action**.

**Values:**

- **Display Name:** `Reject`
- **Link Name:** `Reject_Claim`
- **Show In:** Report + Form Details
- **Criteria:** `status == "Pending LM Approval" || status == "Pending HoD Approval"`
- **Success Message:** `Claim rejected.`
- **Script:**

```deluge
// Require a comment on the claim before allowing rejection
if(input.approval_comments == null || input.approval_comments == "")
{
    alert "Please enter a reason in 'Approval Comments' before rejecting.";
    return;
}

input.status = "Rejected";

insert into approval_history
[
    added_user = zoho.loginuser
    claim      = input.ID
    action_1   = "Rejected"
    timestamp  = zoho.currenttime
    actor_role = zoho.loginuser
    notes      = "Rejected: " + input.approval_comments
];
```

**Save.**

**Walkthrough in plain English.**

- `alert ... ; return;` is how you abort a Custom Action without
  changing anything. The user sees the alert and stays on the claim.
- `return` (without a value) exits the script cleanly. The claim's
  state is untouched; nothing is written.
- The rejection reason is prefixed with `"Rejected: "` in notes so a
  future reader grepping for rejections can find them without
  parsing every `action_1` field.

**Operational detail.** The same `Reject` button serves both LM and HoD
— a rejection at either tier is a rejection. If your audit policy
requires distinguishing "rejected by LM" from "rejected by HoD", extend
the `action_1` picklist on `approval_history` with `Rejected (LM)` and
`Rejected (HoD)` values and branch on `input.status` before writing:

```deluge
rejection_label = if(input.status == "Pending LM Approval", "Rejected (LM)", "Rejected (HoD)");
// then use rejection_label as the action_1 value
```

Not required for Pass 1; flagging here so you can harden later if
wanted.

---

## A.7. Custom Action — `Request_Clarification`

**What this step does and why.** Sometimes an approver doesn't want to
approve *or* reject — they want the Employee to edit and resubmit with
more info. This button bounces the claim back to `Resubmitted` status
with the approver's comment attached. When the Employee edits and saves,
the On Edit workflow (Pass 2) re-routes through the tiers.

In Pass 1 we don't have an On Edit re-routing workflow yet, so clicking
Request Clarification in Pass 1 leaves the claim in `Resubmitted` until
the Employee manually re-submits (by changing status back to `Submitted`
or editing and saving). Pass 2 adds the auto-re-routing logic.

**Navigate to:** **Workflow → Custom Actions → expense_claims → + Add New
Custom Action**.

**Values:**

- **Display Name:** `Request Clarification`
- **Link Name:** `Request_Clarification`
- **Show In:** Report + Form Details
- **Criteria:** `status == "Pending LM Approval" || status == "Pending HoD Approval"`
- **Success Message:** `Clarification requested. Sent back to the submitter.`
- **Script:**

```deluge
if(input.approval_comments == null || input.approval_comments == "")
{
    alert "Please enter a message in 'Approval Comments' explaining what clarification is needed.";
    return;
}

input.status = "Resubmitted";

insert into approval_history
[
    added_user = zoho.loginuser
    claim      = input.ID
    action_1   = "Reconsidered (Key 1)"
    timestamp  = zoho.currenttime
    actor_role = zoho.loginuser
    notes      = "Clarification requested: " + input.approval_comments
];
```

**Save.**

**Walkthrough in plain English.**

- Identical comment-required guard as Reject — we never want a silent
  bounce-back.
- `action_1 = "Reconsidered (Key 1)"` is the closest-fitting existing
  picklist value. If you extend the picklist with a `Clarification
  Requested` value, swap it in.
- The claim is now in `Resubmitted` status. In Pass 1 the Employee has
  to manually trigger re-evaluation; in Pass 2 the On Edit workflow
  catches this status and re-routes automatically.

---

## A.8. Blueprint — lifecycle display

**What this step does and why.** Your app has a blueprint
(`expense_claim_approval_workflow`) with nine stages — Claim Submitted →
Claim Under Review → Claim Approved / Rejected / etc. It's a pretty chart
intended to show users where their claim is in the lifecycle at a glance.

**The blueprint is display-only in this guide.** The source of truth for
routing decisions is the `status` field; the blueprint just visualises a
projection of status. We keep it this way because blueprints are more
rigid than Deluge — you can't run arbitrary code on a transition — and
we want all routing logic in one place.

So we add a small On Edit → On Success snippet that *syncs* the
blueprint stage to whatever the `status` field says.

**Navigate to:** **Workflow → Form Actions → expense_claims → On Edit →
On Success → Click to write Deluge → Free-flow script**.

> If there's already a script here from previous work, **append** — do
> not replace what's there.

**Paste (or append):**

```deluge
// Mirror the status field into the blueprint's current stage so the
// lifecycle chart advances in lock-step with routing decisions.
if(input.status == "Approved")
{
    input.currentStage = "Claim Approved";
}
else if(input.status == "Rejected")
{
    input.currentStage = "Claim Rejected";
}
else if(input.status == "Resubmitted")
{
    input.currentStage = "Claim Under Review";
}
else if(input.status == "Pending LM Approval" || input.status == "Pending HoD Approval")
{
    input.currentStage = "Claim Under Review";
}
```

**Save.**

**Walkthrough in plain English.**

- `input.currentStage` is Creator's standard handle for the blueprint's
  active stage field. If your Creator version reports `currentStage` as
  unresolved when saving, open **Workflow → Blueprints → Expense Claim
  Approval Workflow → Settings** and check the configured "stage field"
  name — use that name instead of `currentStage`.
- All `Pending ...` statuses collapse to `Claim Under Review` on the
  blueprint — the blueprint is coarser than the status picklist, which
  is fine for user-facing display.
- This script runs on every edit (including approvals / rejections /
  clarifications), so the blueprint stays in sync without any explicit
  trigger in the Custom Actions above.

> **Blueprint transition caveat.** The `-development.ds` blueprint has
> an explicit transition graph (e.g. `Claim Submitted → Claim Under
> Review → Claim Approved`). Directly assigning `input.currentStage`
> bypasses that graph. Most Creator versions allow it; a minority enforce
> the transition graph and will reject `currentStage = "Claim Rejected"`
> if there's no valid transition from the current stage. If you see
> errors about "invalid blueprint transition" when saving a claim, treat
> this nudge as optional — remove it and rely on the `status` field
> alone for lifecycle display. The approval logic does not depend on
> the blueprint.

**Verify.** After approving a claim (from A.4 or A.5), open the claim's
detail view. Near the top you should see the blueprint chart with
**Claim Approved** highlighted as the current stage. For a Pending claim,
**Claim Under Review** should be highlighted.

---

## A.9. Smoke tests — prove Pass 1 works

Run these three scenarios end-to-end. Each should produce the exact
outcomes listed. If anything differs, stop and debug before adding more
— a broken core is harder to debug once Pass 2 logic is layered on top.

### Scenario 1 — small claim, direct LM approval

1. **View mode → Expense Claims → + Add.** Fill in: `Email` =
   your email, `Submission_Date` = today, `amount_zar` = `500`,
   `Department_ID` = any active department, `Client_ID` = optional.
2. **Expected after save:**
   - `Claim_Reference` = `EXP-<id>`
   - `Claim_Submission_Timestamp` = current time
   - `Retention_Expiry_Date` = today + 5 years
   - `status` = `Pending LM Approval`
   - Approval History shows one row with `action_1 = "Submitted"` and
     notes containing "Routed to: Pending LM Approval"
   - Blueprint displays `Claim Under Review`
3. Open the claim. Click **LM Approve**.
4. **Expected:**
   - `status` = `Approved`
   - `Key_1_Approver` = your username
   - Approval History now has two rows: `Submitted`, `Approved (LM)`
   - Blueprint displays `Claim Approved`

### Scenario 2 — mid-sized claim, LM escalates to HoD

1. **+ Add** another claim with `amount_zar` = `5000`, other fields
   valid.
2. **Expected after save:** `status` = `Pending HoD Approval` (above
   Tier 1 max directly, routed to HoD by tier routing).
3. Click **HoD Approve**.
4. **Expected:** `status` = `Approved`; `Key_1_Approver` = you;
   Approval History has `Submitted` and `Approved (HoD)`.

> **What about claims that go LM → HoD?** Those happen when you submit
> at `amount_zar` between R0 and R999.99, and then LM approves. But Pass
> 1's routing sends anything ≤ R999.99 to LM and anything > R999.99 to
> HoD at submit, so LM → HoD via click only happens if you **change the
> amount** after submit and before LM clicks. You can still trigger it
> deliberately: submit at `amount_zar = 100`, then in the record edit
> `amount_zar = 5000` and save, then click LM Approve — now `amount_zar
> > t2_max` so LM_Approve escalates instead of finalising. This is edge
> behaviour; treat it as "expected but rare" until Pass 3.

### Scenario 3 — rejection with comment

1. Add a claim with valid values.
2. Open the claim and, in the same edit view, **type a rejection reason
   into `approval_comments`** (e.g. "Missing receipts"). Save.
3. Click **Reject**.
4. **Expected:** `status` = `Rejected`; Approval History has a row with
   `action_1 = "Rejected"` and notes containing your reason; Blueprint
   shows `Claim Rejected`.

### Scenario 3b — rejection attempted without a comment

1. Add another claim. Open it. Do **not** fill `approval_comments`.
2. Click **Reject**.
3. **Expected:** Alert popup "Please enter a reason...". Claim state
   unchanged (still `Pending LM Approval`). No audit row written.

**If all four scenarios pass, Pass 1 is complete.** Commit a snapshot of
the live app (export `.ds` again so the development.ds reflects the new
state) before starting Pass 2.

---

## A.10. Optional hardening (recommended before Pass 2)

None of these are required for Pass 1 to work, but each is a small
one-time change that closes a class of mistake.

1. **Make `status` read-only on the form.** Prevents users from
   hand-editing the dropdown to bypass the approval flow. **Design →
   expense_claims → click the `status` field → Field Properties →
   Advanced → "Disable in form view"** (name varies across Creator
   versions; look for a "read-only" or "display only" toggle). Approval
   logic goes through the Custom Actions; the dropdown is display-only.
2. **Claim_Reference uniqueness.** Prevents two claims from ever sharing
   the same `EXP-<ID>` (shouldn't happen given how we derive it, but
   belt-and-braces). **Design → expense_claims → click `Claim_Reference`
   → Field Properties → Advanced → "Do not allow duplicate values"** →
   save. Add a unique index if prompted.
3. **Role gate the approval buttons** (only meaningful after Pass 2's
   role wiring — come back here then). Each Custom Action has a
   **Permissions** tab; restrict **LM_Approve** to `Line Manager` and
   **HoD_Approve** to `HoD`. The in-script logic is the primary gate;
   the permissions gate just keeps the button out of sight for users
   who can't use it.

---

# Part B — Pass 2: Self-approval bypass + SLA enforcement

Part A wired the core approval loop, but two governance rules are
unimplemented:

- **Self-approval bypass** (King IV Principle 1): if the submitter is
  themselves a Line Manager, the LM tier is skipped and the claim goes
  straight to HoD. A Line Manager cannot approve their own claim.
- **SLA enforcement**: pending claims older than 2 days trigger a
  reminder; pending claims older than 3 days auto-escalate to the next
  tier (actor = `"SYSTEM"` in the audit trail).

Both require internal-role plumbing that wasn't needed in Pass 1.
**B.0 is mandatory before any Pass 2 Deluge will work.**

---

## B.0. Critical: which panel to use for roles

**This paragraph is load-bearing.** Zoho Creator has two unrelated
concepts both often called "permissions":

- **Internal Roles** live under **Users & Control → Roles**. These are
  the roles the Deluge below inspects via
  `thisapp.permissions.isUserInRole("Line Manager")`. Examples:
  Employee, Line Manager, HoD, Finance.
- **Portal User Permissions** (the panel whose header reads
  "Portal User Permissions — Add and manage portal users' permission for
  this application") is for **external** users — people who log in via
  a customer/vendor/partner portal. This is **not** where Line Manager
  and HoD live.

**If you wire your LM and HoD users as Portal users, the self-approval
bypass Deluge will silently never match.** The check returns `false`
for every submitter and every claim falls through to the normal tier
routing — the bypass never fires, there's no visible error, you'll wonder
why nothing works for a day.

![Screenshot: Users & Control → Roles panel (internal roles)](./screenshots/b0-users-control-roles.png)

**How to tell you're in the right panel.** The internal-roles panel is
usually under a left-sidebar entry called **Users & Control** or
**Users & Permissions** (naming varies by Creator version). Once you
click it, you should see a sub-nav with **Users**, **Roles**,
**Permissions**, and possibly **Portal Users** as a *separate* entry.
Click **Roles**. If the right-hand panel's header mentions "portal", go
back and find the non-portal entry.

---

## B.1. Wire internal roles

**What this step does and why.** Create three named internal roles and
assign real users to them. Without users in the `Line Manager` and `HoD`
roles, the approval buttons from Part A work (anyone can click them
given permissions), but the bypass check in B.2 has nothing to detect.

**Navigate to:** **Users & Control → Roles → + Add New Role** (or the
"+" icon above the roles list).

**Create these three roles:**

1. **Employee** — name `Employee`, no special description needed. This
   is the default for anyone submitting a claim.
2. **Line Manager** — name `Line Manager`. (The string must be literal —
   the Deluge below does `isUserInRole("Line Manager")`.)
3. **HoD** — name `HoD` (short for Head of Department; exact string
   matters).

**Assign test users.** Go to **Users & Control → Users** (or the users
sub-tab). If you don't have extra test users, invite at least two:
e.g. `tester-lm@yourdomain.com` and `tester-hod@yourdomain.com`.
Zoho will email each one an invite; they need to accept before showing
as active users.

Once accepted, edit each user and assign:

- Yourself → `Employee` role (you'll submit claims as a regular user)
- `tester-lm@yourdomain.com` → `Line Manager` role
- `tester-hod@yourdomain.com` → `HoD` role

**Verify.** Back in **Users & Control → Roles**, click each role; the
"Members" tab should list the assigned user(s).

**Also verify form permissions.** Click **Users & Control → Permissions
→ expense_claims**. You should see a table of roles × operations
(Create, Read, Update, Delete) and also report-level permissions. At
minimum:

- `Employee`: Create on `expense_claims`; Read limited to **own
  records** (the radio dial / scope selector on the Read row).
- `Line Manager`: Read on all `expense_claims`; Update on
  `expense_claims` (needed to change `status` via Custom Action).
- `HoD`: same as Line Manager.

(Fine-grained scoping — e.g. LM can only see their department's claims
— is beyond Pass 2 scope. Flag it for a later governance pass.)

---

## B.2. Form Action patch — self-approval bypass

**What this step does and why.** In Part A, the On Add → On Validate
routed every claim to `Pending LM Approval` or `Pending HoD Approval`
based purely on amount. Pass 2 adds one rule: **if the submitter is in
the Line Manager role, skip the LM tier** — the claim goes straight to
HoD regardless of amount. This is the King-IV-aligned self-approval
prevention control.

The check must happen *before* the amount-based routing so it can
override it. We're patching the existing On Validate script to add a
bypass check at the top, followed by the existing logic in an `else`
branch.

**Navigate to:** **Workflow → Form Actions → expense_claims → On Add →
On Validate → Edit Deluge** (opens the script you pasted in A.2).

**Replace the entire contents with:**

```deluge
// --- Required-field checks (unchanged from Pass 1) --------------------
if(input.Email == null || input.Email == "")
{
    alert "Email is required.";
    cancel submit;
}
if(input.Submission_Date == null)
{
    alert "Submission Date is required.";
    cancel submit;
}
if(input.amount_zar == null || input.amount_zar <= 0)
{
    alert "Amount (ZAR) must be greater than zero.";
    cancel submit;
}
if(input.Department_ID == null)
{
    alert "Department is required.";
    cancel submit;
}

// --- Submission metadata (unchanged) ----------------------------------
input.Claim_Submission_Timestamp = zoho.currenttime;
input.Retention_Expiry_Date      = input.Submission_Date.addYear(5);

// --- Self-approval bypass (NEW in Pass 2) -----------------------------
// If the submitter is themselves a Line Manager, skip the LM tier
// entirely and route to HoD. Also flagged in the initial audit row
// written in On Success so auditors can see the bypass fired.
is_lm_submitter = thisapp.permissions.isUserInRole("Line Manager");

if(is_lm_submitter)
{
    input.status = "Pending HoD Approval";
}
else
{
    // --- Tier routing by amount (unchanged from Pass 1) ---------------
    t1 = approval_thresholds[tier_name == "Tier 1" && Active == true];
    t2 = approval_thresholds[tier_name == "Tier 2" && Active == true];

    t1_max = if(t1.count() > 0, t1.max_amount_zar, 0.0);
    t2_max = if(t2.count() > 0, t2.max_amount_zar, 0.0);

    if(input.amount_zar <= t1_max)
    {
        input.status = "Pending LM Approval";
    }
    else
    {
        input.status = "Pending HoD Approval";
    }
}
```

**Save.**

**Now patch the On Success audit row** to record when the bypass fired.
Navigate to **Workflow → Form Actions → expense_claims → On Add → On
Success** and replace the script with:

```deluge
// --- Auto-generate claim reference (unchanged) ------------------------
if(input.Claim_Reference == null || input.Claim_Reference == "")
{
    input.Claim_Reference = "EXP-" + input.ID.toString();
}

// --- Seed audit trail, flagging bypass (UPDATED in Pass 2) ------------
// The action_1 picklist already declares a "Submitted (Self-approval bypass)"
// value — use it verbatim so auditors can filter on the exact string.
is_lm_submitter = thisapp.permissions.isUserInRole("Line Manager");
action_label = if(is_lm_submitter, "Submitted (Self-approval bypass)", "Submitted");
submission_note = "Claim submitted. Routed to: " + input.status;

insert into approval_history
[
    added_user = zoho.loginuser
    claim      = input.ID
    action_1   = action_label
    timestamp  = zoho.currenttime
    actor_role = zoho.loginuser
    notes      = submission_note
];
```

**Save.**

**Walkthrough in plain English.**

- `thisapp.permissions.isUserInRole("Line Manager")` is Creator's
  built-in role check. It returns `true` if the currently-logged-in user
  is in the specified internal role — hence B.0's insistence on internal
  vs portal.
- The bypass evaluates *first*. If the submitter is an LM, we go
  directly to HoD; otherwise we fall through to the normal amount-based
  routing.
- The On Success audit note gets suffixed with the bypass flag when
  applicable, giving auditors a searchable marker for bypass events.

---

## B.3. Form Action — On Edit → On Success (resubmission re-routing)

**What this step does and why.** When a claim is `Resubmitted` (either
via the Request Clarification button from A.7 or via the Employee
editing after rejection), Pass 2 wants it to re-enter the routing
automatically, respecting the same bypass rule. Without this, a
resubmitted claim sits in `Resubmitted` forever until a human manually
flips the status.

We also want to **track the resubmission version** so auditors can see
"this is v3 of claim EXP-12345".

**Navigate to:** **Workflow → Form Actions → expense_claims → On Edit →
On Success**. There should already be the blueprint display-sync snippet
from A.8. **Append** this below it:

```deluge
// --- Resubmission re-routing (NEW in Pass 2) --------------------------
// When a claim's status becomes "Resubmitted", bump the version,
// re-run the bypass-aware routing, and audit the resubmission.
if(input.status == "Resubmitted")
{
    // Bump version counter. (Add a `Version` Number field on expense_claims
    // if it doesn't exist — default value 1.)
    if(input.Version == null)
    {
        input.Version = 1;
    }
    else
    {
        input.Version = input.Version + 1;
    }
    input.Submission_Date = zoho.currenttime;

    // Re-run bypass-aware routing
    if(thisapp.permissions.isUserInRole("Line Manager"))
    {
        input.status = "Pending HoD Approval";
        resubmit_route_note = "Resubmitted v" + input.Version + " (self-approval bypass)";
    }
    else
    {
        t1 = approval_thresholds[tier_name == "Tier 1" && Active == true];
        t1_max = if(t1.count() > 0, t1.max_amount_zar, 0.0);
        if(input.amount_zar <= t1_max)
        {
            input.status = "Pending LM Approval";
            resubmit_route_note = "Resubmitted v" + input.Version + " (routed to LM)";
        }
        else
        {
            input.status = "Pending HoD Approval";
            resubmit_route_note = "Resubmitted v" + input.Version + " (routed to HoD)";
        }
    }

    // Audit row for the resubmission itself
    insert into approval_history
    [
        added_user = zoho.loginuser
        claim      = input.ID
        action_1   = "Resubmitted"
        timestamp  = zoho.currenttime
        actor_role = zoho.loginuser
        notes      = resubmit_route_note
    ];
}
```

**Save.**

**Walkthrough in plain English.**

- The `if(status == "Resubmitted")` guard means this block only fires
  on resubmission; normal edits (e.g. an approver clicking LM Approve)
  don't trigger it.
- `Version` increments on every resubmission. First submission starts
  at 1 (handled in A.0 if you added the field with a default) or gets
  bumped to 1 here on first resubmission if it was null.
- `Submission_Date` is updated so SLA calculations (next section) reset
  — a resubmitted claim gets a fresh clock.
- The re-routing block mirrors B.2: bypass check first, fall through to
  amount-based routing.
- One audit row per resubmission, carrying the version number and the
  routing outcome.

**Prerequisite field check.** `Version` is one of the fields listed in
A.0.2. If you added it then (with default value `1`), you're fine —
skip ahead. If you deferred adding it, go back to A.0.2 now: Design →
expense_claims → drag a Number field → Link Name `Version` → default
value `1` → save.

---

## B.4. Scheduled Action — SLA daily enforcement

**What this step does and why.** Pending claims that sit too long are a
governance failure: they indicate either an unresponsive approver or a
claim that fell through the cracks. Our SLA policy is:

- **Day 2:** send the current approver a reminder email (audit-logged).
- **Day 3:** auto-escalate `Pending LM Approval` → `Pending HoD Approval`
  with `actor = "SYSTEM"` in the audit trail. (HoD is the top tier in
  this MVP, so `Pending HoD Approval` at day 3 gets a recorded warning
  but no further auto-escalation.)

A **Scheduled Action** (Creator's cron equivalent) runs this check once
a day and applies the rules to every pending claim.

**Navigate to:** **Workflow → Schedules → + Add New Schedule** (entry
may also be called **Scheduled Actions** or **Scheduled Workflows**
depending on Creator version).

![Screenshot: Schedule configuration panel](./screenshots/b4-schedule-new.png)

**Configure the schedule:**

- **Name:** `SLA Enforcement Daily`
- **Schedule frequency:** Daily
- **Time:** `06:00` (early morning, before the workday — choose a time
  that fits your timezone; the schedule runs in the app's configured
  timezone, which is `Africa/Johannesburg` per the BRD)
- **Criteria / Filter:** select the form `expense_claims` and set the
  filter to `status == "Pending LM Approval" || status == "Pending HoD Approval"`
  (this limits the run to pending claims only — no point scanning
  Approved or Rejected records)
- **Script:** **Free-flow script** and paste:

```deluge
// NOTE on the iterator variable: Creator's Scheduled Actions iterate over
// every record matching the filter and expose the current record as
// `input` (same convention as Form Actions). If your Creator version
// uses a different name (some older tenants use `record`), the first
// `input.Submission_Date` line below will fail to resolve — rename all
// `input.` references accordingly.

// Compute days since last submission — counts weekends; tighten if
// business-day calculation is required (needs custom date arithmetic).
age_days = daysBetween(input.Submission_Date, zoho.currentdate);

// --- Day 2: reminder -------------------------------------------------
if(age_days == 2)
{
    // Identify which role currently owns the claim
    approver_role_note = if(input.status == "Pending LM Approval", "Line Manager", "HoD");

    // action_1 "Warning" is already declared in the picklist; re-use it
    // for day-2 reminder rows. Distinguish from SLA breach via notes.
    insert into approval_history
    [
        added_user = "SYSTEM"
        claim      = input.ID
        action_1   = "Warning"
        timestamp  = zoho.currenttime
        actor_role = "SYSTEM"
        notes      = "SLA day-2 reminder — claim awaiting " + approver_role_note
    ];

    // (Email notification left for a later pass — see Deferred.)
}

// --- Day 3+: auto-escalate LM → HoD ----------------------------------
if(age_days >= 3 && input.status == "Pending LM Approval")
{
    input.status = "Pending HoD Approval";

    // "Escalated (SLA Breach)" is the declared picklist value — use
    // verbatim.
    insert into approval_history
    [
        added_user = "SYSTEM"
        claim      = input.ID
        action_1   = "Escalated (SLA Breach)"
        timestamp  = zoho.currenttime
        actor_role = "SYSTEM"
        notes      = "SLA day-3 auto-escalation — LM tier timed out, routed to HoD"
    ];
}

// --- Day 3+: HoD timeout (log-only; no higher tier in MVP) ------------
else if(age_days >= 3 && input.status == "Pending HoD Approval")
{
    // Only log the warning once per day; protect against duplicate rows
    // by checking whether a warning has already been logged today.
    already_warned = approval_history[
        claim == input.ID &&
        action_1 == "Warning" &&
        notes.startsWith("SLA day-3 HoD overdue") &&
        timestamp >= zoho.currentdate
    ];

    if(already_warned.count() == 0)
    {
        insert into approval_history
        [
            added_user = "SYSTEM"
            claim      = input.ID
            action_1   = "Warning"
            timestamp  = zoho.currenttime
            actor_role = "SYSTEM"
            notes      = "SLA day-3 HoD overdue — day " + age_days + ", no higher tier in MVP"
        ];
    }
}
```

**Save the script and the schedule.**

**Walkthrough in plain English.**

- `daysBetween(a, b)` returns an integer number of days. `input` is one
  record from the filtered set (the schedule iterates over every
  matching claim).
- The day-2 branch writes an audit row only. In a later pass we'll
  add a `sendmail` call using a named template; leaving it out now
  keeps Pass 2 email-free (emails belong in their own pass with the
  18-template contract from the BRD).
- The day-3 branch flips status and logs `actor_role = "SYSTEM"` —
  this is the signature auditors look for: a state change by the
  system rather than a human.
- The day-3 HoD-tier branch logs a warning but doesn't escalate (no
  tier above HoD in this MVP). The `already_warned` guard prevents
  flooding the audit trail with duplicate warnings — one warning row
  per day.
- `action_1` values `Reminder Sent`, `Escalated`, and `SLA Warning` may
  not be in your picklist yet. Add them: **Design → approval_history →
  action_1 field → Edit Choices → Add Choice** for each missing value.

> **Picklist reminder.** The Deluge above uses only `action_1` values
> already declared in `-development.ds`: `Warning` (for reminders and
> HoD-overdue) and `Escalated (SLA Breach)` (for LM→HoD auto-escalation).
> The `approval_history.action_1` picklist also has `others option = true`
> set in the schema, which means arbitrary strings are accepted if you
> want finer categorisation later (e.g. `Reminder Sent` vs `Warning`) —
> but re-using declared values keeps reporting filters clean.

---

## B.5. Smoke tests for Pass 2

### Scenario 4 — self-approval bypass

1. Log out of your current user (the one in the `Employee` role).
   Log in as the test user assigned to the `Line Manager` role.
2. **+ Add** a new claim with `amount_zar` = `500` (well below Tier 1
   max — in Pass 1 this would route to LM).
3. **Expected:** `status` = `Pending HoD Approval` (bypass fired).
   Approval History shows `Submitted` with notes containing
   "self-approval bypass".
4. Log back in as the Employee-role user. Open the claim. The
   **LM Approve** button should **not** appear (criteria doesn't match).
   The **HoD Approve** button should appear, and only the HoD-role user
   (per B.1 permissions) should be able to click it productively.

### Scenario 5 — SLA day-3 auto-escalation

The schedule runs daily in production, but you can't wait three days
for a smoke test. Two options:

- **(Preferred) Manual trigger.** In the Schedules panel, find
  `SLA Enforcement Daily` and look for a **Run Now** button (Creator
  exposes this for testing). Then:
  1. Create a claim, let it land in `Pending LM Approval`.
  2. Edit the claim's `Submission_Date` directly to a date 3 days ago.
     (Back-date via the Design-mode record editor, or via a one-off
     Deluge statement.)
  3. Click **Run Now** on the schedule.
  4. **Expected:** status flips to `Pending HoD Approval`; Approval
     History has a `SYSTEM` row with `action_1 = "Escalated"` and the
     day-3 notes.
- **(Fallback) Wait.** Create a claim and let three days pass. The
  schedule fires at its configured time.

### Scenario 6 — resubmission re-routing

1. Log in as Employee-role user. Submit a claim at `amount_zar` = 500;
   status routes to `Pending LM Approval`.
2. Log in as Line-Manager-role user. Open the claim, type a clarification
   reason into `approval_comments`, click **Request Clarification**.
3. Status should now be `Resubmitted`.
4. Log back in as Employee. Open the claim, edit and save (change any
   field, or just re-save).
5. **Expected:** On-Edit → On-Success fires, `Version` increments to 2,
   `Submission_Date` becomes today, status re-routes to
   `Pending LM Approval` (bypass doesn't apply — submitter is Employee,
   not LM). New audit row with `action_1 = "Resubmitted"` and notes
   including "v2".

---

# Part C — Pass 3 (deferred — not implemented in this guide)

Pass 3 introduces the **dual-approval / segregation-of-duties** control
for high-value claims. Scope outline:

- **Re-activate `Dual Threshold` config row.** Flip `Active` to `true`,
  confirm `Dual_Threshold_ZAR` (R100,000 or your organisation's policy
  number).
- **Extend tier routing** in On Add → On Validate and On Edit → On
  Success: when `amount_zar >= Dual_Threshold_ZAR`, set status to
  `Pending Second Key` (bypasses both LM and HoD tiers).
- **Extend LM_Approve and HoD_Approve Custom Actions**: after approving,
  check whether the claim is over the dual threshold; if yes, set status
  to `Pending Second Key` instead of `Approved`.
- **New Custom Action `Key_2_Approve`**: visible only when
  `status == "Pending Second Key"`. Deluge enforces
  `Key_1_Approver != zoho.loginuser` (the person approving now must be
  different from the Key 1 approver). Writes `Key_2_Approver`, flips
  status to `Approved`, writes audit row.
- **Update `Reject` and `Request_Clarification` criteria** to include
  `|| status == "Pending Second Key"` so those actions remain available
  at the second-key stage.

A dedicated design doc will cover Pass 3 before implementation. Do not
attempt Pass 3 piecemeal without the design — the dual-key control is
security-sensitive and needs an unambiguous spec.

---

# Appendix — UI paths cheatsheet

Creator's navigation occasionally renames things between releases. Here
is the conceptual map used throughout this guide:

| Concept | Likely path (may vary) |
|---|---|
| Forms & fields | **Design → Forms → &lt;form_name&gt;** |
| Form Actions (On Add / On Edit event handlers) | **Workflow → Form Actions → &lt;form_name&gt;** |
| Custom Actions (buttons) | **Workflow → Custom Actions → &lt;form_name&gt;** |
| Scheduled Actions | **Workflow → Schedules** (or "Scheduled Actions") |
| Blueprints | **Workflow → Blueprints** |
| Internal Roles | **Users & Control → Roles** (NOT Portal User Permissions) |
| Internal Users | **Users & Control → Users** |
| Form-level permissions by role | **Users & Control → Permissions → &lt;form_name&gt;** |
| Portal users (external) | **Access → Portal Permissions** or **Portal Users** |

If your Creator shows "Actions" instead of "Custom Actions", or
"Form Workflow" instead of "Form Actions" — the functionality is
identical, just renamed.

---

# Appendix — Deluge reference quick-notes

- `input.<field>` — the current record's field value. In Form Actions,
  refers to the record being added or edited. In Custom Actions, refers
  to the record the button was clicked on.
- `input.<field> = value` — assigns the field. In On Validate, the
  assignment sticks through to save. In Custom Actions, the assignment
  sticks on the underlying record.
- `zoho.loginuser` — the current logged-in user's email address (string).
- `zoho.currenttime` — current date-time in the app's timezone.
- `zoho.currentdate` — current date in the app's timezone.
- `daysBetween(d1, d2)` — integer days from `d1` to `d2`.
- `thisapp.permissions.isUserInRole("<role>")` — boolean role check
  (internal roles only).
- `form_name[filter].field_name` — fetch field value(s) from records
  matching the filter.
- `form_name[filter].count()` — how many records match.
- `insert into form_name [ key1=val1 key2=val2 ... ]` — create a record.
  Fields not listed get defaults.
- `alert "<msg>"` — show a modal to the user. `cancel submit` (On
  Validate) or `return` (Custom Action) then stops further execution.

---

# Deferred — not in this guide

Explicitly out of scope; each deserves its own follow-up design:

- **Email notifications** — the BRD specifies 18 named templates + 1
  inline ad-hoc. This guide has zero `sendmail` calls; audit rows carry
  the information that would otherwise go in email.
- **Custom APIs** — `Get_Claim_Status`, `Get_Dashboard_Summary`,
  `Get_ESG_Summary`, `Get_SLA_Breaches`.
- **ESG fields and reporting** — `Estimated_Carbon_KG`, `ESG_Category`,
  `Carbon_Factor`, `GRI_Indicator` and their roll-up reports.
- **GL code auto-population on approval** — the BRD's query against
  `gl_accounts` and the `UNMAPPED` fallback.
- **Full role permission matrix** — portal roles (Client Rep, Vendor,
  Customer) and fine-grained internal role restrictions.
- **Payment lifecycle** — blueprint stages `Claim Processed for Payment`,
  `Claim On Hold`, `Claim Paid`, `Claim Closed` and their Finance gates.
- **Parent / child resubmission linkage** via `Parent_Claim_ID`.
- **Denormalised department/client shadow fields** for reporting
  without live lookups.
- **Audit-trail retention job** — 90-day archival from
  `approval_history` to long-term storage.

Each is a one-topic pass with its own BRD-aligned design.
