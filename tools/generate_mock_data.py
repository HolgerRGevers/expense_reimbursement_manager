#!/usr/bin/env python3
"""
Generate mock data for stress-testing the Expense Reimbursement Manager.

Creates CSV files matching the Access/Zoho schema with realistic South African
expense data across 7 employee personas with different behaviours (normal,
rookie errors, suspicious patterns, resubmissions, self-approval bypass,
high-value Two-Key dual-approval claims).

Usage:
    python tools/generate_mock_data.py --output-dir exports/csv/
    python tools/generate_mock_data.py --output-dir exports/csv/ --seed 42
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SEED_DIR = Path(__file__).parent.parent / "config" / "seed-data"

# ---------------------------------------------------------------------------
# Employee personas
# ---------------------------------------------------------------------------

EMPLOYEES = [
    {
        "name": "Thandi Molefe",
        "email": "thandi.molefe@company.co.za",
        "department_id": 1,
        "client_ids": [1, 2],
        "role": "Employee",
        "categories": ["Travel - Local", "Meals & Entertainment", "Communication"],
        "amount_range": (45, 900),
        "behavior": "normal",
    },
    {
        "name": "Sipho Dlamini",
        "email": "sipho.dlamini@company.co.za",
        "department_id": 4,
        "client_ids": [4, 5],
        "role": "Employee",
        "categories": ["Travel - Long Distance", "Accommodation", "Office Supplies"],
        "amount_range": (200, 4500),
        "behavior": "normal",
    },
    {
        "name": "Zanele Khumalo",
        "email": "zanele.khumalo@company.co.za",
        "department_id": 2,
        "client_ids": [3],
        "role": "Employee",
        "categories": [
            "Travel - Local",
            "Meals & Entertainment",
            "Office Supplies",
            "Communication",
            "Accommodation",
            "Travel - Long Distance",
            "Client Entertainment",
        ],
        "amount_range": (0, 6000),
        "behavior": "rookie",
    },
    {
        "name": "Pieter van der Merwe",
        "email": "pieter.vandermerwe@company.co.za",
        "department_id": 3,
        "client_ids": [5],
        "role": "Line Manager",
        "categories": ["Office Supplies", "Communication", "Meals & Entertainment"],
        "amount_range": (50, 2500),
        "behavior": "line_manager",
    },
    {
        "name": "Nomsa Sithole",
        "email": "nomsa.sithole@company.co.za",
        "department_id": 1,
        "client_ids": [1, 3],
        "role": "Employee",
        "categories": ["Client Entertainment", "Meals & Entertainment"],
        "amount_range": (500, 9999),
        "behavior": "suspicious",
    },
    {
        "name": "Bongani Nkosi",
        "email": "bongani.nkosi@company.co.za",
        "department_id": 5,
        "client_ids": [2],
        "role": "Employee",
        "categories": ["Communication", "Travel - Local", "Office Supplies"],
        "amount_range": (99, 1500),
        "behavior": "resubmitter",
    },
    {
        "name": "Lindiwe Mahlangu",
        "email": "lindiwe.mahlangu@company.co.za",
        "department_id": 1,
        "client_ids": [1, 4],
        "role": "Employee",
        "categories": ["Travel - Long Distance", "Client Entertainment", "Accommodation"],
        "amount_range": (3000, 9500),
        "behavior": "high_value",
    },
]

# ---------------------------------------------------------------------------
# Description templates (realistic South African vendors)
# ---------------------------------------------------------------------------

DESCRIPTIONS = {
    "Travel - Local": [
        "Uber from Sandton to OR Tambo International",
        "Bolt to MTN head office Fairland",
        "Gautrain Sandton to Pretoria return",
        "MyCiti bus Cape Town CBD to Bellville",
        "Uber from Rosebank to Braamfontein",
        "Bolt ride to Vodacom World Midrand",
        "E-hailing to client site Centurion",
        "Gautrain Marlboro to Hatfield",
    ],
    "Travel - Long Distance": [
        "FlySafair JNB-CPT return flight",
        "Petrol Shell N1 highway Johannesburg to Pretoria",
        "Petrol Engen N3 Durban to Pietermaritzburg",
        "FlySafair JNB-DUR one-way",
        "Intercape bus Johannesburg to Cape Town",
        "Petrol BP N12 Johannesburg to Klerksdorp",
        "SAA JNB-PLZ return Gqeberha",
        "Car rental Avis 3 days Cape Town",
    ],
    "Accommodation": [
        "City Lodge Sandton 2 nights",
        "Protea Hotel Cape Town Waterfront 1 night",
        "Garden Court OR Tambo 1 night",
        "SunSquare Cape Town City Bowl 2 nights",
        "StayEasy Pretoria 1 night",
        "Airbnb Umhlanga 3 nights",
        "Town Lodge Bellville 1 night",
        "Premier Hotel Midrand 2 nights",
    ],
    "Meals & Entertainment": [
        "Team lunch Nando's Rosebank",
        "Client dinner Ocean Basket V&A Waterfront",
        "Working lunch Spur Sandton City",
        "Team breakfast Wimpy Centurion",
        "Lunch meeting Steers Braamfontein",
        "Coffee meeting Vida e Caffe Melrose Arch",
        "Team dinner RocoMamas Fourways",
        "Working lunch Mugg & Bean Menlyn",
    ],
    "Office Supplies": [
        "Printer cartridge HP LaserJet from Takealot",
        "USB-C hub and cables from Incredible Connection",
        "A4 paper 5 reams from PNA Sandton",
        "Whiteboard markers and erasers from Waltons",
        "Laptop stand from Takealot",
        "External SSD 1TB from Incredible Connection",
        "Stationery pack from PNA",
        "Monitor HDMI cable from Matrix Warehouse",
    ],
    "Communication": [
        "Vodacom data bundle 10GB",
        "MTN airtime top-up R200",
        "Telkom fibre monthly contribution",
        "Vodacom contract top-up",
        "MTN data bundle 5GB",
        "Cell C data package 20GB",
        "Vodacom WiFi hotspot rental",
        "MTN business data add-on",
    ],
    "Client Entertainment": [
        "Client lunch Marble restaurant Rosebank JHB",
        "Venue hire Montecasino for product demo",
        "Client dinner The Test Kitchen Cape Town",
        "Golf day with MTN executives Randpark",
        "Client meeting lunch Tashas Morningside",
        "Networking event drinks Sandton Convention Centre",
        "Client appreciation dinner DW Eleven-13",
        "Product launch catering The Venue Melrose Arch",
    ],
}

# ---------------------------------------------------------------------------
# Receipt placeholder URLs
# ---------------------------------------------------------------------------

RECEIPT_URLS = [
    "https://upload.wikimedia.org/wikipedia/commons/0/0b/ReceiptSwiss.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Receipts.jpg/220px-Receipts.jpg",
    "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=400",
    "https://images.unsplash.com/photo-1554224154-22dec7ec8818?w=400",
    "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=400",
]


# ---------------------------------------------------------------------------
# Seed data loading
# ---------------------------------------------------------------------------

def load_seed_json(filename: str) -> list[dict]:
    """Load a JSON seed-data file from config/seed-data/."""
    path = SEED_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_category_to_gl(gl_accounts: list[dict]) -> dict[str, int]:
    """Map Expense_Category -> GL row ID (1-based)."""
    mapping: dict[str, int] = {}
    for idx, gl in enumerate(gl_accounts, start=1):
        mapping[gl["Expense_Category"]] = idx
    return mapping


def build_category_esg_maps(gl_accounts: list[dict]) -> tuple[dict[str, float], dict[str, str]]:
    """Map Expense_Category -> Carbon_Factor and ESG_Category."""
    carbon: dict[str, float] = {}
    esg: dict[str, str] = {}
    for gl in gl_accounts:
        cat = gl["Expense_Category"]
        carbon[cat] = gl.get("Carbon_Factor", 0)
        esg[cat] = gl.get("ESG_Category", "None")
    return carbon, esg


# ---------------------------------------------------------------------------
# CSV writers for lookup tables
# ---------------------------------------------------------------------------

def write_departments_csv(output_dir: str, data: list[dict]) -> int:
    """Write Departments.csv with ID column."""
    path = os.path.join(output_dir, "Departments.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Department_Name", "Active"])
        for idx, d in enumerate(data, start=1):
            active = "true" if d["Active"] else "false"
            writer.writerow([idx, d["Department_Name"], active])
    return len(data)


def write_clients_csv(output_dir: str, data: list[dict]) -> int:
    """Write Clients.csv with ID column."""
    path = os.path.join(output_dir, "Clients.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Client_Name", "Active"])
        for idx, c in enumerate(data, start=1):
            active = "true" if c["Active"] else "false"
            writer.writerow([idx, c["Client_Name"], active])
    return len(data)


def write_gl_accounts_csv(output_dir: str, data: list[dict]) -> int:
    """Write GL_Accounts.csv with ID column."""
    path = os.path.join(output_dir, "GL_Accounts.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "GL_Code", "Account_Name", "Expense_Category",
            "Receipt_Required", "SARS_Provision", "Risk_Level", "Active",
            "ESG_Category", "Carbon_Factor", "GRI_Indicator",
        ])
        for idx, g in enumerate(data, start=1):
            receipt = "true" if g["Receipt_Required"] else "false"
            active = "true" if g["Active"] else "false"
            writer.writerow([
                idx,
                g["GL_Code"],
                g["Account_Name"],
                g["Expense_Category"],
                receipt,
                g["SARS_Provision"],
                g.get("Risk_Level", "Standard"),
                active,
                g.get("ESG_Category", "None"),
                g.get("Carbon_Factor", 0),
                g.get("GRI_Indicator", ""),
            ])
    return len(data)


def write_thresholds_csv(output_dir: str, data: list[dict]) -> int:
    """Write Approval_Thresholds.csv with ID column."""
    path = os.path.join(output_dir, "Approval_Thresholds.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "Tier_Name", "Max_Amount_ZAR", "Approver_Role",
            "Tier_Order", "Active", "Requires_Dual_Approval",
            "Dual_Approval_Role", "Dual_Threshold_ZAR",
        ])
        for idx, t in enumerate(data, start=1):
            active = "true" if t["Active"] else "false"
            dual = "true" if t.get("Requires_Dual_Approval") else "false"
            writer.writerow([
                idx,
                t["Tier_Name"],
                f"{t['Max_Amount_ZAR']:.2f}",
                t["Approver_Role"],
                t.get("Tier_Order", 0),
                active,
                dual,
                t.get("Dual_Approval_Role", ""),
                f"{t['Dual_Threshold_ZAR']:.2f}" if t.get("Dual_Threshold_ZAR") else "",
            ])
    return len(data)


def write_compliance_config_csv(output_dir: str, data: list[dict]) -> int:
    """Write Compliance_Config.csv with ID column."""
    path = os.path.join(output_dir, "Compliance_Config.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Config_Key", "Config_Value", "Description", "Active"])
        for idx, c in enumerate(data, start=1):
            active = "true" if c["Active"] else "false"
            writer.writerow([
                idx,
                c["Config_Key"],
                c["Config_Value"],
                c.get("Description", ""),
                active,
            ])
    return len(data)


# ---------------------------------------------------------------------------
# VAT logic
# ---------------------------------------------------------------------------

def get_vat_type(amount: float, behavior: str) -> str:
    """Determine VAT invoice type based on amount and employee behaviour."""
    if amount >= 5000:
        if behavior == "rookie" and random.random() < 0.3:
            return "Abbreviated"
        return "Full Tax Invoice (>= R5,000)"
    return random.choice(["None", "Abbreviated"])


# ---------------------------------------------------------------------------
# Helper: random expense date within last N days before a reference date
# ---------------------------------------------------------------------------

def random_expense_date(before: date, max_days_back: int = 21) -> date:
    """Return a random date within the last max_days_back days before *before*."""
    offset = random.randint(1, max_days_back)
    return before - timedelta(days=offset)


def random_weekend_date(before: date, max_days_back: int = 21) -> date:
    """Return a random Saturday or Sunday within range."""
    candidates: list[date] = []
    for d in range(1, max_days_back + 1):
        dt = before - timedelta(days=d)
        if dt.weekday() in (5, 6):
            candidates.append(dt)
    if not candidates:
        # Fallback: just pick a Saturday
        dt = before - timedelta(days=((before.weekday() + 2) % 7) or 7)
        candidates.append(dt)
    return random.choice(candidates)


def ifnull(value: str | None, fallback: str) -> str:
    """Return fallback if value is None or empty."""
    return value if value else fallback


def fmt_date(d: date) -> str:
    """Format date as ISO 8601 datetime string."""
    return datetime(d.year, d.month, d.day).strftime("%Y-%m-%d %H:%M:%S")


def fmt_datetime(dt: datetime) -> str:
    """Format datetime as ISO 8601 string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def fmt_amount(amount: float) -> str:
    """Format ZAR amount to 2 decimal places."""
    return f"{amount:.2f}"


