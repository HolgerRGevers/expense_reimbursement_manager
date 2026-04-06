#!/usr/bin/env python3
"""
Deluge Script Linter for Zoho Creator .dg files.

Static analysis tool that catches common Deluge scripting errors,
enforces project conventions, and validates field references.
Backed by a SQLite database of Deluge language data.

Usage:
    python tools/lint_deluge.py src/deluge/           # lint all .dg files
    python tools/lint_deluge.py path/to/file.dg       # lint one file

Exit codes:
    0 = clean (no issues)
    1 = warnings only
    2 = errors found
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


# ============================================================
# Constants
# ============================================================

DB_PATH = Path(__file__).parent / "deluge_lang.db"

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}(:\d{2})?)?$")
TIME_PATTERN = re.compile(r"^\d{2}:\d{2}(:\d{2})?$")
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

DEMO_EMAIL_DOMAINS = {"yourdomain.com", "example.com", "placeholder.com"}
THRESHOLD_FALLBACK = "999.99"


# ============================================================
# Enums
# ============================================================

class Severity(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"


class FileType(str, Enum):
    FORM_WORKFLOW = "form-workflow"
    APPROVAL_SCRIPT = "approval-script"
    SCHEDULED = "scheduled"


# ============================================================
# Data classes
# ============================================================

@dataclass(frozen=True)
class Diagnostic:
    filename: str
    line: int
    severity: Severity
    code: str
    message: str

    def __str__(self) -> str:
        return (
            f"{self.filename}:{self.line}: "
            f"[{self.severity.value}] {self.code}: {self.message}"
        )


@dataclass
class FieldAssignment:
    name: str
    value: str
    line: int
    separator: str  # "=" or ":"


@dataclass
class Block:
    block_type: str             # "insert" | "sendmail" | "invokeUrl"
    target_table: str | None
    start_line: int
    end_line: int
    fields: dict[str, FieldAssignment] = field(default_factory=dict)
    raw_lines: list[str] = field(default_factory=list)


# ============================================================
# Database-backed lookup cache
# ============================================================

class DelugeDB:
    """Read-only cache of Deluge language data from SQLite."""

    def __init__(self, db_path: Path) -> None:
        if not db_path.exists():
            raise FileNotFoundError(
                f"Deluge language DB not found at {db_path}. "
                "Run: python tools/build_deluge_db.py"
            )
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._load_caches()

    def _query_set(self, sql: str) -> set[str]:
        return {row[0] for row in self._conn.execute(sql).fetchall()}

    def _load_caches(self) -> None:
        self.valid_statuses: set[str] = self._query_set(
            "SELECT value FROM valid_statuses"
        )
        self.valid_actions: set[str] = self._query_set(
            "SELECT value FROM valid_actions"
        )
        self.reserved_words: set[str] = self._query_set(
            "SELECT word FROM reserved_words"
        )
        self.zoho_variable_names: set[str] = self._query_set(
            "SELECT name FROM zoho_variables"
        )
        self.function_names: set[str] = self._query_set(
            "SELECT DISTINCT name FROM functions"
        )
        self.banned_functions: dict[str, str] = {
            row["pattern"]: row["message"]
            for row in self._conn.execute(
                "SELECT pattern, message FROM banned_patterns WHERE pattern_type = 'function'"
            ).fetchall()
        }
        self.banned_variables: dict[str, str] = {
            row["pattern"]: row["message"]
            for row in self._conn.execute(
                "SELECT pattern, message FROM banned_patterns WHERE pattern_type = 'variable'"
            ).fetchall()
        }

        # Form fields: { form_name: { field_link_name, ... } }
        self.form_fields: dict[str, set[str]] = {}
        for row in self._conn.execute("SELECT form_name, field_link FROM form_fields"):
            form = row["form_name"]
            if form not in self.form_fields:
                self.form_fields[form] = set()
            self.form_fields[form].add(row["field_link"])

        # Expense_claims fields (used for input.X validation)
        self.expense_fields: set[str] = self.form_fields.get("expense_claims", set())

        # Approval_history fields (used for insert validation)
        self.approval_history_fields: set[str] = self.form_fields.get(
            "approval_history", set()
        )

        # Sendmail required params
        row = self._conn.execute(
            "SELECT required_params FROM builtin_tasks WHERE name = 'sendmail'"
        ).fetchone()
        self.sendmail_required: set[str] = (
            set(row["required_params"].split(",")) if row and row["required_params"] else set()
        )

        # InvokeUrl required params
        row = self._conn.execute(
            "SELECT required_params FROM builtin_tasks WHERE name = 'invokeUrl'"
        ).fetchone()
        self.invoke_url_required: set[str] = (
            set(row["required_params"].split(",")) if row and row["required_params"] else set()
        )

    def close(self) -> None:
        self._conn.close()


# ============================================================
# File type detection
# ============================================================

def detect_file_type(filepath: str) -> FileType:
    """Determine script context from file path."""
    normalized = filepath.replace("\\", "/")
    if "/scheduled/" in normalized:
        return FileType.SCHEDULED
    if "/approval-scripts/" in normalized:
        return FileType.APPROVAL_SCRIPT
    return FileType.FORM_WORKFLOW


# ============================================================
# Comment handling
# ============================================================

def strip_comments(line: str) -> str:
    """Remove trailing // comments, respecting double-quoted strings."""
    in_string = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"' and (i == 0 or line[i - 1] != '\\'):
            in_string = not in_string
        elif not in_string and line[i:i + 2] == '//':
            return line[:i]
        i += 1
    return line


