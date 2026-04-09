# Expense Reimbursement Manager — Project Memory

## OmniScript Rules (ALWAYS follow these)
1. If uncertain about any part of the answer, explicitly say "UNCERTAIN" and explain why.
2. Do NOT invent functions, APIs, syntax, or facts.
3. Only use information you are confident is correct.
4. If assumptions are required, list them clearly before proceeding.
5. Show reasoning step-by-step.
6. After completing the answer, perform a self-review and identify possible errors or weak points.
7. Do not guess syntax. If unsure, say "UNCERTAIN ABOUT SYNTAX".
8. Validate the logic as if you were a compiler or linter.
9. Highlight any part of the code that may fail at runtime.
10. Provide a minimal test case or example input/output.

## What this repo is
Version archive and documentation hub for a Zoho Creator expense reimbursement app. 
No CI/CD — Creator has no structural deployment API. Code is applied manually in Creator UI.

## Tech stack
- **Platform**: Zoho Creator (Free Trial → Standard)
- **Scripting**: Deluge (event-driven, not general-purpose)
- **File convention**: `.dg` = Deluge script files (plain text)

## Key Deluge rules (always follow these)
- `zoho.loginuserrole` does NOT exist — use `thisapp.permissions.isUserInRole("Role Name")`
- `lpad()` does not exist in Deluge
- `hoursBetween` not available on Free Trial daily schedules — use `daysBetween`
- All `insert into approval_history` blocks MUST include `Added_User = zoho.loginuser`
- Threshold fallback value is `999.99` (matches seed data), not `1000`
- GL query always needs null guard: `glRec != null && glRec.count() > 0`
- Strings use double quotes only (never single quotes)
- `ifnull(value, fallback)` for every query result
- `Added_User` in insert tasks ONLY accepts `zoho.loginuser` or `zoho.adminuser` (NOT `zoho.adminuserid`)
- ESG fields (`ESG_Category`, `Estimated_Carbon_KG`) are populated alongside GL code on approval
- `Carbon_Factor` uses `ifnull(glRec.Carbon_Factor, 0)` — never assume GL record has ESG fields
- `Estimated_Carbon_KG = input.amount_zar * carbonFactor` — calculated, not stored on GL account
- `Compliance_Config` queries use `Config_Key == "KEY_NAME" && Active == true` pattern
- Custom API scripts have NO `input.FieldName` — parameters come from the Custom API Builder request definition
- Custom API scripts must return data via response Map, NOT `alert` or form actions
- Custom API Link Name becomes the endpoint URL path segment
- See `docs/zoho-custom-api-builder-research.md` for full Custom API Builder reference

## Tooling workflow
After editing any .dg file:
```
python tools/lint_deluge.py src/deluge/              # lint
python tools/lint_deluge.py --fix src/deluge/        # auto-fix then lint
```
Exit 0 = clean. Exit 1 = warnings. Exit 2 = errors (must fix before proceeding).
If errors found: try `--fix` first, then fix remaining manually and re-run until clean.

Before creating a new .dg file, scaffold it:
```
python tools/scaffold_deluge.py --name SCRIPT_NAME   # from manifest
python tools/scaffold_deluge.py --list                # show all manifest entries
```

After a new .ds export from Creator:
```
python tools/parse_ds_export.py exports/FILE.ds --generate-field-docs docs/build-guide/ --extract-scripts src/deluge/
```

## .ds deployment rules
- Apply ONE type of change at a time (fields, then scripts, then reports — never combined)
- Test each import before adding the next change type
- Always export .ds from Creator after successful import to capture normalised state
- Report removal: ALWAYS use `ds_editor.py remove-reports` (handles 5-point dependency chain)
- Never edit report menu/action blocks manually — use share_settings for permissions
- .ds files MUST be UTF-8 without BOM
- Log every Creator import error in `docs/discovery-log.md` with DL-XXX ID
- Discovery docs use "unresolved" not "impossible" — keep investigation paths open

If the linter DB is missing, rebuild it:
```
python tools/build_deluge_db.py
python tools/build_access_vba_db.py
```

## Access/VBA tooling workflow
After editing any .sql file:
```
python tools/lint_access.py src/access/              # lint all .sql files
python tools/lint_access.py path/to/file.sql         # lint one file
```

Build the Access/VBA language database:
```
python tools/build_access_vba_db.py                  # creates tools/access_vba_lang.db
python tools/build_access_vba_db.py --force           # recreate from scratch
```

Run hybrid linter (cross-environment Access<->Zoho validation):
```
python tools/lint_hybrid.py                           # schema validation only
python tools/lint_hybrid.py --data exports/csv/       # + data validation
python tools/lint_hybrid.py --data exports/csv/ --scripts src/deluge/  # + script cross-ref
```

## Access-to-Zoho import workflow
1. Export Access tables to CSV (Windows only):
```
python tools/export_access_csv.py exports/ERM.accdb --output-dir exports/csv/
```
2. Validate data before upload:
```
python tools/validate_import_data.py exports/csv/ --check-picklists --check-refs
```
3. Upload to Zoho Creator (mock mode by default):
```
python tools/upload_to_creator.py --config config/zoho-api.yaml --csv-dir exports/csv/
python tools/upload_to_creator.py --config config/zoho-api.yaml --csv-dir exports/csv/ --live
```

See `docs/imports/access-to-zoho-import-guide.md` for detailed pathway documentation.