# ---------------------------------------------------------------------------
# Claim generation
# ---------------------------------------------------------------------------

def generate_claims(
    category_to_gl: dict[str, int],
    today: date,
    gl_carbon_factors: dict[str, float] | None = None,
    gl_esg_categories: dict[str, str] | None = None,
) -> tuple[list[dict], int, int]:
    """
    Generate 175 expense claims across 5 intervals x 7 employees x 5 claims.

    Returns (claims_list, valid_count, error_count).
    """
    if gl_carbon_factors is None:
        gl_carbon_factors = {}
    if gl_esg_categories is None:
        gl_esg_categories = {}
    claims: list[dict] = []
    claim_id = 0
    error_count = 0
    base_dt = datetime(today.year, today.month, today.day, 8, 0, 0)

    for interval in range(5):
        submission_dt = base_dt + timedelta(hours=interval * 6)
        submission_date = submission_dt.date()

        for employee in EMPLOYEES:
            behavior = employee["behavior"]

            for claim_num in range(5):
                claim_id += 1
                claim_ref = f"EXP-{claim_id:04d}"

                # Defaults
                category = random.choice(employee["categories"])
                lo, hi = employee["amount_range"]
                amount = round(random.uniform(max(lo, 1), hi), 2)
                expense_dt = random_expense_date(submission_date)
                popia = "true"
                status = "Submitted"
                rejection_reason = ""
                version = 1
                description = random.choice(DESCRIPTIONS[category])
                receipt_url = random.choice(RECEIPT_URLS)

                # --- Behaviour-specific overrides ---

                if behavior == "rookie":
                    is_error = False
                    if interval == 0 and claim_num == 0:
                        # Future date
                        expense_dt = today + timedelta(days=5)
                        is_error = True
                    elif interval == 0 and claim_num == 1:
                        # POPIA not consented
                        popia = "false"
                        is_error = True
                    elif interval == 1 and claim_num == 0:
                        # Zero amount
                        amount = 0.00
                        is_error = True
                    elif interval == 1 and claim_num == 1:
                        # Expense date >90 days ago
                        expense_dt = today - timedelta(days=120)
                        is_error = True
                    elif interval == 2 and claim_num == 0:
                        # Wrong VAT for high amount
                        amount = 5500.00
                        category = "Client Entertainment"
                        description = random.choice(DESCRIPTIONS[category])
                        is_error = True
                        # VAT will be set below but we force Abbreviated
                    elif interval == 2 and claim_num == 1:
                        # Duplicate of interval 2 claim 0 -- same date and amount
                        prev = claims[-1]
                        expense_dt = datetime.strptime(
                            prev["Expense_Date"], "%Y-%m-%d %H:%M:%S"
                        ).date()
                        amount = float(prev["Amount_ZAR"])
                        category = prev["Category"]
                        description = prev["Description"]
                        is_error = True

                    if is_error:
                        error_count += 1

                    # Force wrong VAT for the specific case
                    if interval == 2 and claim_num == 0:
                        vat_type = "Abbreviated"
                    else:
                        vat_type = get_vat_type(amount, behavior)

                elif behavior == "suspicious":
                    # Suspicious patterns
                    if interval == 0 and claim_num < 3:
                        # 3 claims on same date, all Client Entertainment
                        category = "Client Entertainment"
                        expense_dt = random_weekend_date(submission_date)
                        # Use same date for all 3
                        if claim_num == 0:
                            _suspicious_date = expense_dt
                        else:
                            expense_dt = _suspicious_date  # noqa: F821
                        description = "Client meeting - " + random.choice(
                            DESCRIPTIONS[category]
                        )
                    elif interval == 0 and claim_num >= 3:
                        category = random.choice(employee["categories"])
                        description = "Client meeting - " + random.choice(
                            DESCRIPTIONS[category]
                        )

                    # Round amounts
                    round_amounts = [500.00, 1000.00, 2000.00, 4999.00, 3000.00]
                    if interval == 3 and claim_num == 0:
                        amount = 9999.00
                    else:
                        amount = random.choice(round_amounts)

                    # Weekend dates for Client Entertainment
                    if category == "Client Entertainment" and interval != 0:
                        expense_dt = random_weekend_date(submission_date)

                    # Prepend vague prefix if not already done
                    if not description.startswith("Client meeting"):
                        description = "Client meeting - " + description

                    vat_type = get_vat_type(amount, behavior)

                elif behavior == "resubmitter":
                    if interval == 2 and claim_num == 0:
                        # Will be rejected
                        status = "Rejected"
                        rejection_reason = "Wrong category selected for expense type"
                    elif interval == 2 and claim_num == 1:
                        # Resubmission of previous
                        prev = claims[-1]
                        category = prev["Category"]
                        amount = float(prev["Amount_ZAR"])
                        expense_dt = datetime.strptime(
                            prev["Expense_Date"], "%Y-%m-%d %H:%M:%S"
                        ).date()
                        description = prev["Description"] + " (corrected)"
                        version = 2
                        status = "Resubmitted"
                        rejection_reason = ""
                    elif interval == 3 and claim_num == 0:
                        # Another rejection
                        status = "Rejected"
                        rejection_reason = "Amount appears incorrect - please verify"
                    elif interval == 3 and claim_num == 1:
                        # Resubmission
                        prev = claims[-1]
                        category = prev["Category"]
                        amount = round(float(prev["Amount_ZAR"]) * 0.95, 2)
                        expense_dt = datetime.strptime(
                            prev["Expense_Date"], "%Y-%m-%d %H:%M:%S"
                        ).date()
                        description = prev["Description"] + " (corrected amount)"
                        version = 2
                        status = "Resubmitted"
                        rejection_reason = ""

                    vat_type = get_vat_type(amount, behavior)

                elif behavior == "line_manager":
                    vat_type = get_vat_type(amount, behavior)

                elif behavior == "high_value":
                    # Always above dual threshold (R5,000)
                    amount = round(random.uniform(5001, 9500), 2)
                    # One Key 2 dispute scenario
                    if interval == 2 and claim_num == 0:
                        status = "Key 2 Dispute"
                        rejection_reason = "Amount seems excessive for this category"
                    elif interval == 2 and claim_num == 1:
                        # Resubmission after HoD agrees with Key 2 rejection
                        prev = claims[-1]
                        category = prev["Category"]
                        amount = round(float(prev["Amount_ZAR"]) * 0.8, 2)
                        expense_dt = datetime.strptime(
                            prev["Expense_Date"], "%Y-%m-%d %H:%M:%S"
                        ).date()
                        description = prev["Description"] + " (revised amount)"
                        version = 2
                        status = "Resubmitted"
                        rejection_reason = ""
                    vat_type = get_vat_type(amount, behavior)

                else:
                    # normal
                    vat_type = get_vat_type(amount, behavior)

                # GL mapping
                gl_code_id = category_to_gl.get(category, 1)

                # Retention expiry: submission + 5 years (SARS S29)
                retention_expiry = date(
                    submission_date.year + 5,
                    submission_date.month,
                    submission_date.day,
                )

                claim = {
                    "ID": claim_id,
                    "Employee_Name": employee["name"],
                    "Email": employee["email"],
                    "Submission_Date": fmt_datetime(submission_dt),
                    "Claim_Reference": claim_ref,
                    "Department_ID": employee["department_id"],
                    "Client_ID": random.choice(employee["client_ids"]),
                    "Expense_Date": fmt_date(expense_dt),
                    "Category": category,
                    "Amount_ZAR": fmt_amount(amount),
                    "Description": description,
                    "VAT_Invoice_Type": vat_type,
                    "POPIA_Consent": popia,
                    "Status": status,
                    "Rejection_Reason": rejection_reason,
                    "Version": version,
                    "Retention_Expiry_Date": fmt_date(retention_expiry),
                    "GL_Code_ID": gl_code_id,
                    "Supporting_Documents": receipt_url,
                    "Requires_Dual_Approval": "true" if (amount > 5000 and status not in ("Rejected", "Resubmitted") and behavior != "rookie") else "false",
                    "Key_1_Approver": "Head of Department" if (amount > 5000 and status not in ("Rejected", "Resubmitted") and behavior != "rookie") else "",
                    "Key_1_Timestamp": fmt_datetime(submission_dt + timedelta(days=2)) if (amount > 5000 and status not in ("Rejected", "Resubmitted") and behavior != "rookie") else "",
                    "Key_2_Approver": "Finance Director" if (amount > 5000 and status == "Submitted" and behavior not in ("rookie", "high_value")) else "",
                    "Key_2_Timestamp": fmt_datetime(submission_dt + timedelta(days=3)) if (amount > 5000 and status == "Submitted" and behavior not in ("rookie", "high_value")) else "",
                    "Estimated_Carbon_KG": fmt_amount(amount * gl_carbon_factors.get(category, 0)),
                    "ESG_Category": gl_esg_categories.get(category, "None"),
                }
                claims.append(claim)

    valid_count = len(claims) - error_count
    return claims, valid_count, error_count


