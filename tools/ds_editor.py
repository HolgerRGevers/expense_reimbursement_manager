#!/usr/bin/env python3
"""
Zoho Creator .ds Export Editor.

Programmatic modifications to .ds export files for deployment via import.
Reads configuration from config/ YAML files and applies changes to the .ds.

Subcommands:
    add-descriptions   Add field help text from config/field-descriptions.yaml
    remove-reports     Remove named reports and all their references
    restrict-menus     Strip Edit/Duplicate/Delete from report menus
    audit              Show current state: descriptions, reports, menu permissions

Usage:
    python tools/ds_editor.py add-descriptions exports/FILE.ds
    python tools/ds_editor.py remove-reports exports/FILE.ds --reports name1,name2
    python tools/ds_editor.py restrict-menus exports/FILE.ds --reports name1,name2
    python tools/ds_editor.py audit exports/FILE.ds
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ============================================================
# Simple YAML loader (stdlib only)
# ============================================================

def load_field_descriptions(yaml_path: Path) -> dict[str, dict[str, str]]:
    """Load field-descriptions.yaml into {form: {field: description}}."""
    result: dict[str, dict[str, str]] = {}
    current_form = ""

    with open(yaml_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Top-level form key (no indent, ends with :)
            if not line.startswith(" ") and stripped.endswith(":"):
                current_form = stripped.rstrip(":")
                result[current_form] = {}
                continue

            # Field entry (indented, key: "value")
            m = re.match(r'^\s+(\w+):\s*"(.+)"\s*$', line)
            if m and current_form:
                result[current_form][m.group(1)] = m.group(2)

    return result


# ============================================================
# Add descriptions
# ============================================================

def add_descriptions(ds_path: Path, descriptions: dict[str, dict[str, str]]) -> int:
    """Add help_text description blocks to fields in a .ds file.

    Returns the number of descriptions added.
    """
    with open(ds_path, encoding="utf-8") as f:
        lines = f.read().split("\n")

    # Flatten descriptions for lookup: {field_name: {form_name: desc}}
    field_to_forms: dict[str, dict[str, str]] = {}
    for form, fields in descriptions.items():
        for field, desc in fields.items():
            if field not in field_to_forms:
                field_to_forms[field] = {}
            field_to_forms[field][form] = desc

    current_form = ""
    added = 0
    i = 0

    while i < len(lines):
        # Track current form
        form_match = re.match(r"^\t{2,3}form\s+(\w+)\s*$", lines[i])
        if form_match:
            current_form = form_match.group(1)

        # Find field definitions: field_name followed by (
        field_match = re.match(r"^\t{3,4}(?:must have\s+)?(\w+)\s*$", lines[i])
        if field_match and i + 1 < len(lines) and lines[i + 1].strip() == "(":
            field_name = field_match.group(1)

            # Skip non-field entries
            if field_name in (
                "Section", "actions", "submit", "reset", "update", "cancel",
                "prefix", "first_name", "last_name", "suffix",
            ):
                i += 1
                continue

            # Check if already has description
            has_desc = False
            j = i + 2
            paren_depth = 1
            while j < len(lines) and paren_depth > 0:
                paren_depth += lines[j].count("(") - lines[j].count(")")
                if "type = help_text" in lines[j]:
                    has_desc = True
                    break
                j += 1

            if has_desc:
                i += 1
                continue

            # Find description text
            desc = None
            if field_name in field_to_forms:
                if current_form in field_to_forms[field_name]:
                    desc = field_to_forms[field_name][current_form]
                elif len(field_to_forms[field_name]) == 1:
                    # Only one form has this field -- use it
                    desc = next(iter(field_to_forms[field_name].values()))

            if desc:
                # Find the row = 1 line to insert before
                j = i + 2
                paren_depth = 1
                insert_at = None
                while j < len(lines) and paren_depth > 0:
                    paren_depth += lines[j].count("(") - lines[j].count(")")
                    if "row = 1" in lines[j] and paren_depth == 1:
                        insert_at = j
                        break
                    j += 1

                if insert_at:
                    indent = "\t\t\t\t"
                    desc_block = [
                        f"{indent}description",
                        f"{indent}[",
                        f"{indent}\ttype = help_text",
                        f'{indent}\tmessage = "{desc}"',
                        f"{indent}]",
                    ]
                    for k, desc_line in enumerate(desc_block):
                        lines.insert(insert_at + k, desc_line)
                    added += 1
                    i = insert_at + len(desc_block)
                    continue

        i += 1

    with open(ds_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return added


# ============================================================
# Remove reports
# ============================================================

def remove_reports(ds_path: Path, report_names: list[str]) -> int:
    """Remove named reports and all references from a .ds file.

    Returns the number of reports removed.
    """
    with open(ds_path, encoding="utf-8") as f:
        content = f.read()

    removed = 0
    for name in report_names:
        # Remove report definition blocks (kanban or list)
        for report_type in ["kanban", "list"]:
            pattern = rf"\t+{report_type}\s+{re.escape(name)}\s*\{{[^}}]*\}}"
            if re.search(pattern, content, re.DOTALL):
                # More robust: line-by-line removal
                pass

        # Remove permission references
        content = re.sub(rf"\n\t+{re.escape(name)}=\{{[^}}]*\}}", "", content)

        # Remove menu entries
        content = re.sub(
            rf"\n\t+report {re.escape(name)}\s*\{{[^}}]*\}}",
            "",
            content,
        )

        # Line-by-line block removal for report definitions
        lines = content.split("\n")
        new_lines: list[str] = []
        skipping = False
        skip_depth = 0

        for line in lines:
            if not skipping and re.match(
                rf"^\t+(?:kanban|list)\s+{re.escape(name)}\s*$", line.rstrip()
            ):
                skipping = True
                skip_depth = 0
                removed += 1
                continue
            if skipping:
                skip_depth += line.count("{") - line.count("}")
                if skip_depth <= 0 and "}" in line:
                    skipping = False
                    continue
                continue
            new_lines.append(line)

        content = "\n".join(new_lines)

    with open(ds_path, "w", encoding="utf-8") as f:
        f.write(content)

    return removed


# ============================================================
# Restrict menus
# ============================================================

MENU_ITEMS_TO_REMOVE = {"Edit", "Duplicate", "Delete", "Print", "Add", "Import", "Export"}


def restrict_menus(ds_path: Path, report_names: list[str]) -> int:
    """Remove Edit/Duplicate/Delete/etc from report menus.

    Returns the number of reports modified.
    """
    with open(ds_path, encoding="utf-8") as f:
        lines = f.read().split("\n")

    modified = 0
    in_target = False
    current_report = ""
    i = 0
    new_lines: list[str] = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Track report context
        report_match = re.match(r"\t+report\s+(\w+)\s*$", line)
        if report_match:
            current_report = report_match.group(1)
            in_target = current_report in report_names

        if in_target:
            # Remove menu items from header blocks
            if stripped == "header":
                new_lines.append(line)
                i += 1
                if i < len(lines) and lines[i].strip() == "(":
                    new_lines.append(lines[i])
                    depth = 1
                    i += 1
                    while i < len(lines) and depth > 0:
                        s = lines[i].strip()
                        depth += s.count("(") - s.count(")")
                        if depth <= 0:
                            new_lines.append(lines[i])
                            break
                        if s in MENU_ITEMS_TO_REMOVE:
                            i += 1
                            continue
                        new_lines.append(lines[i])
                        i += 1
                    modified += 1
                    i += 1
                    continue

            # Remove entire record block (keyword + parens + content)
            if stripped == "record":
                # Skip "record" line
                i += 1
                if i < len(lines) and lines[i].strip() == "(":
                    # Skip everything until matching )
                    depth = 1
                    i += 1
                    while i < len(lines) and depth > 0:
                        depth += lines[i].strip().count("(") - lines[i].strip().count(")")
                        i += 1
                    continue
                continue

            # Remove entire right-click blocks
            if stripped == "on right click":
                i += 1
                if i < len(lines) and lines[i].strip() == "(":
                    depth = 1
                    i += 1
                    while i < len(lines) and depth > 0:
                        depth += lines[i].strip().count("(") - lines[i].strip().count(")")
                        i += 1
                    continue

        new_lines.append(line)
        i += 1

    with open(ds_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))

    return modified


# ============================================================
# Audit
# ============================================================

def audit_ds(ds_path: Path) -> None:
    """Print audit summary of descriptions, reports, and menu permissions."""
    with open(ds_path, encoding="utf-8") as f:
        content = f.read()

    # Count descriptions
    desc_count = content.count("type = help_text")
    print(f"Field descriptions (help_text): {desc_count}")

    # Count fields (approximate)
    field_defs = len(re.findall(r"^\t{3,4}(?:must have\s+)?\w+\s*$", content, re.MULTILINE))
    print(f"Field definitions (approximate): {field_defs}")
    print(f"Description coverage: {desc_count}/{field_defs} ({100*desc_count//max(field_defs,1)}%)")

    # List reports
    print("\nReports:")
    for m in re.finditer(r"^\t+(?:list|kanban)\s+(\w+)\s*$", content, re.MULTILINE):
        report_type = "list" if "list" in m.group(0) else "kanban"
        print(f"  [{report_type}] {m.group(1)}")

    # Check menu permissions per report
    print("\nReport menu audit:")
    for m in re.finditer(r"^\t+report\s+(\w+)\s*$", content, re.MULTILINE):
        name = m.group(1)
        # Find the next ~500 chars to check for Edit/Delete
        start = m.start()
        block = content[start:start + 2000]
        has_edit = "Edit" in block.split("report", 1)[-1][:500] if "report" in block else False
        has_delete = "Delete" in block.split("report", 1)[-1][:500] if "report" in block else False
        status = "FULL" if has_edit else "RESTRICTED"
        print(f"  {name}: {status}")


# ============================================================
# Main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Zoho Creator .ds export editor",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add-descriptions
    p_desc = sub.add_parser("add-descriptions", help="Add field help text from YAML config")
    p_desc.add_argument("ds_file", help="Path to .ds file")
    p_desc.add_argument(
        "--config", default=str(Path(__file__).parent.parent / "config" / "field-descriptions.yaml"),
        help="Path to field-descriptions.yaml",
    )

    # remove-reports
    p_rm = sub.add_parser("remove-reports", help="Remove named reports and references")
    p_rm.add_argument("ds_file", help="Path to .ds file")
    p_rm.add_argument("--reports", required=True, help="Comma-separated report names to remove")

    # restrict-menus
    p_menu = sub.add_parser("restrict-menus", help="Strip Edit/Delete from report menus")
    p_menu.add_argument("ds_file", help="Path to .ds file")
    p_menu.add_argument("--reports", required=True, help="Comma-separated report names to restrict")

    # audit
    p_audit = sub.add_parser("audit", help="Audit descriptions, reports, menus")
    p_audit.add_argument("ds_file", help="Path to .ds file")

    args = parser.parse_args()
    ds_path = Path(args.ds_file)

    if not ds_path.exists():
        print(f"Error: {ds_path} not found", file=sys.stderr)
        sys.exit(1)

    if args.command == "add-descriptions":
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: {config_path} not found", file=sys.stderr)
            sys.exit(1)
        descriptions = load_field_descriptions(config_path)
        total_fields = sum(len(f) for f in descriptions.values())
        print(f"Loaded {total_fields} field descriptions from {config_path}")
        added = add_descriptions(ds_path, descriptions)
        print(f"Added {added} descriptions to {ds_path}")

    elif args.command == "remove-reports":
        names = [n.strip() for n in args.reports.split(",")]
        removed = remove_reports(ds_path, names)
        print(f"Removed {removed} report(s) from {ds_path}")

    elif args.command == "restrict-menus":
        names = [n.strip() for n in args.reports.split(",")]
        modified = restrict_menus(ds_path, names)
        print(f"Restricted menus on {modified} block(s) in {ds_path}")

    elif args.command == "audit":
        audit_ds(ds_path)


if __name__ == "__main__":
    main()
