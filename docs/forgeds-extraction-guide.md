# ForgeDS Extraction Guide

## Purpose

This document maps what moves from `expense_reimbursement_manager/tools/` into the `ForgeDS` pip package, what stays in this repo, and how the two connect via `forgeds.yaml`.

## Architecture

```
ForgeDS (pip package)                    ERM repo (this repo)
========================                 ========================
forgeds/                                 forgeds.yaml          <-- project config
  engines/                               config/
    lint_deluge.py   (engine + lang rules)   deluge-manifest.yaml
    lint_access.py   (engine + rules)        deluge-reference.md
    scaffold.py      (engine + generic tmpl) seed-data/
    ds_parser.py     (full tool)             field-descriptions.yaml
    api_client.py    (full tool)         rules/
    validator.py     (engine)                erm_rules.py      <-- DG004-DG016
  db/                                    templates/
    build_deluge_db.py                       erm_templates.py  <-- audit-trail, etc.
    build_access_vba_db.py               src/deluge/           <-- .dg scripts
  data/                                  docs/
    deluge-builtins.json                 exports/
    access-vba-builtins.json
  config.py          (loads forgeds.yaml)
pyproject.toml
```

## Tool Classification

### A) Move to ForgeDS (6 tools — generic engines)

| Tool | ForgeDS module | Changes needed | Priority |
|------|---------------|----------------|----------|
| `parse_ds_export.py` | `forgeds.engines.ds_parser` | None — zero hardcoding | High |
| `build_deluge_db.py` | `forgeds.db.build_deluge_db` | Parameterize DB output path | High |
| `build_access_vba_db.py` | `forgeds.db.build_access_vba_db` | Parameterize DB output path | High |
| `upload_to_creator.py` | `forgeds.engines.api_client` | Move UPLOAD_ORDER, EXCLUDE_FIELDS to forgeds.yaml config read | High |
| `validate_import_data.py` | `forgeds.engines.validator` | Move TABLE_TO_FORM, FK_RELATIONSHIPS to config read | Medium |
| `lint_access.py` | `forgeds.engines.lint_access` | Parameterize DB path | Medium |

### B) Split: Engine to ForgeDS, Rules/Templates stay in ERM (2 tools)

#### `lint_deluge.py` — Split into engine + rules

**ForgeDS gets** (the engine):
- `Severity`, `FileType`, `Diagnostic`, `Block` classes
- `strip_comments()`, `is_comment_line()`, `extract_blocks()`
- `detect_file_type()` (with all context detection including `custom-api`)
- `DelugeDB` class (SQLite cache loader)
- Language-level rules: DG001, DG002, DG003, DG008, DG013, DG017, DG018, DG019, DG020, DG021
- `run_line_rules()`, `run_block_rules()` with plugin hook for app rules
- Auto-fix engine (`fix_file`, `_fix_single_quotes`)
- CLI entry point (`main()`)

**ERM keeps** (app rules, loaded as plugins):
- DG004 (`check_dg004`) — ERM field names from DB
- DG005 (`check_dg005`) — null guard (generic pattern but uses ERM form names)
- DG006/DG007 (`check_dg006`, `check_dg007`) — approval_history Added_User
- DG009 (`check_dg009`) — insert block separator
- DG010 (`check_dg010`) — sendmail/invokeUrl required params
- DG011 (`check_dg011`) — ERM status values from DB
- DG012 (`check_dg012`) — ERM action values from DB
- DG014 (`check_dg014`) — ERM threshold fallback values
- DG015/DG016 (`check_dg015_016`) — ERM email domain list

**Plugin mechanism**: ForgeDS engine discovers app rules via entry points or a `rules/` directory referenced in `forgeds.yaml`.

#### `scaffold_deluge.py` — Split into engine + templates

**ForgeDS gets** (the engine):
- `_parse_simple_yaml()` — YAML parser
- `load_yaml()` — file loader
- `generate_header()` — universal .dg header
- `generate_custom_api_boilerplate()` — Custom API template
- `scaffold_script()` — assembly function with plugin hook for app templates
- CLI entry point with `--context` choices loaded from `forgeds.yaml` `script_contexts`

**ERM keeps** (app templates):
- `generate_audit_trail()` — ERM approval_history insert pattern
- `generate_sendmail()` — ERM notification pattern
- `generate_self_approval_check()` — King IV self-approval pattern
- `generate_gl_lookup()` — ERM GL code population
- `generate_threshold_check()` — ERM threshold lookup with fallback

### C) Stay in ERM (5 tools — fully app-specific)

| Tool | Reason |
|------|--------|
| `lint_hybrid.py` | ERM-specific cross-environment validation |
| `ds_editor.py` | ERM schema modifications (two-key, ESG, reports) |
| `generate_mock_data.py` | 7 ERM personas, SA-specific test scenarios |
| `build_access_db.py` | ERM table structure (pyodbc, Windows) |
| `export_access_csv.py` | ERM export order (pyodbc, Windows) |

Note: `lint_hybrid.py` and `ds_editor.py` could partially extract later, but they're deeply tied to ERM schema. Low priority.

## forgeds.yaml — Config Bridge

