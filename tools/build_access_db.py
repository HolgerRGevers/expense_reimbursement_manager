#!/usr/bin/env python3
"""
Build a Microsoft Access database (.accdb) for Zoho Creator import.

Creates all 6 forms as tables with proper data types, relationships,
and seed data. Zoho Creator imports .accdb with table relationships
preserved, creating forms with linked lookup fields.

Usage:
    python tools/build_access_db.py                    # creates exports/ERM.accdb
    python tools/build_access_db.py --output path.accdb
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import pyodbc
except ImportError:
    print("Error: pyodbc not installed. Run: pip install pyodbc", file=sys.stderr)
    sys.exit(1)


DB_NAME = "ERM.accdb"
SEED_DIR = Path(__file__).parent.parent / "config" / "seed-data"


def get_connection_string(db_path: str) -> str:
    """Build ODBC connection string for Access."""
    return (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={db_path};"
    )


def create_database(db_path: str) -> None:
    """Create a new empty .accdb file."""
    # pyodbc can't create Access files directly -- use ADOX via COM or
    # the catalog approach. Simplest: create via DAO/ADOX through win32com
    # or just use the driver with CREATE_DB flag.

    # Remove existing file
    if os.path.exists(db_path):
        os.remove(db_path)

    # Create using win32com (most reliable on Windows)
    try:
        import win32com.client
        engine = win32com.client.Dispatch("DAO.DBEngine.120")
        db = engine.CreateDatabase(
            os.path.abspath(db_path),
            ";LANGID=0x0409;CP=1252;COUNTRY=0",
            64,  # dbVersion120 for .accdb
        )
        db.Close()
        print(f"Created: {db_path}")
    except ImportError:
        # Fallback: use catalog
        try:
            import win32com.client
        except ImportError:
            pass

        # Alternative: use ADOX
        try:
            import win32com.client
            cat = win32com.client.Dispatch("ADOX.Catalog")
            conn_str = (
                "Provider=Microsoft.ACE.OLEDB.12.0;"
                f"Data Source={os.path.abspath(db_path)};"
            )
            cat.Create(conn_str)
            cat.ActiveConnection.Close()
            print(f"Created: {db_path}")
        except Exception as e:
            print(f"Error creating database: {e}", file=sys.stderr)
            print("Trying alternative method...", file=sys.stderr)
            # Last resort: copy an empty .accdb template
            _create_empty_accdb(db_path)


def _create_empty_accdb(db_path: str) -> None:
    """Create a minimal empty .accdb file using raw bytes."""
    # An .accdb is a Jet/ACE database. We can't create one from scratch
    # without COM. Let's try the pypyodbc approach.
    print("UNCERTAIN: Cannot create .accdb without COM/DAO.", file=sys.stderr)
    print("Please install pywin32: pip install pywin32", file=sys.stderr)
    sys.exit(1)


def create_tables(conn: pyodbc.Connection) -> None:
    """Create all 6 tables with proper types."""
    cur = conn.cursor()

    # Departments (lookup)
    cur.execute("""
        CREATE TABLE Departments (
            ID AUTOINCREMENT PRIMARY KEY,
            Department_Name TEXT(100) NOT NULL,
            Active BIT
        )
    """)

    # Clients (lookup)
    cur.execute("""
        CREATE TABLE Clients (
            ID AUTOINCREMENT PRIMARY KEY,
            Client_Name TEXT(100) NOT NULL,
            Active BIT
        )
    """)

    # GL_Accounts (lookup)
    cur.execute("""
        CREATE TABLE GL_Accounts (
            ID AUTOINCREMENT PRIMARY KEY,
            GL_Code TEXT(20) NOT NULL,
            Account_Name TEXT(200) NOT NULL,
            Expense_Category TEXT(100),
            Receipt_Required BIT,
            SARS_Provision TEXT(100),
            Risk_Level TEXT(20),
            Active BIT,
            ESG_Category TEXT(50),
            Carbon_Factor DOUBLE,
            GRI_Indicator TEXT(50)
        )
    """)

    # Approval_Thresholds (config)
    cur.execute("""
        CREATE TABLE Approval_Thresholds (
            ID AUTOINCREMENT PRIMARY KEY,
            Tier_Name TEXT(100) NOT NULL,
            Max_Amount_ZAR CURRENCY,
            Approver_Role TEXT(100),
            Tier_Order INTEGER,
            Active BIT
        )
    """)

    # Expense_Claims (transaction) -- no FK constraints in CREATE,
    # Access relationships are added separately via DAO/ADOX
    cur.execute("""
        CREATE TABLE Expense_Claims (
            ID AUTOINCREMENT PRIMARY KEY,
            Employee_Name TEXT(200),
            Email TEXT(200),
            Submission_Date DATETIME,
            Claim_Reference TEXT(20),
            Department_ID LONG,
            Client_ID LONG,
            Expense_Date DATETIME,
            Category TEXT(100),
            Amount_ZAR CURRENCY,
            Description MEMO,
            VAT_Invoice_Type TEXT(100),
            POPIA_Consent BIT,
            Status TEXT(50),
            Rejection_Reason MEMO,
            Version INTEGER,
            Retention_Expiry_Date DATETIME,
            GL_Code_ID LONG,
            Requires_Dual_Approval BIT,
            Key_1_Approver TEXT(200),
            Key_1_Timestamp DATETIME,
            Key_2_Approver TEXT(200),
            Key_2_Timestamp DATETIME,
            Estimated_Carbon_KG DOUBLE,
            ESG_Category TEXT(50)
        )
    """)

    # Approval_History (audit)
    cur.execute("""
        CREATE TABLE Approval_History (
            ID AUTOINCREMENT PRIMARY KEY,
            Claim_ID LONG,
            Action_Type TEXT(100),
            Actor TEXT(200),
            Action_Timestamp DATETIME,
            Comments MEMO
        )
    """)

    # Compliance_Config (config)
    cur.execute("""
        CREATE TABLE Compliance_Config (
            ID AUTOINCREMENT PRIMARY KEY,
            Config_Key TEXT(100) NOT NULL,
            Config_Value TEXT(200),
            Description TEXT(500),
            Active BIT
        )
    """)

    conn.commit()
    print("Created 7 tables")


def create_relationships(db_path: str) -> None:
    """Create table relationships using DAO COM objects."""
    import win32com.client
    engine = win32com.client.Dispatch("DAO.DBEngine.120")
    db = engine.OpenDatabase(os.path.abspath(db_path))

    relationships = [
        ("FK_EC_Dept", "Departments", "Expense_Claims", "ID", "Department_ID"),
        ("FK_EC_Client", "Clients", "Expense_Claims", "ID", "Client_ID"),
        ("FK_EC_GL", "GL_Accounts", "Expense_Claims", "ID", "GL_Code_ID"),
        ("FK_AH_Claim", "Expense_Claims", "Approval_History", "ID", "Claim_ID"),
    ]

    for name, parent_table, child_table, parent_field, child_field in relationships:
        try:
            rel = db.CreateRelation(name, parent_table, child_table, 0)
            field = rel.CreateField(parent_field)
            field.ForeignName = child_field
            rel.Fields.Append(field)
            db.Relations.Append(rel)
            print(f"  Relationship: {parent_table}.{parent_field} -> {child_table}.{child_field}")
        except Exception as e:
            print(f"  WARNING: Could not create {name}: {e}")

    db.Close()
    print("Relationships created")


def populate_seed_data(conn: pyodbc.Connection) -> None:
    """Insert seed data from config/seed-data/ JSON files."""
    cur = conn.cursor()

    # Departments
    with open(SEED_DIR / "departments.json", encoding="utf-8") as f:
        departments = json.load(f)
    for d in departments:
        cur.execute(
            "INSERT INTO Departments (Department_Name, Active) VALUES (?, ?)",
            d["Department_Name"], d["Active"],
        )
    print(f"  Departments: {len(departments)} records")

    # Clients
    with open(SEED_DIR / "clients.json", encoding="utf-8") as f:
        clients = json.load(f)
    for c in clients:
        cur.execute(
            "INSERT INTO Clients (Client_Name, Active) VALUES (?, ?)",
            c["Client_Name"], c["Active"],
        )
    print(f"  Clients: {len(clients)} records")

    # GL Accounts
    with open(SEED_DIR / "gl_accounts.json", encoding="utf-8") as f:
        gl_accounts = json.load(f)
    for g in gl_accounts:
        cur.execute(
            "INSERT INTO GL_Accounts (GL_Code, Account_Name, Expense_Category, "
            "Receipt_Required, SARS_Provision, Risk_Level, Active, "
            "ESG_Category, Carbon_Factor, GRI_Indicator) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            g["GL_Code"], g["Account_Name"], g["Expense_Category"],
            g["Receipt_Required"], g["SARS_Provision"],
            g.get("Risk_Level", "Standard"), g["Active"],
            g.get("ESG_Category", "None"), g.get("Carbon_Factor", 0),
            g.get("GRI_Indicator", ""),
        )
    print(f"  GL_Accounts: {len(gl_accounts)} records")

    # Approval Thresholds
    with open(SEED_DIR / "approval_thresholds.json", encoding="utf-8") as f:
        thresholds = json.load(f)
    for t in thresholds:
        cur.execute(
            "INSERT INTO Approval_Thresholds (Tier_Name, Max_Amount_ZAR, "
            "Approver_Role, Tier_Order, Active) VALUES (?, ?, ?, ?, ?)",
            t["Tier_Name"], t["Max_Amount_ZAR"], t["Approver_Role"],
            t.get("Tier_Order", 0), t["Active"],
        )
    print(f"  Approval_Thresholds: {len(thresholds)} records")

    # Compliance Config
    cc_path = SEED_DIR / "compliance_config.json"
    if cc_path.exists():
        with open(cc_path, encoding="utf-8") as f:
            configs = json.load(f)
        for c in configs:
            cur.execute(
                "INSERT INTO Compliance_Config (Config_Key, Config_Value, "
                "Description, Active) VALUES (?, ?, ?, ?)",
                c["Config_Key"], c["Config_Value"],
                c.get("Description", ""), c["Active"],
            )
        print(f"  Compliance_Config: {len(configs)} records")

    conn.commit()
    print("Seed data loaded")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Access database for Zoho Creator import",
    )
    parser.add_argument(
        "--output", "-o",
        default=str(Path(__file__).parent.parent / "exports" / DB_NAME),
        help="Output .accdb file path",
    )
    args = parser.parse_args()

    db_path = os.path.abspath(args.output)

    # Step 1: Create empty database
    create_database(db_path)

    # Step 2: Connect and create tables
    conn_str = get_connection_string(db_path)
    conn = pyodbc.connect(conn_str)
    try:
        create_tables(conn)
        populate_seed_data(conn)
    finally:
        conn.close()

    # Step 3: Add relationships via DAO
    create_relationships(db_path)

    # Summary
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()
    tables = [row.table_name for row in cur.tables(tableType="TABLE")]
    print(f"\nDatabase: {db_path}")
    print(f"Tables: {len(tables)}")
    for t in tables:
        count = cur.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"  {t}: {count} records")
    conn.close()


if __name__ == "__main__":
    main()
