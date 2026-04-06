#!/usr/bin/env python3
"""
Deluge Script Linter for Zoho Creator .dg files.

Static analysis tool that catches common Deluge scripting errors,
enforces project conventions, and validates field references.

Usage:
    python tools/lint_deluge.py src/deluge/           # lint all .dg files
    python tools/lint_deluge.py path/to/file.dg       # lint one file

Exit codes:
    0 = clean (no issues)
    1 = warnings only
    2 = errors found
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# ============================================================
# Constants
# ============================================================

VALID_STATUSES = {
    "Draft",
    "Submitted",
    "Pending LM Approval",
    "Pending HoD Approval",
    "Approved",
    "Rejected",
    "Resubmitted",
}

VALID_ACTIONS = {
    "Submitted",
    "Submitted (Self-approval bypass)",
    "Approved (LM)",
    "Approved (HoD)",
    "Rejected",
    "Escalated (SLA Breach)",
    "Resubmitted",
    "Warning",
}

VALID_EXPENSE_FIELDS = {
    "Employee_Name1", "Email", "Submission_Date", "claim_id",
    "department", "Claim_Reference", "client", "Expense_Date",
    "Department_Shadow", "category", "Client_Shadow", "amount_zar",
    "Supporting_Documents", "description", "status", "Rejection_Reason",
    "Version", "Parent_Claim_ID", "gl_code", "ID",
}

VALID_APPROVAL_HISTORY_FIELDS = {
    "claim", "action_1", "actor", "timestamp", "comments", "Added_User",
}

BANNED_FUNCTIONS = {"lpad", "rpad"}

REQUIRED_SENDMAIL_PARAMS = {"from", "to", "subject", "message"}

THRESHOLD_FALLBACK = "999.99"

DEMO_EMAIL_DOMAINS = {"yourdomain.com", "example.com", "placeholder.com"}

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}(:\d{2})?)?$")
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


# ============================================================
# Data classes
# ============================================================

@dataclass
class Diagnostic:
    filename: str
    line: int
    severity: str  # "ERROR", "WARN", "INFO"
    code: str      # "DG001"
    message: str

    def __str__(self):
        return f"{self.filename}:{self.line}: [{self.severity}] {self.code}: {self.message}"


@dataclass
class FieldAssignment:
    name: str
    value: str
    line: int
    separator: str  # "=" or ":"


@dataclass
class Block:
    block_type: str             # "insert" or "sendmail"
    target_table: Optional[str] # e.g., "approval_history" for insert blocks
    start_line: int             # 1-based
    end_line: int               # 1-based
    fields: Dict[str, FieldAssignment] = field(default_factory=dict)
    raw_lines: List[str] = field(default_factory=list)


# ============================================================
# File type detection
# ============================================================

def detect_file_type(filepath: str) -> str:
    normalized = filepath.replace("\\", "/")
    if "/scheduled/" in normalized:
        return "scheduled"
    elif "/approval-scripts/" in normalized:
        return "approval-script"
    return "form-workflow"


# ============================================================
# Comment stripping
# ============================================================

def strip_comments(line: str) -> str:
    """Remove trailing // comments, respecting strings."""
    in_string = False
    for i, ch in enumerate(line):
        if ch == '"' and (i == 0 or line[i - 1] != '\\'):
            in_string = not in_string
        elif not in_string and i + 1 < len(line) and line[i:i+2] == '//':
            return line[:i]
    return line


def is_comment_line(line: str) -> bool:
    return line.strip().startswith("//") or line.strip().startswith("/*")


# ============================================================
# Block extractor (Pass 1)
# ============================================================

def extract_blocks(lines: List[str]) -> List[Block]:
    """Extract multi-line insert into [...] and sendmail [...] blocks."""
    blocks = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        if is_comment_line(stripped):
            i += 1
            continue

        # Detect insert into
        insert_match = re.search(r"\binsert\s+into\s+(\w+)", stripped, re.IGNORECASE)
        if insert_match:
            table_name = insert_match.group(1)
            block = _extract_bracket_block(lines, i, "insert", table_name)
            if block:
                blocks.append(block)
                i = block.end_line  # skip past block
                continue

        # Detect sendmail
        if re.search(r"\bsendmail\b", stripped, re.IGNORECASE):
            block = _extract_bracket_block(lines, i, "sendmail", None)
            if block:
                blocks.append(block)
                i = block.end_line
                continue

        i += 1

    return blocks


