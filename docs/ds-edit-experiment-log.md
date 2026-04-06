# .ds Edit Experiment Log

## Purpose
Test whether directly editing a Zoho Creator `.ds` export file and re-importing it into a separate Creator account produces a working application with the intended changes.

## Result Summary

**Import: SUCCESS** -- Creator accepted the modified .ds file without errors.
**Edits: ALL REVERTED** -- Creator silently reverted all 4 edits on import.

This is a significant finding: **the .ds import pipeline normalises/resets field attributes and share_settings to Creator's internal defaults.** Direct .ds editing is NOT a viable path for structural or permission changes.

## Edits Made (on branch `ds-edit-experiment`)

### Edit 1: G-08 -- receipt_required default
- **Change**: `initial value = false` -> `initial value = true`
- **Risk**: Very Low

### Edit 2: G-13 -- Remove gl_code "allow new entries"
- **Change**: Removed 4-line `allow new entries` block
- **Risk**: Low

### Edit 3: G-14 -- Remove client "allow new entries"
- **Change**: Removed 4-line `allow new entries` block
- **Risk**: Low

### Edit 4: G-07 -- LM status field readonly
- **Change**: `readonly:false` -> `readonly:true` in Line Manager share_settings
- **Risk**: Low edit, critical governance fix

## Results

| Edit | Import Status | Persisted After Re-export? | Notes |
|------|--------------|---------------------------|-------|
| G-08 receipt default | Accepted | **NO** -- reverted to `initial value = false` | Creator resets field defaults on import |
| G-13 gl_code entries | Accepted | **NO** -- `allow new entries` re-added | Creator re-adds lookup "Add New" on import |
| G-14 client entries | Accepted | **NO** -- `allow new entries` re-added | Same behaviour as G-13 |
| G-07 LM status readonly | Accepted | **NO** -- reverted to `readonly:false` | Creator resets share_settings permissions on import |

## Lessons Learned

### What works
1. Creator accepts modified .ds files without import errors
2. The .ds format is syntactically tolerant of edits (no checksum/hash validation)
3. The upload-import pipeline does not reject files with missing blocks

### What does NOT work
1. **Field attribute changes** (defaults, allow new entries) are reset by Creator's import normalisation
2. **Permission/share_settings changes** are reverted to Creator's internal state
3. Creator treats the .ds import as a **structural scaffold** -- it rebuilds field properties and permissions from its own metadata, ignoring .ds overrides

### Implications for the Governance Remediation Plan
- **All 16 gaps must be fixed in the Creator UI**, not via .ds file edits
- The .ds file remains useful for:
  - Version archiving (read-only reference)
  - Disaster recovery (full app rebuild on fresh account)
  - Script extraction (Deluge code IS preserved -- verified by working workflows)
- For script changes: edit `.dg` files in this repo, paste into Creator UI
- For structural changes (fields, permissions, defaults): must be done in Creator Settings

### What to try next
- **UNCERTAIN**: Whether Creator preserves Deluge script edits in the .ds on import (our experiment only tested structural/permission changes, not script code changes)
- A follow-up experiment could modify an embedded workflow script in the .ds and test whether that change persists after import
