# OmegaScript Vision

## Status
Phase 1 (prompt enrichment) implemented. Full tooling deferred until post-demo / multi-app scale.

## What this is
A proposal for integrated Deluge parsing, validation, and editing capabilities within Claude. The full spec covers a local parser (ANTLR/Tree-sitter), mock interpreter, syntax-rule database, LSP, and edit-apply workflow with sandboxed execution.

## What's implemented now
- CLAUDE.md enriched with Deluge quick-reference (data types, operators, control flow, built-ins, collection methods, record operations)
- Project-specific gotchas documented as "Key Deluge rules"

## Phase roadmap
1. **Now**: Deluge quick-reference in CLAUDE.md (done)
2. **Post-demo**: Python linter for .dg files checking known pitfalls
3. **At scale**: Tree-sitter grammar + AST tooling if multiple Creator apps

## Full specification
See the original OmegaScript vision document for the complete technical design including:
- Deluge grammar analysis and syntax-rule database schema
- Parser comparison (ANTLR vs Tree-sitter vs Lark)
- Edit-apply workflow with AST-based patching
- Mock interpreter design for semantic validation
- Security sandboxing requirements
- Testing strategy with grammar-based fuzzing
- Integration architecture (Mermaid diagrams)