def _extract_bracket_block(lines: List[str], start_idx: int,
                           block_type: str, target_table: Optional[str]) -> Optional[Block]:
    """Extract a [...] block starting from start_idx."""
    # Find opening [
    bracket_line = None
    for j in range(start_idx, min(start_idx + 3, len(lines))):
        if "[" in lines[j]:
            bracket_line = j
            break
    if bracket_line is None:
        return None

    # Collect until closing ]
    raw_lines = []
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
    fields = {}
    for j in range(bracket_line + 1, end_idx + 1):
        line = lines[j].strip()
        if line.startswith("]") or line.startswith("["):
            continue
        if is_comment_line(line):
            continue

        # Try = assignment (insert into)
        eq_match = re.match(r"(\w+)\s*=\s*(.+?)(?:\s*$)", line)
        # Try : assignment (sendmail)
        colon_match = re.match(r"(\w+)\s*:\s*(.+?)(?:\s*$)", line)

        if block_type == "insert" and eq_match:
            fname = eq_match.group(1)
            fval = eq_match.group(2).strip()
            fields[fname] = FieldAssignment(fname, fval, j + 1, "=")
        elif block_type == "insert" and colon_match and not eq_match:
            # Colon in insert block -- will be flagged by DG009
            fname = colon_match.group(1)
            fval = colon_match.group(2).strip()
            fields[fname] = FieldAssignment(fname, fval, j + 1, ":")
        elif block_type == "sendmail" and colon_match:
            fname = colon_match.group(1)
            fval = colon_match.group(2).strip()
            fields[fname] = FieldAssignment(fname, fval, j + 1, ":")
        elif block_type == "sendmail" and eq_match and not colon_match:
            # Equals in sendmail -- unusual but parse it
            fname = eq_match.group(1)
            fval = eq_match.group(2).strip()
            fields[fname] = FieldAssignment(fname, fval, j + 1, "=")

    return Block(
        block_type=block_type,
        target_table=target_table,
        start_line=start_idx + 1,  # 1-based
        end_line=end_idx + 1,      # 1-based
        fields=fields,
        raw_lines=raw_lines,
    )


# ============================================================
# Line-scoped rules (Pass 2)
# ============================================================

def check_dg001(filename: str, line: str, lineno: int) -> List[Diagnostic]:
    """Banned function: lpad() / rpad()"""
    diags = []
    for func in BANNED_FUNCTIONS:
        if re.search(rf"\b{func}\s*\(", line):
            diags.append(Diagnostic(
                filename, lineno, "ERROR", "DG001",
                f"Banned function '{func}()' does not exist in Deluge. Use manual string padding."
            ))
    return diags


def check_dg002(filename: str, line: str, lineno: int) -> List[Diagnostic]:
    """Banned variable: zoho.loginuserrole"""
    if re.search(r"\bzoho\.loginuserrole\b", line):
        return [Diagnostic(
            filename, lineno, "ERROR", "DG002",
            "zoho.loginuserrole does NOT exist. Use thisapp.permissions.isUserInRole(\"Role Name\")."
        )]
    return []


def check_dg003(filename: str, line: str, lineno: int, file_type: str) -> List[Diagnostic]:
    """hoursBetween in scheduled scripts"""
    if file_type == "scheduled" and re.search(r"\bhoursBetween\b", line):
        return [Diagnostic(
            filename, lineno, "ERROR", "DG003",
            "hoursBetween not available on Free Trial daily schedules. Use daysBetween."
        )]
    return []


def check_dg004(filename: str, line: str, lineno: int) -> List[Diagnostic]:
    """Unknown input.FieldName reference"""
    diags = []
    for match in re.finditer(r"\binput\.(\w+)", line):
        field_name = match.group(1)
        # Allow sub-field access on known fields (e.g., input.Employee_Name1.first_name)
        if field_name not in VALID_EXPENSE_FIELDS:
            diags.append(Diagnostic(
                filename, lineno, "ERROR", "DG004",
                f"Unknown field 'input.{field_name}'. Valid fields: check docs/build-guide/field-link-names.md"
            ))
    return diags