def is_comment_line(line: str) -> bool:
    """Check if line is a full-line comment."""
    stripped = line.strip()
    return stripped.startswith("//") or stripped.startswith("/*")


# ============================================================
# Block extractor (Pass 1)
# ============================================================

def extract_blocks(lines: list[str]) -> list[Block]:
    """Extract multi-line insert into/sendmail/invokeUrl blocks."""
    blocks: list[Block] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if is_comment_line(stripped):
            i += 1
            continue

        # Detect insert into
        insert_match = re.search(r"\binsert\s+into\s+(\w+)", stripped, re.IGNORECASE)
        if insert_match:
            block = _extract_bracket_block(
                lines, i, "insert", insert_match.group(1)
            )
            if block:
                blocks.append(block)
                i = block.end_line
                continue

        # Detect sendmail
        if re.search(r"\bsendmail\b", stripped, re.IGNORECASE):
            block = _extract_bracket_block(lines, i, "sendmail", None)
            if block:
                blocks.append(block)
                i = block.end_line
                continue

        # Detect invokeUrl
        if re.search(r"\binvokeUrl\b", stripped, re.IGNORECASE):
            block = _extract_bracket_block(lines, i, "invokeUrl", None)
            if block:
                blocks.append(block)
                i = block.end_line
                continue

        i += 1
    return blocks


def _extract_bracket_block(
    lines: list[str],
    start_idx: int,
    block_type: str,
    target_table: str | None,
) -> Block | None:
    """Extract a [...] delimited block starting near start_idx."""
    # Find opening [
    bracket_line: int | None = None
    for j in range(start_idx, min(start_idx + 3, len(lines))):
        if "[" in lines[j]:
            bracket_line = j
            break
    if bracket_line is None:
        return None

    # Collect until closing ]
    raw_lines: list[str] = []
    end_idx = bracket_line
    for j in range(bracket_line, len(lines)):
        raw_lines.append(lines[j])
        if "]" in lines[j] and j > bracket_line:
            end_idx = j
            break
        elif j == bracket_line and "]" in lines[j].split("[", 1)[-1]:
            end_idx = j
            break
        end_idx = j

    # Parse field assignments inside the block
    fields: dict[str, FieldAssignment] = {}
    for j in range(bracket_line + 1, end_idx + 1):
        line = lines[j].strip()
        if line.startswith(("]", "[")):
            continue
        if is_comment_line(line):
            continue

        eq_match = re.match(r"(\w+)\s*=\s*(.+?)(?:\s*$)", line)
        colon_match = re.match(r"(\w+)\s*:\s*(.+?)(?:\s*$)", line)

        if block_type == "insert":
            if eq_match:
                fname = eq_match.group(1)
                fields[fname] = FieldAssignment(
                    fname, eq_match.group(2).strip(), j + 1, "="
                )
            elif colon_match:
                fname = colon_match.group(1)
                fields[fname] = FieldAssignment(
                    fname, colon_match.group(2).strip(), j + 1, ":"
                )
        else:  # sendmail, invokeUrl
            if colon_match:
                fname = colon_match.group(1)
                fields[fname] = FieldAssignment(
                    fname, colon_match.group(2).strip(), j + 1, ":"
                )
            elif eq_match:
                fname = eq_match.group(1)
                fields[fname] = FieldAssignment(
                    fname, eq_match.group(2).strip(), j + 1, "="
                )

    return Block(
        block_type=block_type,
        target_table=target_table,
        start_line=start_idx + 1,
        end_line=end_idx + 1,
        fields=fields,
        raw_lines=raw_lines,
    )