def write_claims_csv(output_dir: str, claims: list[dict]) -> int:
    """Write Expense_Claims.csv."""
    columns = [
        "ID", "Employee_Name", "Email", "Submission_Date", "Claim_Reference",
        "Department_ID", "Client_ID", "Expense_Date", "Category", "Amount_ZAR",
        "Description", "VAT_Invoice_Type", "POPIA_Consent", "Status",
        "Rejection_Reason", "Version", "Retention_Expiry_Date", "GL_Code_ID",
        "Supporting_Documents", "Requires_Dual_Approval",
        "Key_1_Approver", "Key_1_Timestamp", "Key_2_Approver", "Key_2_Timestamp",
        "Estimated_Carbon_KG", "ESG_Category",
    ]
    path = os.path.join(output_dir, "Expense_Claims.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for claim in claims:
            writer.writerow(claim)
    return len(claims)


# ---------------------------------------------------------------------------
# Approval history generation
# ---------------------------------------------------------------------------

def generate_approval_history(
    claims: list[dict],
    today: date,
) -> list[dict]:
    """
    Generate approval history records for all claims.

    Includes SLA breach injection for 2 early-interval claims.
    """
    history: list[dict] = []
    history_id = 0

    # Collect interval-0 normal employee claims for SLA breach injection
    sla_breach_candidates: list[tuple[dict, dict]] = []

    for claim in claims:
        claim_id = claim["ID"]
        status = claim["Status"]
        submission_dt = datetime.strptime(claim["Submission_Date"], "%Y-%m-%d %H:%M:%S")
        amount = float(claim["Amount_ZAR"])

        # Find the employee for this claim
        employee = None
        for emp in EMPLOYEES:
            if emp["name"] == claim["Employee_Name"]:
                employee = emp
                break

        if employee is None:
            continue

        behavior = employee["behavior"]

        if status == "Rejected":
            # Submitted then rejected
            history_id += 1
            history.append({
                "ID": history_id,
                "Claim_ID": claim_id,
                "Action_Type": "Submitted",
                "Actor": employee["name"],
                "Action_Timestamp": fmt_datetime(submission_dt),
                "Comments": "Initial submission",
            })
            history_id += 1
            history.append({
                "ID": history_id,
                "Claim_ID": claim_id,
                "Action_Type": "Rejected",
                "Actor": "Line Manager",
                "Action_Timestamp": fmt_datetime(
                    submission_dt + timedelta(days=1)
                ),
                "Comments": "Insufficient documentation / wrong category",
            })

        elif status == "Key 2 Dispute":
            # Two-Key dispute: Submitted -> LM escalate -> Key 1 approve -> Key 2 reject
            history_id += 1
            history.append({
                "ID": history_id,
                "Claim_ID": claim_id,
                "Action_Type": "Submitted",
                "Actor": employee["name"],
                "Action_Timestamp": fmt_datetime(submission_dt),
                "Comments": "Initial submission",
            })
            history_id += 1
            history.append({
                "ID": history_id,
                "Claim_ID": claim_id,
                "Action_Type": "Approved (LM)",
                "Actor": "Line Manager",
                "Action_Timestamp": fmt_datetime(
                    submission_dt + timedelta(days=1)
                ),
                "Comments": "Escalated to HoD - amount exceeds R999.99",
            })
            history_id += 1
            history.append({
                "ID": history_id,
                "Claim_ID": claim_id,
                "Action_Type": "Approved (Key 1)",
                "Actor": "Head of Department",
                "Action_Timestamp": fmt_datetime(
                    submission_dt + timedelta(days=2)
                ),
                "Comments": "HoD approved as Key 1. Routed to Finance Director.",
            })
            history_id += 1
            history.append({
                "ID": history_id,
                "Claim_ID": claim_id,
                "Action_Type": "Rejected (Key 2)",
                "Actor": "Finance Director",
                "Action_Timestamp": fmt_datetime(
                    submission_dt + timedelta(days=3)
                ),
                "Comments": "Key 2 disputes Key 1 approval. Reason: "
                + ifnull(claim.get("Rejection_Reason"), "Amount seems excessive"),
            })

        elif status == "Resubmitted":
            # Resubmitted then approved
            history_id += 1
            history.append({
                "ID": history_id,
                "Claim_ID": claim_id,
                "Action_Type": "Resubmitted",
                "Actor": employee["name"],
                "Action_Timestamp": fmt_datetime(submission_dt),
                "Comments": "Corrected and resubmitted",
            })
            if amount <= 999.99:
                history_id += 1
                history.append({
                    "ID": history_id,
                    "Claim_ID": claim_id,
                    "Action_Type": "Approved (LM)",
                    "Actor": "Line Manager",
                    "Action_Timestamp": fmt_datetime(
                        submission_dt + timedelta(days=1)
                    ),
                    "Comments": "Approved after resubmission",
                })
            else:
                history_id += 1
                history.append({
                    "ID": history_id,
                    "Claim_ID": claim_id,
                    "Action_Type": "Approved (LM)",
                    "Actor": "Line Manager",
                    "Action_Timestamp": fmt_datetime(
                        submission_dt + timedelta(days=1)
                    ),
                    "Comments": "Escalated to HoD - amount exceeds R999.99",
                })
                history_id += 1
                history.append({
                    "ID": history_id,
                    "Claim_ID": claim_id,
                    "Action_Type": "Approved (HoD)",
                    "Actor": "Head of Department",
                    "Action_Timestamp": fmt_datetime(
                        submission_dt + timedelta(days=2)
                    ),
                    "Comments": "Final approval",
                })

        elif behavior == "line_manager":
            # Self-approval bypass -> routed to HoD
            history_id += 1
            history.append({
                "ID": history_id,
                "Claim_ID": claim_id,
                "Action_Type": "Submitted (Self-approval bypass)",
                "Actor": employee["name"],
                "Action_Timestamp": fmt_datetime(submission_dt),
                "Comments": "Line Manager self-submission — routed to HoD",
            })
            approval_delay = random.randint(1, 2)
            history_id += 1
            history.append({
                "ID": history_id,
                "Claim_ID": claim_id,
                "Action_Type": "Approved (HoD)",
                "Actor": "Head of Department",
                "Action_Timestamp": fmt_datetime(
                    submission_dt + timedelta(days=approval_delay)
                ),
                "Comments": "Approved",
            })

        else:
            # Normal / rookie / suspicious submitted claims
            history_id += 1
            history.append({
                "ID": history_id,
                "Claim_ID": claim_id,
                "Action_Type": "Submitted",
                "Actor": employee["name"],
                "Action_Timestamp": fmt_datetime(submission_dt),
                "Comments": "Initial submission",
            })

            if amount <= 999.99:
                history_id += 1
                history.append({
                    "ID": history_id,
                    "Claim_ID": claim_id,
                    "Action_Type": "Approved (LM)",
                    "Actor": "Line Manager",
                    "Action_Timestamp": fmt_datetime(
                        submission_dt + timedelta(days=1)
                    ),
                    "Comments": "Approved within threshold",
                })
            else:
                history_id += 1
                history.append({
                    "ID": history_id,
                    "Claim_ID": claim_id,
                    "Action_Type": "Approved (LM)",
                    "Actor": "Line Manager",
                    "Action_Timestamp": fmt_datetime(
                        submission_dt + timedelta(days=1)
                    ),
                    "Comments": "Escalated to HoD - amount exceeds R999.99",
                })

                if amount > 5000:
                    # Two-Key flow: HoD = Key 1, Finance Director = Key 2
                    history_id += 1
                    history.append({
                        "ID": history_id,
                        "Claim_ID": claim_id,
                        "Action_Type": "Approved (Key 1)",
                        "Actor": "Head of Department",
                        "Action_Timestamp": fmt_datetime(
                            submission_dt + timedelta(days=2)
                        ),
                        "Comments": "HoD approved as Key 1. Amount R"
                        + fmt_amount(amount)
                        + " exceeds dual threshold. Routed to Key 2.",
                    })
                    history_id += 1
                    history.append({
                        "ID": history_id,
                        "Claim_ID": claim_id,
                        "Action_Type": "Approved (Key 2)",
                        "Actor": "Finance Director",
                        "Action_Timestamp": fmt_datetime(
                            submission_dt + timedelta(days=3)
                        ),
                        "Comments": "Finance Director final approval (Key 2). "
                        "Two-Key authorization complete.",
                    })
                else:
                    history_id += 1
                    history.append({
                        "ID": history_id,
                        "Claim_ID": claim_id,
                        "Action_Type": "Approved (HoD)",
                        "Actor": "Head of Department",
                        "Action_Timestamp": fmt_datetime(
                            submission_dt + timedelta(days=2)
                        ),
                        "Comments": "Final approval",
                    })

            # Track candidates for SLA breach (interval 0, normal employees)
            if behavior in ("normal",):
                # Interval 0 claims have submission_dt at base time (hour 8)
                if submission_dt.hour == 8:
                    sla_breach_candidates.append((claim, employee))

    # Inject SLA breach records for 2 random interval-0 claims
    if len(sla_breach_candidates) >= 2:
        breach_picks = random.sample(sla_breach_candidates, 2)
        for claim, employee in breach_picks:
            claim_id = claim["ID"]
            submission_dt = datetime.strptime(
                claim["Submission_Date"], "%Y-%m-%d %H:%M:%S"
            )

            # Warning on day 2
            history_id += 1
            history.append({
                "ID": history_id,
                "Claim_ID": claim_id,
                "Action_Type": "Warning",
                "Actor": "SYSTEM",
                "Action_Timestamp": fmt_datetime(
                    submission_dt + timedelta(days=2)
                ),
                "Comments": "Approval SLA warning - 48 hours without action",
            })

            # Escalated on day 3
            history_id += 1
            history.append({
                "ID": history_id,
                "Claim_ID": claim_id,
                "Action_Type": "Escalated (SLA Breach)",
                "Actor": "SYSTEM",
                "Action_Timestamp": fmt_datetime(
                    submission_dt + timedelta(days=3)
                ),
                "Comments": "SLA breached - auto-escalated to Head of Department",
            })

            # HoD approval on day 3
            history_id += 1
            history.append({
                "ID": history_id,
                "Claim_ID": claim_id,
                "Action_Type": "Approved (HoD)",
                "Actor": "Head of Department",
                "Action_Timestamp": fmt_datetime(
                    submission_dt + timedelta(days=3, hours=4)
                ),
                "Comments": "Approved after SLA escalation",
            })

    return history


def write_history_csv(output_dir: str, history: list[dict]) -> int:
    """Write Approval_History.csv."""
    columns = [
        "ID", "Claim_ID", "Action_Type", "Actor",
        "Action_Timestamp", "Comments",
    ]
    path = os.path.join(output_dir, "Approval_History.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for record in history:
            writer.writerow(record)
    return len(history)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate mock data for Expense Reimbursement Manager stress-testing",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).parent.parent / "exports" / "csv"),
        help="Output directory for CSV files (default: exports/csv/)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic output (default: 42)",
    )
    args = parser.parse_args()

    # Seed RNG
    random.seed(args.seed)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    today = date.today()

    # --- Load seed data ---
    departments = load_seed_json("departments.json")
    clients = load_seed_json("clients.json")
    gl_accounts = load_seed_json("gl_accounts.json")
    thresholds = load_seed_json("approval_thresholds.json")

    # --- Write lookup CSVs ---
    dept_count = write_departments_csv(args.output_dir, departments)
    client_count = write_clients_csv(args.output_dir, clients)
    gl_count = write_gl_accounts_csv(args.output_dir, gl_accounts)
    thresh_count = write_thresholds_csv(args.output_dir, thresholds)

    # --- Build category -> GL mapping ---
    category_to_gl = build_category_to_gl(gl_accounts)
    gl_carbon_factors, gl_esg_categories = build_category_esg_maps(gl_accounts)

    # --- Write compliance config CSV ---
    cc_path = SEED_DIR / "compliance_config.json"
    if cc_path.exists():
        cc_data = load_seed_json("compliance_config.json")
        cc_count = write_compliance_config_csv(args.output_dir, cc_data)
    else:
        cc_count = 0

    # --- Generate expense claims ---
    claims, valid_count, error_count = generate_claims(
        category_to_gl, today, gl_carbon_factors, gl_esg_categories,
    )
    claims_count = write_claims_csv(args.output_dir, claims)

    # --- Generate approval history ---
    history = generate_approval_history(claims, today)
    history_count = write_history_csv(args.output_dir, history)

    # --- Summary ---
    print("Generated mock data:")
    print(f"  Departments: {dept_count} records")
    print(f"  Clients: {client_count} records")
    print(f"  GL_Accounts: {gl_count} records")
    print(f"  Approval_Thresholds: {thresh_count} records")
    print(f"  Compliance_Config: {cc_count} records")
    print(
        f"  Expense_Claims: {claims_count} records "
        f"({valid_count} valid, {error_count} with errors)"
    )
    print(f"  Approval_History: {history_count} records")
    print(f"  Output: {os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()
