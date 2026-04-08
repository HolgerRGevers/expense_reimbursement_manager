#!/usr/bin/env python3
"""
Rebuild the Employee Dashboard in the .ds export file.

Replaces the dspZml CDATA blocks with native Zoho Creator dashboard
components (text, chart, report) that render responsively on desktop,
tablet, and mobile.

Usage:
    python tools/rebuild_employee_dashboard.py exports/Expense_Reimbursement_Management-stage.ds
    python tools/rebuild_employee_dashboard.py exports/FILE.ds --dry-run
"""

from __future__ import annotations

import argparse
import os
import re
import sys


def build_employee_dashboard_zml() -> str:
    """Build the new Employee Dashboard ZML using native components only."""

    # Row 1: Header banner with title + submit button
    header_row = (
        "<row>\n"
        "\t<column width='100%'>\n"
        "\t<panel elementName='Header_Banner'\n"
        "\t\tbgColor = '#5A3D9B'\n"
        ">\n"
        "<pr width='fill' height='fill'>\n"
        "<pc\n"
        "\tpadding = '24px'\n"
        "\twidth = '75%'\n"
        "\thAlign = 'left'\n"
        "\tvAlign = 'middle'\n"
        ">\n"
        "<pr><pc>\n"
        "<text\n"
        "\tcolor = '#FFFFFF'\n"
        "\tsize = '26px'\n"
        "\tbold = 'true'\n"
        "\ttype = 'Text'\n"
        "\tvalue = 'My Expense Dashboard'\n"
        "/>\n"
        "</pc></pr>\n"
        "<pr><pc>\n"
        "<text\n"
        "\tmarginTop = '5px'\n"
        "\tcolor = '#E0D4F5'\n"
        "\tsize = '14px'\n"
        "\ttype = 'Text'\n"
        "\tvalue = 'Submit, track and manage your expense claims'\n"
        "/>\n"
        "</pc></pr>\n"
        "</pc>\n"
        "<pc\n"
        "\tpadding = '15px'\n"
        "\tbgColor = '#0F6E56'\n"
        "\thAlign = 'center'\n"
        "\tvAlign = 'middle'\n"
        "\tcornerRadius = '8px'\n"
        ">\n"
        "<pr><pc hAlign='center'>\n"
        "<text\n"
        "\taction = 'OpenForm'\n"
        "\tcomponentLinkName = 'expense_claims'\n"
        "\ttarget = 'same-window'\n"
        "\tcolor = '#FFFFFF'\n"
        "\tsize = '15px'\n"
        "\tbold = 'true'\n"
        "\ttype = 'Text'\n"
        "\tvalue = 'Submit New Claim'\n"
        "/>\n"
        "</pc></pr>\n"
        "</pc>\n"
        "</pr>\n"
        "</panel>\n"
        "\t</column>\n"
        "</row>"
    )

    # Helper to build a KPI tile
    def kpi_tile(bg_color: str, icon_bg: str, icon: str,
                 value_expr: str, label: str, label_color: str,
                 criteria: str = "") -> str:
        criteria_attr = ""
        if criteria:
            criteria_attr = f"\n\tcriteria = '{criteria}'"
        return (
            f"<pc\n"
            f"\tpadding = '20px'\n"
            f"\tbgColor = '{bg_color}'\n"
            f"\twidth = '25%'\n"
            f"\thAlign = 'left'\n"
            f"\tvAlign = 'middle'\n"
            f">\n"
            f"<pr width='auto' height='auto'>\n"
            f"<pc>\n"
            f"<image\n"
            f"\tcolor = '#FFFFFF'\n"
            f"\tbgColor = '{icon_bg}'\n"
            f"\twidth = '48px'\n"
            f"\theight = '48px'\n"
            f"\ttype = 'icon'\n"
            f"\tvalue = '{icon}'\n"
            f"\tsize = '20px'\n"
            f"\tcornerRadius = '10px'\n"
            f"\ticonType = 'outline'\n"
            f"/>\n"
            f"</pc>\n"
            f"<pc hAlign='left'>\n"
            f"<pr><pc>\n"
            f"<text\n"
            f"\tmarginLeft = '16px'\n"
            f"\tcolor = '#FFFFFF'\n"
            f"\tsize = '22px'\n"
            f"\tbold = 'true'\n"
            f"\ttype = 'Form Data'\n"
            f"\tdisplayType = 'actual'\n"
            f"\tthousandsSeperator = 'LOCALE'\n"
            f"\tdecimalSeperator = 'DOT'\n"
            f"\tnumberScale = 'none'\n"
            f"\tvalue = '{value_expr}'{criteria_attr}\n"
            f"/>\n"
            f"</pc></pr>\n"
            f"<pr><pc>\n"
            f"<text\n"
            f"\tmarginLeft = '16px'\n"
            f"\tmarginTop = '3px'\n"
            f"\tcolor = '{label_color}'\n"
            f"\tsize = '13px'\n"
            f"\ttype = 'Text'\n"
            f"\tvalue = '{label}'\n"
            f"/>\n"
            f"</pc></pr>\n"
            f"</pc>\n"
            f"</pr>\n"
            f"</pc>\n"
        )

    # Row 2: 4 KPI tiles
    kpi_row = (
        "<row>\n"
        "\t<column width='100%'>\n"
        "\t<panel elementName='KPI_Tiles'\n"
        "\t\ttitle = 'Key Metrics'\n"
        "\t\ttitleSize = '15px'\n"
        ">\n"
        "<pr width='fill' height='fill'>\n"
        "<pc\n"
        "\tpaddingTop = '10px'\n"
        "\tbgColor = '#FFFFFF'\n"
        "\twidth = '100%'\n"
        ">\n"
        "<pr width='fill' height='fill'>\n"
        + kpi_tile(
            "#0F6E56", "#1ABE75", "business-percentage-39",
            "thisapp.expense_claims.amount_zar.sum",
            "Approved (ZAR)", "#E1F5EE",
            'status == &quot;Approved&quot;',
        )
        + kpi_tile(
            "#3C3489", "#734AD0", "education-paper",
            "thisapp.expense_claims.ID.count",
            "Total Claims", "#CECBF6",
        )
        + kpi_tile(
            "#854F0B", "#F6BC2B", "design-todo",
            "thisapp.expense_claims.ID.count",
            "Pending Approval", "#FAEEDA",
            'status == &quot;Pending LM Approval&quot; || status == &quot;Pending HoD Approval&quot;',
        )
        + kpi_tile(
            "#8B2020", "#E2335C", "arrows-circle-remove",
            "thisapp.expense_claims.ID.count",
            "Rejected", "#F5D5D5",
            'status == &quot;Rejected&quot;',
        )
        + "</pr>\n"
        "</pc>\n"
        "</pr>\n"
        "</panel>\n"
        "\t</column>\n"
        "</row>"
    )

    # Row 3: Two charts side by side
    charts_row = (
        "<row>\n"
        "\t<column width='50%'>\n"
        "\t<chart \n"
        "\telementName='Status_Chart'\n"
        "\t\ttype = 'Pie'\n"
        "\t\ttitle = 'Claims by Status'\n"
        "\t\ttitleSize = '15px'\n"
        "\t\txfield = 'status'\n"
        "\t\tyfield = 'count:status'\n"
        "\t\tappLinkName = 'thisapp'\n"
        "\t\tformLinkName = 'expense_claims'\n"
        "\t\tlegendPos = 'bottom'\n"
        "\t\theightType = 'custom'\n"
        "\t\theightValue = '350'\n"
        "/>\n"
        "\t</column>\n"
        "\t<column width='50%'>\n"
        "\t<chart \n"
        "\telementName='Category_Chart'\n"
        "\t\ttype = 'Bar'\n"
        "\t\ttitle = 'Spend by Category (ZAR)'\n"
        "\t\ttitleSize = '15px'\n"
        "\t\txfield = 'category'\n"
        "\t\tyfield = 'sum:amount_zar'\n"
        "\t\tappLinkName = 'thisapp'\n"
        "\t\tformLinkName = 'expense_claims'\n"
        "\t\tlegendPos = 'none'\n"
        "\t\theightType = 'custom'\n"
        "\t\theightValue = '350'\n"
        "/>\n"
        "\t</column>\n"
        "</row>"
    )

    # Row 4: Embedded report (read-only)
    report_row = (
        "<row>\n"
        "\t<column width='100%'>\n"
        "\t<report \n"
        "\telementName='My_Claims_Report'\n"
        "\t\tappLinkName = 'thisapp'\n"
        "\t\tlinkName = 'expense_claims_Report'\n"
        "\t\tiszreport = 'false'\n"
        "\t\tzc_AddRec = 'false'\n"
        "\t\tzc_EditRec = 'false'\n"
        "\t\tzc_Print = 'false'\n"
        "\t\tzc_DelRec = 'false'\n"
        "\t\tzc_DuplRec = 'false'\n"
        "\t\tzc_EditBulkRec = 'false'\n"
        "\t\tzc_BulkDelete = 'false'\n"
        "\t\tzc_BulkDuplicate = 'false'\n"
        "\t\tzc_Export = 'false'\n"
        "\theightType = 'auto'\n"
        "\theightValue = '600'\n"
        "/>\n"
        "\t</column>\n"
        "</row>"
    )

    # Assemble full ZML
    web_config = '{"layout":{"displayType":"card","design":"fluid","style":"padding:0px;"}}'
    zml = (
        f"<zml webDeviceConfig='{web_config}'>\n"
        f"\t<layout>\n"
        f"{header_row}\n"
        f"{kpi_row}\n"
        f"{charts_row}\n"
        f"{report_row}\n"
        f"\t</layout>\n"
        f"</zml>"
    )

    return zml