# ============================================================
# Line-scoped rules (Pass 2)
# ============================================================

def check_dg001(db: DelugeDB, filename: str, line: str, lineno: int) -> list[Diagnostic]:
    """DG001: Banned function call."""
    diags: list[Diagnostic] = []
    for func, msg in db.banned_functions.items():
        if re.search(rf"\b{re.escape(func)}\s*\(", line):
            diags.append(Diagnostic(filename, lineno, Severity.ERROR, "DG001", msg))
    return diags


def check_dg002(db: DelugeDB, filename: str, line: str, lineno: int) -> list[Diagnostic]:
    """DG002: Banned variable reference."""
    diags: list[Diagnostic] = []
    for var, msg in db.banned_variables.items():
        if re.search(rf"\b{re.escape(var)}\b", line):
            diags.append(Diagnostic(filename, lineno, Severity.ERROR, "DG002", msg))
    return diags


def check_dg003(
    filename: str, line: str, lineno: int, file_type: FileType,
) -> list[Diagnostic]:
    """DG003: hoursBetween in scheduled scripts (Free Trial limitation)."""
    if file_type == FileType.SCHEDULED and re.search(r"\bhoursBetween\b", line):
        return [Diagnostic(
            filename, lineno, Severity.ERROR, "DG003",
            "hoursBetween not available on Free Trial daily schedules. Use daysBetween.",
        )]
    return []


def check_dg004(
    db: DelugeDB, filename: str, line: str, lineno: int,
) -> list[Diagnostic]:
    """DG004: Unknown input.FieldName reference."""
    diags: list[Diagnostic] = []
    for match in re.finditer(r"\binput\.(\w+)", line):
        field_name = match.group(1)
        if field_name not in db.expense_fields:
            diags.append(Diagnostic(
                filename, lineno, Severity.ERROR, "DG004",
                f"Unknown field 'input.{field_name}'. "
                "Valid fields: check docs/build-guide/field-link-names.md",
            ))
    return diags


def check_dg008(filename: str, line: str, lineno: int) -> list[Diagnostic]:
    """DG008: Single quotes used for text (not date/time)."""
    diags: list[Diagnostic] = []
    for match in re.finditer(r"'([^']*)'", line):
        content = match.group(1)
        if not content:
            continue
        if DATE_PATTERN.match(content) or TIME_PATTERN.match(content):
            continue
        diags.append(Diagnostic(
            filename, lineno, Severity.ERROR, "DG008",
            f"Single quotes used for text '{content}'. "
            "Use double quotes for strings; single quotes are for dates/times only.",
        ))
    return diags


def check_dg011(
    db: DelugeDB, filename: str, line: str, lineno: int,
) -> list[Diagnostic]:
    """DG011: Unknown status value."""
    match = re.search(r'\.status\s*=\s*"([^"]*)"', line)
    if match:
        status = match.group(1)
        if status not in db.valid_statuses:
            return [Diagnostic(
                filename, lineno, Severity.WARN, "DG011",
                f'Unknown status value "{status}". '
                f"Valid: {', '.join(sorted(db.valid_statuses))}",
            )]
    return []


def check_dg013(filename: str, line: str, lineno: int) -> list[Diagnostic]:
    """DG013: Mixed && and || without parentheses."""
    if "&&" in line and "||" in line:
        return [Diagnostic(
            filename, lineno, Severity.WARN, "DG013",
            "Mixed && and || on same line. Creator evaluates OR before AND "
            "(opposite of most languages). Use explicit parentheses.",
        )]
    return []


