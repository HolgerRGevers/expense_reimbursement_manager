# ESG Reporting Guide

How to extract ESG data from the Expense Reimbursement Manager for sustainability disclosure.

## Overview

The ERM tags every approved expense claim with ESG metadata inherited from GL account configuration. This guide explains how to extract and aggregate this data for ISSB S2 and GRI Standards disclosure.

## ESG Fields Available

### On GL Accounts (configuration)
| Field | Type | Purpose |
|-------|------|---------|
| `ESG_Category` | Picklist | Sustainability classification: Travel Emissions, Energy, Waste, Social, None |
| `Carbon_Factor` | Decimal | Estimated kg CO2e per ZAR spent (DEFRA-adapted for SA) |
| `GRI_Indicator` | Text | GRI Standards reference code |

### On Expense Claims (calculated on approval)
| Field | Type | Purpose |
|-------|------|---------|
| `Estimated_Carbon_KG` | Decimal | `Amount_ZAR * GL.Carbon_Factor` — total estimated emissions for this claim |
| `ESG_Category` | Text | Denormalized from GL account for reporting performance |

## Extraction Methods

### 1. Zoho Creator Reports

Use the Sustainability Dashboard (built-in) for real-time KPIs:
- Total Carbon (kg CO2e) for approved claims
- Spend breakdown by ESG Category
- Carbon footprint by expense category

### 2. CSV Export

Export approved claims from Zoho Creator (Report > Export):
```
Filter: status == "Approved"
Columns: Claim_Reference, Category, Amount_ZAR, ESG_Category, Estimated_Carbon_KG, Expense_Date
```

### 3. API Export

```
GET /api/v2.1/{owner}/expense-reimbursement-management/report/expense_claims_Report
?criteria=status=="Approved"
&fields=Claim_Reference,category,amount_zar,ESG_Category,Estimated_Carbon_KG,Expense_Date
```

## GRI Standards Disclosure

### GRI 305-3: Other indirect (Scope 3) GHG emissions

**Category 6: Business Travel**

Aggregate from approved claims where `ESG_Category == "Travel Emissions"`:

```
Total Business Travel Emissions (kg CO2e) = SUM(Estimated_Carbon_KG)
  WHERE status == "Approved"
  AND ESG_Category == "Travel Emissions"
```

Break down by sub-category:
- Local transport (GL 6200): `Carbon_Factor = 0.12`
- Long distance (GL 6210): `Carbon_Factor = 0.22`

### GRI 302-1: Energy consumption within the organisation

Aggregate from approved claims where `ESG_Category == "Energy"`:

```
Energy-related Spend (ZAR) = SUM(Amount_ZAR)
  WHERE status == "Approved"
  AND ESG_Category == "Energy"
```

Covers: Accommodation (GL 6220), Communication (GL 6500).

### GRI 205-3: Confirmed incidents of corruption

The system tracks high-risk expense categories (Meals & Entertainment, Client Entertainment) with `Risk_Level == "High"`. Monitor:

```
High-Risk Spend (ZAR) = SUM(Amount_ZAR)
  WHERE status == "Approved"
  AND ESG_Category == "Social"
```

Flag patterns: round amounts, weekend dates, vague descriptions.

### GRI 301-1: Materials used

Office supplies tracked with `ESG_Category == "Waste"`:

```
Office Materials Spend (ZAR) = SUM(Amount_ZAR)
  WHERE status == "Approved"
  AND ESG_Category == "Waste"
```

## ISSB IFRS S2 Disclosure

### Climate-Related Financial Disclosures

For IFRS S2 Scope 3 reporting, the ERM provides:

1. **Scope 3 Category 6 (Business Travel)**: `SUM(Estimated_Carbon_KG)` where `ESG_Category == "Travel Emissions"`
2. **Scope 3 Category 8 (Upstream leased assets)**: `SUM(Estimated_Carbon_KG)` where `ESG_Category == "Energy"` (accommodation)
3. **Total estimated emissions**: `SUM(Estimated_Carbon_KG)` across all approved claims

### Reporting Period Alignment

Filter by `Expense_Date` to align with financial reporting periods:
```
WHERE Expense_Date >= '2026-01-01' AND Expense_Date <= '2026-12-31'
```

## Limitations

1. **Estimated factors**: Carbon_Factor values are estimates based on DEFRA methodology adapted for SA. Organisations should refine based on actual supplier data.
2. **Expense scope only**: The ERM covers business expense reimbursements. Other Scope 3 categories (purchased goods, capital goods, etc.) require separate systems.
3. **No distance-based calculation**: Travel emissions use spend-based factors (ZAR), not distance-based (km). For higher accuracy, integrate with travel booking systems.
4. **Social category**: GRI 205 (anti-corruption) uses the system's Risk_Level classification, not a separate anti-bribery investigation module.

## Compliance_Config Settings

| Config Key | Description | Impact on ESG Reporting |
|-----------|-------------|------------------------|
| `ESG_REPORTING` | Enable/disable ESG categorisation | When false, ESG_Category defaults to "None" |
| `CARBON_TRACKING` | Enable/disable carbon estimation | When false, Estimated_Carbon_KG = 0 |
| `ISSB_ALIGNED` | IFRS S1/S2 readiness flag | Informational — indicates disclosure commitment |
| `GRI_ALIGNED` | GRI Standards readiness flag | Informational — indicates disclosure commitment |