def check_dg008(filename: str, line: str, lineno: int) -> List[Diagnostic]:
    """Single quotes used for text (not date/time)"""
    diags = []
    for match in re.finditer(r"'([^']*)'", line):
        content = match.group(1)
        if not content:
            continue
        # Allow date/datetime patterns
        if DATE_PATTERN.match(content):
            continue
        # Allow time patterns like 14:30:00
        if re.match(r"^\d{2}:\d{2}(:\d{2})?$", content):
            continue
        diags.append(Diagnostic(
            filename, lineno, "ERROR", "DG008",
            f"Single quotes used for text '{content}'. Use double quotes for strings; single quotes are for dates/times only."
        ))
    return diags


def check_dg011(filename: str, line: str, lineno: int) -> List[Diagnostic]:
    """Unknown status value"""
    match = re.search(r'\.status\s*=\s*"([^"]*)"', line)
    if match:
        status = match.group(1)
        if status not in VALID_STATUSES:
            return [Diagnostic(
                filename, lineno, "WARN", "DG011",
                f"Unknown status value \"{status}\". Valid: {', '.join(sorted(VALID_STATUSES))}"
            )]
    return []


def check_dg013(filename: str, line: str, lineno: int) -> List[Diagnostic]:
    """Mixed && and || without parentheses (Creator precedence gotcha)"""
    if "&&" in line and "||" in line:
        return [Diagnostic(
            filename, lineno, "WARN", "DG013",
            "Mixed && and || on same line. Creator evaluates OR before AND (opposite of most languages). Use explicit parentheses."
        )]
    return []


def check_dg015_016(filename: str, line: str, lineno: int) -> List[Diagnostic]:
    """Hardcoded email addresses"""
    diags = []
    # Skip lines that reference zoho email variables
    if "zoho.adminuserid" in line or "zoho.loginuserid" in line:
        return []

    for match in EMAIL_PATTERN.finditer(line):
        email = match.group(0)
        domain = email.split("@")[1].lower() if "@" in email else ""

        # Check if it's in a string literal (between quotes)
        # Simple check: the email appears within quotes on this line
        if f'"{email}"' not in line and f"'{email}'" not in line:
            # Might be part of a larger expression, still flag
            pass

        if any(d in domain for d in DEMO_EMAIL_DOMAINS) or "demo" in email.lower():
            diags.append(Diagnostic(
                filename, lineno, "WARN", "DG015",
                f"Hardcoded demo/placeholder email '{email}'. Replace with role-based lookup for production."
            ))
        else:
            diags.append(Diagnostic(
                filename, lineno, "INFO", "DG016",
                f"Hardcoded email '{email}'. Consider using role-based lookup."
            ))
    return diags


def run_line_rules(filename: str, lines: List[str], file_type: str) -> List[Diagnostic]:
    """Run all line-scoped rules."""
    diags = []
    for i, raw_line in enumerate(lines):
        lineno = i + 1
        if is_comment_line(raw_line):
            continue
        line = strip_comments(raw_line)

        diags.extend(check_dg001(filename, line, lineno))
        diags.extend(check_dg002(filename, line, lineno))
        diags.extend(check_dg003(filename, line, lineno, file_type))
        diags.extend(check_dg004(filename, line, lineno))
        diags.extend(check_dg008(filename, line, lineno))
        diags.extend(check_dg011(filename, line, lineno))
        diags.extend(check_dg013(filename, line, lineno))
        diags.extend(check_dg015_016(filename, line, lineno))

    return diags


# ============================================================
# Block-scoped rules (Pass 3)
# ============================================================

def check_dg006(filename: str, block: Block) -> List[Diagnostic]:
    """Missing Added_User in insert into approval_history"""
    if block.block_type != "insert" or block.target_table != "approval_history":
        return []
    if "Added_User" not in block.fields:
        return [Diagnostic(
            filename, block.start_line, "ERROR", "DG006",
            "Missing 'Added_User = zoho.loginuser' in insert into approval_history block."
        )]
    return []


def check_dg007(filename: str, block: Block) -> List[Diagnostic]:
    """Wrong Added_User value"""
    if block.block_type != "insert" or block.target_table != "approval_history":
        return []
    if "Added_User" in block.fields:
        val = block.fields["Added_User"].value.strip()
        if val != "zoho.loginuser":
            return [Diagnostic(
                filename, block.fields["Added_User"].line, "ERROR", "DG007",
                f"Added_User must be 'zoho.loginuser', got '{val}'."
            )]
    return []


