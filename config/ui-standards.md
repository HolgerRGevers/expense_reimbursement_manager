# Zoho Creator UI Standards

Standards for user interface design, accessibility, and governance-aligned UX in Zoho Creator applications. These apply to this project and serve as a reusable reference for any Creator app built with the OmniScript methodology.

## 1. Field Descriptions (Help Text)

### Rule: Every user-facing field MUST have a description

A field without a description is a field users will misuse. Help text appears on hover/focus and eliminates support queries.

### What to include in descriptions

| Field type | Description should cover |
|-----------|------------------------|
| Input fields | Purpose + format + constraints ("Date the expense was incurred. Cannot be in the future or older than 90 days.") |
| System fields | What it does + who controls it ("Set automatically by the approval workflow.") |
| Lookup fields | What to select + fallback option ("Choose Internal for non-client expenses.") |
| Compliance fields | The regulation driving the requirement ("Required by SARS S11(a) for all claims.") |
| Config fields | How it affects system behaviour ("Claims above this amount escalate to the next tier.") |

### What to exclude

- Private/shadow fields (Department_Shadow, Client_Shadow) -- hidden from users
- Self-referential FKs (Parent_Claim_ID) -- system-internal
- Sub-fields of composite fields (prefix, suffix of Name field) -- covered by parent

### Tooling

```bash
# Descriptions are maintained in config/field-descriptions.yaml
# Apply to .ds file:
python tools/ds_editor.py add-descriptions exports/FILE.ds

# Audit coverage:
python tools/ds_editor.py audit exports/FILE.ds
```

## 2. Report Design

### Keep reports that serve a governance purpose

| Report type | Keep if | Remove if |
|------------|---------|-----------|
| Filtered list (e.g., My_Claims, Pending Approvals) | Serves a specific role/workflow | -- |
| Full list (e.g., All Expense Claims) | Primary data view with aggregates | -- |
| Kanban | Provides meaningful categorical view | Duplicates the list with no added filtering |
| Summary/dashboard | Aggregates KPIs | -- |
| Audit Trail | Compliance requirement | -- |

### Launchpad boilerplate signals

These indicate a report was auto-generated and should be reviewed:
- Name follows pattern `FormName_by_FieldName` (e.g., `expense_claims_by_category`)
- No filtering beyond the default "show all rows"
- No conditional formatting
- Same data as another report with different layout only

### Tooling

```bash
# Remove reports and all their references:
python tools/ds_editor.py remove-reports exports/FILE.ds --reports name1,name2
```

## 3. Report Menu Permissions

### Principle: least privilege on menus

| Report purpose | Allowed menus | Blocked menus |
|---------------|--------------|---------------|
| Transaction reports (expense claims) | Edit, View Record | (keep current) |
| Approval worklists | Edit, View Record | (keep current) |
| Reference data (clients, departments, thresholds) | View Record only | Edit, Duplicate, Delete, Import, Export |
| Audit trail | View Record only | Edit, Duplicate, Delete, Import, Export, Print |

### Why this matters

An employee with a report menu showing "Delete" on the approval_thresholds_Report could accidentally (or deliberately) remove a tier configuration. Reference data and audit records should be view-only in report context -- edits happen through the form with proper workflow controls.

### Tooling

```bash
# Restrict menus (removes Edit/Duplicate/Delete/Print/Import/Export):
python tools/ds_editor.py restrict-menus exports/FILE.ds --reports name1,name2
```

## 4. Conditional Formatting

### Rule: formatting must communicate governance state

Good conditional formatting:
- **Status-based colouring** on claim status fields (Approved = green, Rejected = red, Pending = amber)
- **Category-based colouring** on expense types (Entertainment = purple for risk visibility, Travel = red for high-frequency)
- **SLA indicators** on pending approvals (overdue items highlighted)

Bad conditional formatting:
- Purely decorative colours with no meaning
- Inconsistent colour schemes across reports
- Colours that conflict with status meaning (green for rejected)

### Colour conventions for this project

| State/Category | Colour | Hex |
|---------------|--------|-----|
| Approved / Pass | Teal/Green | #1bbc9b |
| Rejected / Fail | Red | #e84c3d |
| Pending / Warning | Amber/Magenta | #bd588b |
| High-risk category | Purple | #765f89 |
| Escalated | Dark teal | #107c91 |

## 5. Form Layout

### Field ordering principles

1. **Identity first**: Employee Name, Email, Claim ID (who is this?)
2. **What happened**: Expense Date, Category, Description, Amount (what was spent?)
3. **Evidence**: Supporting Documents, VAT Invoice Type (prove it)
4. **Compliance**: POPIA Consent (legal requirement)
5. **Status/tracking**: Status, GL Code, Version, Rejection Reason (system-managed)
6. **Hidden**: Shadow fields, Parent Claim ID (private, end of form)

### Field visibility by role

| Field | Employee | Line Manager | HoD | Finance |
|-------|----------|-------------|-----|---------|
| Status | Read-only | Read-only | Read-only | Read-only |
| GL Code | Hidden | Read-only | Read-only | Editable |
| Rejection Reason | Read-only | Editable | Editable | Editable |
| Amount | Editable (create) | Read-only | Read-only | Read-only |
| Shadow fields | Hidden | Hidden | Hidden | Hidden |
| Retention Expiry | Hidden | Hidden | Hidden | Visible |

## 6. Navigation Structure

### Section organisation

Organise by role/workflow, not by database table:

| Section | Purpose | Audience |
|---------|---------|----------|
| Dashboard | KPI pages, overview | All roles |
| Expense Claims | Submit, track, approve claims | Employee + Manager |
| Configuration | Thresholds, GL codes | Admin + Finance |
| Audit & Compliance | Audit trail, history | Auditor + Admin |
| Reference Data | Departments, Clients | Admin only |

### Remove from navigation

- System sections (ZC_App_Preferences, ZC_Approvals, SharedAnalytics) are auto-added by Creator and cannot be removed, but should not distract from the primary workflow sections.

## 7. Accessibility Checklist

Before deploying any Creator app:

- [ ] Every user-facing field has a description (help text)
- [ ] Descriptions explain purpose, format, AND compliance context where applicable
- [ ] Boilerplate reports removed (no duplicate views of same data)
- [ ] Reference/audit report menus restricted to view-only
- [ ] Conditional formatting uses consistent colour scheme
- [ ] Status fields are read-only for non-admin roles
- [ ] Shadow/private fields are hidden from all user-facing views
- [ ] Navigation sections are organised by workflow, not database structure
- [ ] Lookup fields have "allow new entries" removed (unless intentional)
- [ ] Form field order follows identity -> event -> evidence -> compliance -> status pattern