def check_dg015_016(filename: str, line: str, lineno: int) -> list[Diagnostic]:
    """DG015/DG016: Hardcoded email addresses."""
    if "zoho.adminuserid" in line or "zoho.loginuserid" in line:
        return []
    diags: list[Diagnostic] = []
    for match in EMAIL_PATTERN.finditer(line):
        email = match.group(0)
        domain = email.split("@")[1].lower() if "@" in email else ""
        if any(d in domain for d in DEMO_EMAIL_DOMAINS) or "demo" in email.lower():
            diags.append(Diagnostic(
                filename, lineno, Severity.WARN, "DG015",
                f"Hardcoded demo/placeholder email '{email}'. "
                "Replace with role-based lookup for production.",
            ))
        else:
            diags.append(Diagnostic(
                filename, lineno, Severity.INFO, "DG016",
                f"Hardcoded email '{email}'. Consider using role-based lookup.",
            ))
    return diags


def check_dg017(
    db: DelugeDB, filename: str, line: str, lineno: int,
) -> list[Diagnostic]:
    """DG017: Reserved word used as variable name."""
    # Match assignment patterns: word = value (but not == comparison)
    match = re.match(r"\s*(\w+)\s*=[^=]", line)
    if match:
        var_name = match.group(1)
        if var_name in db.reserved_words:
            return [Diagnostic(
                filename, lineno, Severity.ERROR, "DG017",
                f"Reserved word '{var_name}' cannot be used as a variable name. "
                f"Reserved: {', '.join(sorted(db.reserved_words))}",
            )]
    return []


def check_dg018(
    db: DelugeDB, filename: str, line: str, lineno: int,
) -> list[Diagnostic]:
    """DG018: Unknown zoho system variable."""
    diags: list[Diagnostic] = []
    for match in re.finditer(r"\bzoho\.(\w+(?:\.\w+)*)", line):
        full_var = f"zoho.{match.group(1)}"
        if full_var not in db.zoho_variable_names:
            # Check if it's a banned variable (handled by DG002)
            if full_var in db.banned_variables:
                continue
            diags.append(Diagnostic(
                filename, lineno, Severity.WARN, "DG018",
                f"Unknown Zoho variable '{full_var}'. "
                f"Known: {', '.join(sorted(db.zoho_variable_names))}",
            ))
    return diags


def run_line_rules(
    db: DelugeDB, filename: str, lines: list[str], file_type: FileType,
) -> list[Diagnostic]:
    """Run all line-scoped rules."""
    diags: list[Diagnostic] = []
    for i, raw_line in enumerate(lines):
        lineno = i + 1
        if is_comment_line(raw_line):
            continue
        line = strip_comments(raw_line)

        diags.extend(check_dg001(db, filename, line, lineno))
        diags.extend(check_dg002(db, filename, line, lineno))
        diags.extend(check_dg003(filename, line, lineno, file_type))
        diags.extend(check_dg004(db, filename, line, lineno))
        diags.extend(check_dg008(filename, line, lineno))
        diags.extend(check_dg011(db, filename, line, lineno))
        diags.extend(check_dg013(filename, line, lineno))
        diags.extend(check_dg015_016(filename, line, lineno))
        diags.extend(check_dg017(db, filename, line, lineno))
        diags.extend(check_dg018(db, filename, line, lineno))

    return diags


# ============================================================
# Block-scoped rules (Pass 3)
# ============================================================

def check_dg006(filename: str, block: Block) -> list[Diagnostic]:
    """DG006: Missing Added_User in insert into approval_history."""
    if block.block_type != "insert" or block.target_table != "approval_history":
        return []
    if "Added_User" not in block.fields:
        return [Diagnostic(
            filename, block.start_line, Severity.ERROR, "DG006",
            "Missing 'Added_User = zoho.loginuser' in insert into approval_history block.",
        )]
    return []


def check_dg007(filename: str, block: Block) -> list[Diagnostic]:
    """DG007: Wrong Added_User value (must be zoho.loginuser)."""
    if block.block_type != "insert" or block.target_table != "approval_history":
        return []
    if "Added_User" in block.fields:
        val = block.fields["Added_User"].value.strip()
        if val != "zoho.loginuser":
            return [Diagnostic(
                filename, block.fields["Added_User"].line, Severity.ERROR, "DG007",
                f"Added_User must be 'zoho.loginuser', got '{val}'.",
            )]
    return []


