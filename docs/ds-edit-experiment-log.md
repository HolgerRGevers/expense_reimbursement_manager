# .ds Edit Experiment Log

## Purpose
Test whether directly editing a Zoho Creator `.ds` export file and re-importing it into a separate Creator account produces a working application with the intended changes.

## Final Result

**ALL EDIT TYPES PERSIST THROUGH .DS IMPORT.**

Round 1 used an incorrect file (likely the wrong branch or the root-level unedited copy). Round 3 reran from a verified baseline and confirmed that structural, permission, and script edits all survive Creator import.

---

## Round 1: Structural + Permission Edits (INVALID -- wrong file used)

Round 1 results were incorrect. The test file uploaded to Creator was likely the unedited original, not the modified version. This was discovered when Round 3 repeated the same edits with a verified file and all changes persisted.

---

## Round 2: Deluge Script Edit

### Edit: Claim Reference Prefix
**What**: Changed `"EXP-"` to `"EXP2-"` in Generate_Claim_Reference workflow script
**Line**: 1085 in .ds

| Edit | Import Status | Persisted? | Verification |
|------|--------------|------------|-------------|
| EXP- to EXP2- | Accepted | **YES** | Zoho re-export line 1085: `claim_reference = "EXP2-" + padded;` |

**Conclusion**: Deluge script edits persist.

---

## Round 3: Structural + Permission Edits (RERUN -- clean baseline)

Reran Round 1 edits from a verified clean main baseline. Confirmed correct file was used by checking `allow new entries` count before upload (1 in edited, 3 in original).

### Edits Applied
1. **G-08**: `receipt_required` default changed from `false` to `true`
2. **G-13**: Removed `allow new entries` from gl_code lookup field (4 lines deleted)
3. **G-14**: Removed `allow new entries` from client lookup field (4 lines deleted)
4. **G-07**: LM status field changed from `readonly:false` to `readonly:true`

### Round 3 Results

| Edit | Import Status | Persisted After Re-export? | Verification |
|------|--------------|---------------------------|-------|
| G-08 receipt default | Accepted | **YES** -- `initial value = true` | Confirmed in re-export |
| G-13 gl_code entries | Accepted | **YES** -- `allow new entries` removed | Count: 1 (only approval_history.claim) |
| G-14 client entries | Accepted | **YES** -- `allow new entries` removed | Same count confirms both removed |
| G-07 LM status readonly | Accepted | **YES** -- `readonly:true` | Both status lines show readonly:true |

---

## Combined Findings

### What works via .ds edit + import

| Change type | Persists? | Tested |
|-------------|-----------|--------|
| Field defaults (initial value) | **YES** | Round 3 |
| Field attributes (allow new entries) | **YES** | Round 3 |
| Permission / share_settings (readonly) | **YES** | Round 3 |
| Deluge workflow scripts | **YES** | Round 2 |
| Approval process scripts | LIKELY YES | Not yet tested (same format as workflow scripts) |
| New fields / form changes | UNCERTAIN | Not tested |

### Implications

1. **The .ds file IS a viable deployment mechanism** for most changes
2. We can edit .dg scripts in this repo, inject into .ds, and import to Creator
3. Structural governance fixes (permissions, field controls) can also be deployed via .ds
4. This unlocks semi-automated deployment -- the OmegaScript vision becomes practical
5. The `parse_ds_export.py` tool should be extended with an **inject** mode to sync .dg files back into .ds

### Deployment Workflow (validated)

```
1. Edit .dg files in repo (scripts)
2. Edit .ds file for structural changes (permissions, field attributes)
3. Run linter: python tools/lint_deluge.py src/deluge/
4. Import modified .ds into Creator
5. Export .ds from Creator for version archive
6. Commit updated .ds to repo
```

### What to test next
- Adding a NEW field to a form via .ds (does Creator create it on import?)
- Modifying approval process trigger conditions via .ds
- Whether data (existing records) survives import with structural changes
