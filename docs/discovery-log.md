# Discovery Log

Runtime discoveries from Creator that contradict or extend our documented knowledge.
Each entry feeds back into CLAUDE.md, the linter, and deluge-reference.md.

---

## DL-001: Added_User only accepts zoho.loginuser or zoho.adminuser

**Date**: 2026-04-06
**Source**: Creator import error at line 1397
**Error**: `Added User in insert task can only accept zoho.loginuser or zoho.adminuser`

**What we assumed**: `zoho.adminuserid` (the admin's email address) would be valid for `Added_User` in scheduled tasks where no user is logged in.

**What Creator enforces**: `Added_User` field in `insert into` tasks ONLY accepts two values:
- `zoho.loginuser` (username of logged-in user)
- `zoho.adminuser` (username of app owner)

`zoho.adminuserid` (email of app owner) is **rejected** despite being a valid Zoho variable elsewhere.

**Root cause**: `Added_User` is a Creator system field that maps to the internal user identity, not an email address. The `*user` variants return usernames; the `*userid` variants return emails. Creator requires the username form.

**Impact**: Linter rule DG007, CLAUDE.md, sla_enforcement_daily.dg, deluge-reference.md all needed updating.

**Actions taken**:
- Fixed .ds export and .dg script: `zoho.adminuserid` -> `zoho.adminuser`
- Updated linter DG007: `VALID_ADDED_USER_VALUES = {"zoho.loginuser", "zoho.adminuser"}`
- Added to CLAUDE.md Key Deluge rules
- Added DG019 linter rule for explicit enforcement

**Lesson**: Always distinguish `zoho.*user` (username) from `zoho.*userid` (email). The `Added_User` system field requires the username form.

---

## DL-002: New fields via .ds import -- CONFIRMED WORKING

**Date**: 2026-04-06
**Source**: Import of .ds with 5 new fields

**What we tested**: Adding entirely new field definitions to forms in the .ds file.

**Result**: All 5 new fields were created in Creator on import:
- `Tier_Order` (number) on Approval_Thresholds
- `VAT_Invoice_Type` (picklist) on Expense_Claims
- `POPIA_Consent` (checkbox) on Expense_Claims
- `Retention_Expiry_Date` (date) on Expense_Claims
- `Risk_Level` (picklist) on GL_Accounts

**Implication**: The .ds import can create new form fields, not just modify existing ones. This makes the .ds a viable path for full structural deployment.

---

## DL-003: .ds import capability matrix (as of 2026-04-06)

| Change type | Works? | Tested |
|-------------|--------|--------|
| Field defaults (initial value) | YES | Round 3 |
| Field attributes (allow new entries) | YES | Round 3 |
| Permission / share_settings (readonly) | YES | Round 3 |
| Deluge workflow scripts | YES | Round 2 |
| Approval trigger conditions | YES | v0.4.0 |
| New fields on existing forms | YES | v0.4.0 |
| New validation logic in scripts | YES | v0.4.0 |
| New scheduled task logic | YES | v0.4.0 |

### NOT yet tested
- Adding entirely new forms
- Adding new workflows/approval processes
- Deleting fields or forms
- Renaming fields

---

## DL-004: Combined .ds edits can cause untraceable import failures

**Date**: 2026-04-07
**Source**: v0.5.0 import failure -- "A problem encountered while creating the application"

**What happened**: Applied 3 change types in one .ds edit (field descriptions + report removal + menu restriction = 316 deletions, 185 insertions). Creator rejected the import with a generic error and no line number.

**Root cause**: UNCERTAIN -- the error message gives no specifics. Most likely the report removal or menu restriction left a dangling reference or broke an expected structural pattern.

**Recovery**: Reverted to v0.4.0 known-good .ds, reapplied descriptions only. Import succeeded.

**Rule**: Apply .ds changes **one type at a time**, test each import separately. Never combine structural changes (report deletion, menu edits) with content changes (field descriptions) in a single .ds edit.

**Actions taken**:
- Adopted incremental branching strategy for .ds changes
- Each change type gets its own commit and import test
- Added to CLAUDE.md and ui-standards.md

**How to apply**: When editing .ds files:
1. Start from a known-good .ds (last successful import)
2. Apply ONE type of change
3. Import and verify
4. If good, commit and use as new baseline
5. Apply next change type on top

---

## DL-005: Report menu/action block edits -- unresolved, needs more research

**Date**: 2026-04-07
**Status**: UNRESOLVED
**Source**: Multiple failed imports when modifying report quickview/detailview menu blocks

**What we tried so far**:
- Removing menu items (Edit/Delete/Duplicate) from header blocks
- Removing entire `record ( ... )` blocks
- Removing `on right click ( ... )` blocks
- Matching exact Audit_Trail restricted pattern
- Single-report and multi-report changes
- All approaches produced "A problem encountered while creating the application"

**What we observed works as a workaround**:
- Creator auto-restricts reference/audit report menus when boilerplate kanban reports are removed
- Role-based report permissions in `share_settings` DO persist via .ds
- Creator UI allows direct menu restriction

**Hypothesis**: The menu/record/action blocks have mixed-whitespace formatting (tabs + spaces + trailing whitespace) that our tools don't reproduce exactly. The .ds parser may be sensitive to byte-level whitespace matching in these specific blocks.

**Next steps to investigate**:
1. Diff a known-good .ds menu block byte-for-byte against our generated version using `xxd` or similar
2. Try preserving exact original whitespace when editing (read-modify-write at byte level, not line level)
3. Try adding empty `record ( )` blocks (which Zoho generates itself) instead of removing them
4. Research whether Creator's import has an undocumented validation layer for report config blocks

**Current workaround**: Use share_settings for permissions, report removal for menu simplification, Creator UI for fine-grained menu control.

**Updated .ds import capability matrix**:

| Change type | Works? | Tested |
|-------------|--------|--------|
| Field defaults (initial value) | YES | Round 3 |
| Field attributes (allow new entries) | YES | Round 3 |
| Permission / share_settings (readonly) | YES | Round 3 |
| Deluge workflow scripts | YES | Round 2 |
| Approval trigger conditions | YES | v0.4.0 |
| New fields on existing forms | YES | v0.4.0 (5 fields) |
| New validation logic in scripts | YES | v0.4.0 |
| Field descriptions (help_text) | YES | v0.5.0 |
| Report removal (kanban/list) | YES | v0.5.0 |
| Report menu/action block edits | UNRESOLVED | v0.5.0 (needs more research) |

---

## DL-006: Report removal requires 5-point dependency chain cleanup

**Date**: 2026-04-07
**Status**: RESOLVED
**Source**: Investigation into DL-004/DL-005 root cause — orphaned references after report removal

**The 5 reference types for every report in a .ds file**:

| # | Location | Pattern | Example |
|---|----------|---------|---------|
| 1 | Report definition | `kanban/list name { ... }` in `reports` section | Report data/structure |
| 2 | Permission entries | `name={"View","Edit"}` in `share_settings > ReportPermissions` | Per-role access |
| 3 | Quickview/detailview | `report name { quickview(...) detailview(...) }` in `web > reports` | UI config with nested menu/action blocks |
| 4 | Navigation entry | `report name { icon = "..." }` in `web > menu > space > section` | Sidebar menu item |
| 5 | Page Content ZML | `linkName = 'name'` inside `Content="<zml>..."` strings | Dashboard embeds |

**Root cause of DL-004**: The original `remove_reports()` tool only handled #1 and #2 with regex. #3 was fragile (regex couldn't handle nested braces). #4 was completely missing. #5 was not checked.

**Fix**: Rewrote `remove_reports()` in `ds_editor.py` with:
- Brace-depth tracking for complete block removal (handles #1, #3, #4)
- Single-line regex for permission entries (#2)
- ZML content scanning with warnings (#5 — flagged, not auto-removed)
- Post-removal validation (zero remaining references, structural balance)

**Verified**: 14 references → 0 after removal. Brace/paren/bracket balance maintained.

**Rule**: When removing a report, ALWAYS use `ds_editor.py remove-reports` which handles the full chain. If Page Content ZML warnings appear, redesign the dashboard in Creator UI before exporting.