## Key Access/VBA rules (always follow these)
- Access uses `=` for equality (not `==`)
- Access uses `-1`/`0` for Boolean (Zoho uses `true`/`false`)
- Access CURRENCY has exactly 4 decimal places (fixed-point)
- Access has no timezone awareness for DATETIME fields
- Access SQL reserved words must be bracket-escaped: `[Select]`, `[From]`
- Zoho field `action_1` maps to Access `Action_Type` (NOT `action`)
- `config/zoho-api.yaml` must NEVER be committed (contains secrets)

For UI/accessibility changes to .ds files:
```
python tools/ds_editor.py audit exports/FILE.ds                              # check current state
python tools/ds_editor.py add-descriptions exports/FILE.ds                   # from config/field-descriptions.yaml
python tools/ds_editor.py remove-reports exports/FILE.ds --reports name1,name2
python tools/ds_editor.py restrict-menus exports/FILE.ds --reports name1,name2
python tools/ds_editor.py apply-esg exports/FILE.ds                            # deploy ESG + compliance_config schema
python tools/ds_editor.py rebuild-dashboard exports/FILE.ds --page Sustainability_Dashboard
```

## UI standards
- Every user-facing field MUST have help text (see config/field-descriptions.yaml)
- Reference/audit reports: view-only menus (no Edit/Delete/Duplicate)
- Remove Launchpad boilerplate kanbans that duplicate list reports
- Conditional formatting must communicate governance state, not decoration
- See config/ui-standards.md for full guidelines

## Repo structure convention
- `src/deluge/` — scripts organised by Creator UI location (form-workflows, approval-scripts, scheduled)
- `docs/` — architecture, compliance, build-guide, testing
- `docs/imports/` — Access-to-Zoho import guides, type mapping reference, API upload guide
- `config/seed-data/` — JSON source of truth for lookup/config tables
- `config/zoho-api.yaml.template` — template for API credentials (copy to zoho-api.yaml)
- `exports/` — manual .ds snapshots from Creator
- `exports/csv/` — CSV exports from Access for Zoho import (gitignored)
- `tests/` — linter test fixtures (.dg, .sql)

## Governance context
South African compliance: King IV principles, SARS S11(a), segregation of duties.
International alignment: ISSB (IFRS S1/S2), GRI Standards, ISO 26000, ISO 37000, ISSA 5000.
ESG tracking: GL accounts carry ESG_Category and Carbon_Factor; approved claims carry Estimated_Carbon_KG.
Configurable: Compliance_Config table enables org-type-specific controls (PRIVATE, JSE_LISTED, SOE, MULTINATIONAL).
This is not optional flavour — it drives architectural decisions (self-approval prevention, audit trail writes, configurable thresholds).

## Deluge quick-reference

### Data types
- **Text**: double quotes only (`"hello"`, never `'hello'`)
- **Number**: integer (`42`)
- **Decimal**: float (`3.14`)
- **Boolean**: `true` / `false`
- **Date**: single quotes (`'2026-04-06'`) — only dates use single quotes
- **DateTime**: `'2026-04-06 14:30:00'`
- **List**: `{"a", "b", "c"}` or `List()`
- **Map/Key-Value**: `{"key": "value", "key2": "value2"}`
- **Null**: `null` — always guard with `ifnull()`

### Variables
Dynamically typed. Assignment creates the variable:
```
count = 0;
name = "Alice";
```

### Operators
- Arithmetic: `+`, `-`, `*`, `/`
- Comparison: `==`, `!=`, `>`, `<`, `>=`, `<=`
- Logical: `&&`, `||`
- String/collection: `contains`, `in`

### Control flow
```
if (condition)
{
    // ...
}
else if (condition2)
{
    // ...
}
else
{
    // ...
}
```

### Loops
```
for each item in collection
{
    info item;
}
```
Record loop with criteria:
```
for each rec in FormName[field == value]
{
    // ...
}
```

### Built-in tasks (bracket syntax)
```
sendmail
[
    from : zoho.adminuserid
    to : "email@domain.com"
    subject : "Subject"
    message : "Body"
];
```

### Common built-ins
- `zoho.currentdate` — today's date
- `zoho.currenttime` — current datetime
- `zoho.loginuser` — logged-in user name
- `zoho.loginuserid` — logged-in user email
- `zoho.adminuserid` — app admin email
- `thisapp.permissions.isUserInRole("Role")` — role check (NOT `zoho.loginuserrole`)
- `ifnull(value, fallback)` — null coalescing
- `daysBetween(date1, date2)` — days between two dates
- `input.FieldName` — current form field value
- `alert "message"` — show user alert
- `cancel submit` — abort form submission
- `info expression` — debug log

### Collection methods
- `list.add(element)` — append to list
- `list.size()` — list length
- `map.put("key", value)` — add to map
- `map.get("key")` — retrieve from map
- `collection.count()` — record count from query

### Record operations
```
// Insert
row = insert into FormName [field1 = value1  field2 = value2  Added_User = zoho.loginuser];

// Query (returns collection)
recs = FormName[criteria];

// Update (on fetched record)
rec.FieldName = newValue;
```

### Gotchas (project-specific)
See "Key Deluge rules" section above. Additionally:
- No `lpad()`, no `hoursBetween` on Free Trial
- Semicolons optional on most statements but required after task blocks
- `insert into` field assignments use `=` not `:` (unlike sendmail)
- Record queries return collections — always null-guard before accessing fields

## Version convention
v0.0 (Launchpad Generated) → v0.1 (Scaffold Remediation) → v1.0 (Demo Ready)