def check_dg009(filename: str, block: Block) -> list[Diagnostic]:
    """DG009: Colon instead of = in insert into blocks."""
    if block.block_type != "insert":
        return []
    diags: list[Diagnostic] = []
    for fa in block.fields.values():
        if fa.separator == ":":
            diags.append(Diagnostic(
                filename, fa.line, Severity.ERROR, "DG009",
                f"Field '{fa.name}' uses ':' separator in insert block. "
                "Use '=' (colons are for sendmail).",
            ))
    return diags


def check_dg010(db: DelugeDB, filename: str, block: Block) -> list[Diagnostic]:
    """DG010: Missing required sendmail/invokeUrl params."""
    if block.block_type == "sendmail":
        required = db.sendmail_required
    elif block.block_type == "invokeUrl":
        required = db.invoke_url_required
    else:
        return []

    diags: list[Diagnostic] = []
    param_names = {k.lower().strip() for k in block.fields}
    for req in required:
        if req not in param_names:
            diags.append(Diagnostic(
                filename, block.start_line, Severity.ERROR, "DG010",
                f"Missing required {block.block_type} parameter '{req}'.",
            ))
    return diags


def check_dg012(db: DelugeDB, filename: str, block: Block) -> list[Diagnostic]:
    """DG012: Unknown action_1 value in audit trail."""
    if block.block_type != "insert" or block.target_table != "approval_history":
        return []
    if "action_1" in block.fields:
        val = block.fields["action_1"].value.strip().strip('"')
        if val not in db.valid_actions:
            return [Diagnostic(
                filename, block.fields["action_1"].line, Severity.WARN, "DG012",
                f'Unknown action_1 value "{val}". '
                f"Valid: {', '.join(sorted(db.valid_actions))}",
            )]
    return []


def check_dg014(filename: str, lines: list[str]) -> list[Diagnostic]:
    """DG014: Threshold fallback not 999.99."""
    diags: list[Diagnostic] = []
    for i, raw_line in enumerate(lines):
        lineno = i + 1
        if is_comment_line(raw_line):
            continue
        line = strip_comments(raw_line)

        # Direct threshold assignment
        match = re.search(
            r"\bthreshold\w*\s*=\s*(\d+\.?\d*)", line, re.IGNORECASE,
        )
        if match:
            val = match.group(1)
            try:
                if float(val) != float(THRESHOLD_FALLBACK):
                    diags.append(Diagnostic(
                        filename, lineno, Severity.WARN, "DG014",
                        f"Threshold fallback value is {val}, "
                        f"expected {THRESHOLD_FALLBACK} (matching seed data).",
                    ))
            except ValueError:
                pass

        # ifnull with threshold context
        if "ifnull" in line and "threshold" in line.lower():
            ifnull_match = re.search(
                r"ifnull\s*\([^,]+,\s*(\d+\.?\d*)\s*\)", line,
            )
            if ifnull_match:
                val = ifnull_match.group(1)
                try:
                    if float(val) != float(THRESHOLD_FALLBACK):
                        diags.append(Diagnostic(
                            filename, lineno, Severity.WARN, "DG014",
                            f"Threshold ifnull fallback is {val}, "
                            f"expected {THRESHOLD_FALLBACK} (matching seed data).",
                        ))
                except ValueError:
                    pass

    return diags


def run_block_rules(
    db: DelugeDB, filename: str, blocks: list[Block], lines: list[str],
) -> list[Diagnostic]:
    """Run all block-scoped rules."""
    diags: list[Diagnostic] = []
    for block in blocks:
        diags.extend(check_dg006(filename, block))
        diags.extend(check_dg007(filename, block))
        diags.extend(check_dg009(filename, block))
        diags.extend(check_dg010(db, filename, block))
        diags.extend(check_dg012(db, filename, block))
    diags.extend(check_dg014(filename, lines))
    return diags


# ============================================================
# File-scoped rules (Pass 4)
# ============================================================