def check_dg009(filename: str, block: Block) -> List[Diagnostic]:
    """Colon instead of = in insert into blocks"""
    if block.block_type != "insert":
        return []
    diags = []
    for fa in block.fields.values():
        if fa.separator == ":":
            diags.append(Diagnostic(
                filename, fa.line, "ERROR", "DG009",
                f"Field '{fa.name}' uses ':' separator in insert block. Use '=' (colons are for sendmail)."
            ))
    return diags


def check_dg010(filename: str, block: Block) -> List[Diagnostic]:
    """Missing required sendmail params"""
    if block.block_type != "sendmail":
        return []
    diags = []
    param_names = {k.lower().strip() for k in block.fields.keys()}
    for req in REQUIRED_SENDMAIL_PARAMS:
        if req not in param_names:
            diags.append(Diagnostic(
                filename, block.start_line, "ERROR", "DG010",
                f"Missing required sendmail parameter '{req}'."
            ))
    return diags


def check_dg012(filename: str, block: Block) -> List[Diagnostic]:
    """Unknown action_1 value in audit trail"""
    if block.block_type != "insert" or block.target_table != "approval_history":
        return []
    if "action_1" in block.fields:
        val = block.fields["action_1"].value.strip().strip('"')
        if val not in VALID_ACTIONS:
            return [Diagnostic(
                filename, block.fields["action_1"].line, "WARN", "DG012",
                f"Unknown action_1 value \"{val}\". Valid: {', '.join(sorted(VALID_ACTIONS))}"
            )]
    return []


def check_dg014(filename: str, lines: List[str]) -> List[Diagnostic]:
    """Threshold fallback not 999.99"""
    diags = []
    for i, line in enumerate(lines):
        lineno = i + 1
        if is_comment_line(line):
            continue
        stripped = strip_comments(line)
        # Look for threshold-related fallback assignments
        if re.search(r"\bthreshold\w*\s*=\s*(\d+\.?\d*)", stripped, re.IGNORECASE):
            match = re.search(r"\bthreshold\w*\s*=\s*(\d+\.?\d*)", stripped, re.IGNORECASE)
            if match:
                val = match.group(1)
                if val != THRESHOLD_FALLBACK and float(val) != float(THRESHOLD_FALLBACK):
                    diags.append(Diagnostic(
                        filename, lineno, "WARN", "DG014",
                        f"Threshold fallback value is {val}, expected {THRESHOLD_FALLBACK} (matching seed data)."
                    ))
        # Also check ifnull with threshold context
        if "ifnull" in stripped and "threshold" in stripped.lower():
            match = re.search(r"ifnull\s*\([^,]+,\s*(\d+\.?\d*)\s*\)", stripped)
            if match:
                val = match.group(1)
                if val != THRESHOLD_FALLBACK and float(val) != float(THRESHOLD_FALLBACK):
                    diags.append(Diagnostic(
                        filename, lineno, "WARN", "DG014",
                        f"Threshold ifnull fallback is {val}, expected {THRESHOLD_FALLBACK} (matching seed data)."
                    ))
    return diags


def run_block_rules(filename: str, blocks: List[Block], lines: List[str]) -> List[Diagnostic]:
    """Run all block-scoped rules."""
    diags = []
    for block in blocks:
        diags.extend(check_dg006(filename, block))
        diags.extend(check_dg007(filename, block))
        diags.extend(check_dg009(filename, block))
        diags.extend(check_dg010(filename, block))
        diags.extend(check_dg012(filename, block))
    diags.extend(check_dg014(filename, lines))
    return diags


# ============================================================
# File-scoped rules (Pass 4)
# ============================================================

