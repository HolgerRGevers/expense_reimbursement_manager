# OmegaScript Vision

## Status

Phase 2 (Python linter suite) **complete**. Phase 3 (AST tooling) deferred until multi-app scale.

## What this is

A proposal for integrated Deluge parsing, validation, and editing capabilities within Claude. Originally envisioned as a full parser/interpreter stack, the pragmatic path has been to build increasingly sophisticated Python linters.

## What's implemented

### Phase 1: Prompt Enrichment (Complete)
- CLAUDE.md enriched with Deluge quick-reference (data types, operators, control flow, built-ins, collection methods, record operations)
- Project-specific gotchas documented as "Key Deluge rules"

### Phase 2: Python Linter Suite (Complete)
Three linters covering the full development pipeline:

**`tools/lint_deluge.py`** -- Deluge static analysis
- 41 rules across 4 severity levels (ERROR/WARN/INFO)
- DG001-DG015: syntax validation, banned patterns, governance checks
- Reads from `tools/deluge_lang.db` (SQLite, built by `build_deluge_db.py`)
- `--fix` flag for auto-remediation of common issues
- Exit codes: 0 (clean), 1 (warnings), 2 (errors)

**`tools/lint_access.py`** -- Access SQL static analysis
- AV001-AV008: reserved word escaping, type validation, FK integrity, naming conventions
- Reads from `tools/access_vba_lang.db` (SQLite, built by `build_access_vba_db.py`)
- Validates `.sql` files in `src/access/`

**`tools/lint_hybrid.py`** -- Cross-environment validation
- HY001-HY016: Access-to-Zoho field mapping, type conversion, data validation
- Reads both `deluge_lang.db` and `access_vba_lang.db`
- Three modes: schema-only, +data (CSV), +scripts (Deluge cross-ref)
- Validates that Deluge scripts reference fields that exist in both environments

### Supporting Tools
- `tools/build_deluge_db.py` -- Builds Deluge language database (64 form fields, 12 valid actions, 9 valid statuses, 232 functions)
- `tools/build_access_vba_db.py` -- Builds Access/VBA language database (62 table fields, 14 type mappings, 85 reserved words)
- `tools/scaffold_deluge.py` -- Scaffolds new `.dg` files from manifest
- `tools/ds_editor.py` -- Programmatic `.ds` file modifications (7 subcommands including apply-two-key and apply-esg)
- `tools/generate_mock_data.py` -- Generates 175 synthetic claims with 7 personas for stress testing

## Phase 3: AST Tooling (Deferred)

Full specification for when multiple Creator apps justify the investment:

- **Tree-sitter grammar** for Deluge -- AST-based analysis, not regex
- **Mock interpreter** for semantic validation (variable tracking, type inference)
- **LSP server** for IDE integration (completion, diagnostics, hover docs)
- **Edit-apply workflow** with AST-based patching and sandboxed execution
- **Grammar-based fuzzing** for exhaustive test case generation

### Parser Comparison (from original analysis)

| Parser | Pros | Cons |
|--------|------|------|
| ANTLR | Mature, well-documented, visitor pattern | Java dependency, heavy for this use case |
| Tree-sitter | Incremental parsing, multi-language, Rust core | Grammar authoring learning curve |
| Lark | Pure Python, EBNF grammar, lightweight | No incremental parsing, slower on large files |

**Recommendation**: Tree-sitter for the grammar + AST, with Python bindings. Only justified when managing 3+ Creator apps or when the regex-based linter hits coverage limits.

## Architecture

```
Current (Phase 2):
  .dg files --> lint_deluge.py --> deluge_lang.db --> diagnostics
  .sql files --> lint_access.py --> access_vba_lang.db --> diagnostics
  Both DBs --> lint_hybrid.py --> cross-environment diagnostics

Future (Phase 3):
  .dg files --> tree-sitter parser --> AST --> semantic analysis --> diagnostics
                                        |
                                        +--> mock interpreter --> runtime prediction
                                        |
                                        +--> LSP server --> IDE integration
```

## Key Insight

The Phase 2 Python linters have proven more valuable than originally expected. The regex-based approach catches 95%+ of real errors encountered during development, and the governance-specific rules (DG015 hardcoded emails, DG014 threshold validation) are uniquely useful for this domain. Phase 3 AST tooling would add value for refactoring and code generation, but is not a bottleneck for a single-app project.