`forgeds.yaml` is the contract between ForgeDS and the app repo. ForgeDS reads it at runtime to:

1. **Configure the linter**: Thresholds, email domains, rule enable/disable
2. **Configure the scaffold**: Available contexts, template paths
3. **Configure the API client**: Upload order, exclude fields, form mappings
4. **Configure the validator**: FK relationships, mandatory fields
5. **Define Custom APIs**: Link names, parameters, response schemas

Already defined in `forgeds.yaml`:
- `lint.*` — thresholds, email domains
- `schema.*` — table mappings, FK relationships, upload order
- `custom_apis.*` — Custom API definitions (added this session)
- `lint_rules.*` — engine vs app rule classification (added this session)
- `script_contexts` — supported Deluge contexts (added this session)
- `scaffold.*` — engine vs app template classification (added this session)

## ForgeDS Package Structure (Proposed)

```
ForgeDS/
  pyproject.toml              # pip package config
  src/
    forgeds/
      __init__.py
      config.py               # Loads and validates forgeds.yaml
      engines/
        __init__.py
        lint_deluge.py         # Deluge linter engine + language rules
        lint_access.py         # Access SQL linter
        scaffold.py            # Scaffold engine + generic templates
        ds_parser.py           # .ds export parser
        api_client.py          # Zoho Creator REST API client
        validator.py           # Import data validator
      db/
        __init__.py
        build_deluge_db.py     # Deluge language DB builder
        build_access_vba_db.py # Access/VBA language DB builder
      data/
        deluge-builtins.json   # Deluge stdlib reference data
        access-vba-builtins.json
      cli.py                   # CLI entry points (forgeds lint, forgeds scaffold, etc.)
  tests/
```

## ERM Repo After Extraction

```
expense_reimbursement_manager/
  forgeds.yaml                 # Project config (consumed by ForgeDS)
  requirements.txt             # forgeds>=0.1.0
  config/
    deluge-manifest.yaml       # Script metadata (consumed by forgeds scaffold)
    seed-data/                 # Lookup table data
    field-descriptions.yaml
    deluge-reference.md
  rules/
    erm_lint_rules.py          # App-specific linter rules (DG004-DG016)
  templates/
    erm_scaffold_templates.py  # App-specific scaffold templates
  src/deluge/                  # .dg script files (unchanged)
  docs/                        # Documentation (unchanged)
  exports/                     # .ds snapshots (unchanged)
  enhancements/                # Roadmap docs (unchanged)
```

The `tools/` directory would be replaced by ForgeDS CLI commands:
```bash
forgeds lint src/deluge/                    # was: python tools/lint_deluge.py
forgeds lint --fix src/deluge/              # was: python tools/lint_deluge.py --fix
forgeds scaffold --name get_dashboard_summary  # was: python tools/scaffold_deluge.py --name
forgeds scaffold --list                     # was: python tools/scaffold_deluge.py --list
forgeds upload --config config/zoho-api.yaml --csv-dir exports/csv/  # was: python tools/upload_to_creator.py
forgeds validate exports/csv/              # was: python tools/validate_import_data.py
forgeds parse exports/FILE.ds              # was: python tools/parse_ds_export.py
forgeds build-db deluge                    # was: python tools/build_deluge_db.py
forgeds build-db access-vba               # was: python tools/build_access_vba_db.py
```

## Extraction Sequence

1. **Create ForgeDS package skeleton** — `pyproject.toml`, `src/forgeds/`, entry points
2. **Extract zero-change tools first** — `parse_ds_export.py`, `build_*_db.py` (High priority, minimal risk)
3. **Extract config-parameterized tools** — `upload_to_creator.py`, `validate_import_data.py`, `lint_access.py` (read UPLOAD_ORDER etc. from forgeds.yaml)
4. **Split linter** — Extract engine + language rules; create plugin hook; move app rules to `rules/erm_lint_rules.py`
5. **Split scaffold** — Extract engine + generic templates; create plugin hook; move app templates to `templates/erm_scaffold_templates.py`
6. **Add `requirements.txt`** to ERM — `forgeds>=0.1.0`
7. **Update CLAUDE.md** — Change tooling workflow to use `forgeds` CLI commands
8. **Remove `tools/`** — Once ForgeDS is verified working via pip

## Custom API Builder — ForgeDS vs ERM Split

From the Custom API Builder work done this session:

| Item | Goes to |
|------|---------|
| `docs/zoho-custom-api-builder-research.md` | **ERM** — app-specific research |
| `docs/discovery-log.md` DL-007 | **ERM** — app-specific discovery |
| `config/deluge-manifest.yaml` custom-api entries | **ERM** — app-specific manifest |
| `forgeds.yaml` custom_apis section | **ERM** — app config for ForgeDS |
| `FileType.CUSTOM_API` enum + detection | **ForgeDS** — engine knows about all contexts |
| DG020 (response Map required) | **ForgeDS** — language-level rule |
| DG021 (no form tasks in API context) | **ForgeDS** — language-level rule |
| DG004 skip for custom-api context | **ForgeDS** — engine behavior |
| `generate_custom_api_boilerplate()` | **ForgeDS** — generic template |
| Custom API entries in scaffold `--context` | **ForgeDS** — engine supports all contexts |