def check_dg005(filename: str, lines: List[str]) -> List[Diagnostic]:
    """Query result used without null guard."""
    diags = []
    query_vars: Dict[str, int] = {}  # var_name -> assignment line (1-based)
    guarded_vars: Set[str] = set()
    guard_scopes: List[Tuple[str, int]] = []  # (var_name, brace_depth_at_guard)
    brace_depth = 0

    for i, raw_line in enumerate(lines):
        lineno = i + 1
        if is_comment_line(raw_line):
            continue
        line = strip_comments(raw_line)

        # Track brace depth
        brace_depth += line.count("{") - line.count("}")

        # Pop guard scopes when braces close
        while guard_scopes and brace_depth < guard_scopes[-1][1]:
            var = guard_scopes.pop()[0]
            guarded_vars.discard(var)

        # Detect query assignment: var = TableName[criteria]
        # Pattern: word = word[ but NOT inside strings
        q_match = re.match(r"\s*(\w+)\s*=\s*(\w+)\s*\[", line)
        if q_match:
            var_name = q_match.group(1)
            table_name = q_match.group(2)
            # Exclude common non-table patterns (e.g., "row = insert into")
            if table_name not in ("insert", "into", "if", "for", "while"):
                query_vars[var_name] = lineno

        # Detect null guard: if (var != null or if(var != null
        guard_match = re.search(r"if\s*\(\s*(\w+)\s*!=\s*null", line)
        if guard_match:
            var_name = guard_match.group(1)
            if var_name in query_vars:
                guarded_vars.add(var_name)
                guard_scopes.append((var_name, brace_depth))

        # Detect unguarded access: var.field or var.method()
        for var_name, assign_line in query_vars.items():
            if var_name in guarded_vars:
                continue
            if lineno == assign_line:
                continue
            # Check for var.something access
            if re.search(rf"\b{re.escape(var_name)}\.(\w+)", line):
                # Don't flag if this line IS the null check
                if guard_match and guard_match.group(1) == var_name:
                    continue
                diags.append(Diagnostic(
                    filename, lineno, "ERROR", "DG005",
                    f"Query result '{var_name}' accessed without null guard. Add: if ({var_name} != null && {var_name}.count() > 0)"
                ))
                # Only flag once per variable to avoid noise
                guarded_vars.add(var_name)

    return diags


# ============================================================
# Main pipeline
# ============================================================

def lint_file(filepath: str) -> List[Diagnostic]:
    """Run all lint passes on a single .dg file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError) as e:
        return [Diagnostic(filepath, 0, "ERROR", "DG000", f"Cannot read file: {e}")]

    # Strip newlines but preserve original for line counting
    lines = [line.rstrip("\n\r") for line in lines]

    file_type = detect_file_type(filepath)

    # Pass 1: Extract blocks
    blocks = extract_blocks(lines)

    # Pass 2: Line rules
    diags = run_line_rules(filepath, lines, file_type)

    # Pass 3: Block rules
    diags.extend(run_block_rules(filepath, blocks, lines))

    # Pass 4: File-scope rules
    diags.extend(check_dg005(filepath, lines))

    return diags


def resolve_files(paths: List[str]) -> List[str]:
    """Expand directories to .dg files, pass through individual files."""
    files = []
    for path in paths:
        if os.path.isdir(path):
            for root, _dirs, filenames in os.walk(path):
                for fn in sorted(filenames):
                    if fn.endswith(".dg"):
                        files.append(os.path.join(root, fn))
        elif os.path.isfile(path) and path.endswith(".dg"):
            files.append(path)
        else:
            print(f"Warning: skipping '{path}' (not a .dg file or directory)", file=sys.stderr)
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Deluge script linter for .dg files",
        epilog="Exit codes: 0=clean, 1=warnings, 2=errors"
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to lint")
    parser.add_argument("-q", "--quiet", action="store_true", help="Only show errors, suppress warnings and info")
    parser.add_argument("--errors-only", action="store_true", help="Only show ERROR severity")
    args = parser.parse_args()

    files = resolve_files(args.paths)
    if not files:
        print("No .dg files found.", file=sys.stderr)
        sys.exit(0)

    all_diags: List[Diagnostic] = []
    for filepath in files:
        all_diags.extend(lint_file(filepath))

    # Filter by severity if requested
    if args.errors_only:
        all_diags = [d for d in all_diags if d.severity == "ERROR"]
    elif args.quiet:
        all_diags = [d for d in all_diags if d.severity in ("ERROR", "WARN")]

    # Sort and output
    all_diags.sort(key=lambda d: (d.filename, d.line, d.severity))
    for diag in all_diags:
        print(str(diag))

    # Summary
    errors = sum(1 for d in all_diags if d.severity == "ERROR")
    warnings = sum(1 for d in all_diags if d.severity == "WARN")
    infos = sum(1 for d in all_diags if d.severity == "INFO")
    total_files = len(files)

    print(f"\n--- Linted {total_files} file(s): {errors} error(s), {warnings} warning(s), {infos} info(s) ---")

    sys.exit(2 if errors > 0 else 1 if warnings > 0 else 0)


if __name__ == "__main__":
    main()