def check_dg005(filename: str, lines: list[str]) -> list[Diagnostic]:
    """DG005: Query result used without null guard."""
    diags: list[Diagnostic] = []
    query_vars: dict[str, int] = {}
    guarded_vars: set[str] = set()
    guard_scopes: list[tuple[str, int]] = []
    brace_depth = 0

    for i, raw_line in enumerate(lines):
        lineno = i + 1
        if is_comment_line(raw_line):
            continue
        line = strip_comments(raw_line)

        brace_depth += line.count("{") - line.count("}")

        # Pop guard scopes when braces close
        while guard_scopes and brace_depth < guard_scopes[-1][1]:
            var = guard_scopes.pop()[0]
            guarded_vars.discard(var)

        # Detect query: var = TableName[criteria]
        q_match = re.match(r"\s*(\w+)\s*=\s*(\w+)\s*\[", line)
        if q_match:
            var_name = q_match.group(1)
            table_name = q_match.group(2)
            if table_name not in ("insert", "into", "if", "for", "while"):
                query_vars[var_name] = lineno

        # Detect null guard: if (var != null
        guard_match = re.search(r"if\s*\(\s*(\w+)\s*!=\s*null", line)
        if guard_match:
            var_name = guard_match.group(1)
            if var_name in query_vars:
                guarded_vars.add(var_name)
                guard_scopes.append((var_name, brace_depth))

        # Detect unguarded access: var.field
        for var_name, assign_line in query_vars.items():
            if var_name in guarded_vars or lineno == assign_line:
                continue
            if re.search(rf"\b{re.escape(var_name)}\.(\w+)", line):
                if guard_match and guard_match.group(1) == var_name:
                    continue
                diags.append(Diagnostic(
                    filename, lineno, Severity.ERROR, "DG005",
                    f"Query result '{var_name}' accessed without null guard. "
                    f"Add: if ({var_name} != null && {var_name}.count() > 0)",
                ))
                guarded_vars.add(var_name)

    return diags


# ============================================================
# Main pipeline
# ============================================================

def lint_file(db: DelugeDB, filepath: str) -> list[Diagnostic]:
    """Run all lint passes on a single .dg file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            raw_lines = f.readlines()
    except (OSError, UnicodeDecodeError) as e:
        return [Diagnostic(filepath, 0, Severity.ERROR, "DG000", f"Cannot read file: {e}")]

    lines = [line.rstrip("\n\r") for line in raw_lines]
    file_type = detect_file_type(filepath)

    blocks = extract_blocks(lines)
    diags = run_line_rules(db, filepath, lines, file_type)
    diags.extend(run_block_rules(db, filepath, blocks, lines))
    diags.extend(check_dg005(filepath, lines))

    return diags


def resolve_files(paths: list[str]) -> list[str]:
    """Expand directories to .dg files, pass through individual files."""
    files: list[str] = []
    for path in paths:
        if os.path.isdir(path):
            for root, _dirs, filenames in os.walk(path):
                for fn in sorted(filenames):
                    if fn.endswith(".dg"):
                        files.append(os.path.join(root, fn))
        elif os.path.isfile(path) and path.endswith(".dg"):
            files.append(path)
        else:
            print(
                f"Warning: skipping '{path}' (not a .dg file or directory)",
                file=sys.stderr,
            )
    return files


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Deluge script linter for .dg files",
        epilog="Exit codes: 0=clean, 1=warnings, 2=errors",
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to lint")
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Only show errors and warnings, suppress info",
    )
    parser.add_argument(
        "--errors-only", action="store_true",
        help="Only show ERROR severity",
    )
    args = parser.parse_args()

    files = resolve_files(args.paths)
    if not files:
        print("No .dg files found.", file=sys.stderr)
        sys.exit(0)

    db = DelugeDB(DB_PATH)
    all_diags: list[Diagnostic] = []
    try:
        for filepath in files:
            all_diags.extend(lint_file(db, filepath))
    finally:
        db.close()

    # Filter by severity
    if args.errors_only:
        all_diags = [d for d in all_diags if d.severity == Severity.ERROR]
    elif args.quiet:
        all_diags = [d for d in all_diags if d.severity != Severity.INFO]

    # Sort and output
    severity_order = {Severity.ERROR: 0, Severity.WARN: 1, Severity.INFO: 2}
    all_diags.sort(key=lambda d: (d.filename, d.line, severity_order[d.severity]))
    for diag in all_diags:
        print(diag)

    # Summary
    errors = sum(1 for d in all_diags if d.severity == Severity.ERROR)
    warnings = sum(1 for d in all_diags if d.severity == Severity.WARN)
    infos = sum(1 for d in all_diags if d.severity == Severity.INFO)

    print(
        f"\n--- Linted {len(files)} file(s): "
        f"{errors} error(s), {warnings} warning(s), {infos} info(s) ---"
    )

    sys.exit(2 if errors > 0 else 1 if warnings > 0 else 0)


if __name__ == "__main__":
    main()