def replace_dashboard_content(ds_content: str, new_zml: str) -> str:
    """Replace the Employee_Dashboard Content attribute in the .ds file."""
    # Strategy: Find the Employee_Dashboard page block, then locate the
    # Content="..." attribute. The Content value ends with </zml>"
    # followed by a newline and closing brace.

    # Step 1: Find the page block start
    marker = 'page Employee_Dashboard'
    start_idx = ds_content.find(marker)
    if start_idx == -1:
        print("ERROR: Could not find Employee_Dashboard page block", file=sys.stderr)
        sys.exit(1)

    # Step 2: Find Content=" within the block
    content_start = ds_content.find('Content="', start_idx)
    if content_start == -1 or content_start > start_idx + 5000:
        print("ERROR: Could not find Content attribute in Employee_Dashboard", file=sys.stderr)
        sys.exit(1)

    # Move past Content="
    value_start = content_start + len('Content="')

    # Step 3: Find the end of the Content value -- it ends with </zml>"
    # The closing pattern is </zml>" at the end of the attribute
    end_marker = '</zml>"'
    end_idx = ds_content.find(end_marker, value_start)
    if end_idx == -1:
        print("ERROR: Could not find </zml>\" end marker", file=sys.stderr)
        sys.exit(1)

    # end_idx points to start of </zml>", we want to include </zml> but not the closing "
    value_end = end_idx + len('</zml>')

    # Step 4: Escape the new ZML for the Content attribute
    # Convert newlines/tabs to literal \n \t (as the .ds format stores them)
    escaped_zml = new_zml.replace("\n", "\\n").replace("\t", "\\t")

    # Step 5: Replace
    result = ds_content[:value_start] + escaped_zml + ds_content[value_end:]

    print(f"Replaced Employee_Dashboard Content (old: {value_end - value_start} chars, new: {len(escaped_zml)} chars)")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild Employee Dashboard with native Zoho Creator components",
    )
    parser.add_argument(
        "ds_file",
        help="Path to .ds export file",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print new ZML without modifying the file",
    )
    args = parser.parse_args()

    if not os.path.exists(args.ds_file):
        print(f"Error: File not found: {args.ds_file}", file=sys.stderr)
        sys.exit(1)

    # Build the new dashboard ZML
    new_zml = build_employee_dashboard_zml()

    if args.dry_run:
        print("=== New Employee Dashboard ZML ===")
        print(new_zml)
        print(f"\n=== ZML length: {len(new_zml)} characters ===")
        return

    # Read the .ds file
    with open(args.ds_file, "r", encoding="utf-8") as f:
        ds_content = f.read()

    # Replace the dashboard content
    updated = replace_dashboard_content(ds_content, new_zml)

    # Write back
    with open(args.ds_file, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"Updated: {args.ds_file}")
    print("Import this .ds file into Zoho Creator to see the new dashboard.")


if __name__ == "__main__":
    main()
