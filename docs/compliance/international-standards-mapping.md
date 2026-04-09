# International Standards Mapping

Maps international compliance and sustainability standards to ERM system controls.

## Standards Alignment Matrix

| Standard | Requirement | ERM System Control | Status |
|----------|------------|--------------------|--------|
| **ISSB IFRS S1** | General sustainability disclosures | GL accounts tagged with ESG_Category; Compliance_Config org-type flags | Implemented |
| **ISSB IFRS S2** | Climate-related financial disclosures | Carbon_Factor on GL accounts; Estimated_Carbon_KG on approved claims (Scope 3 Category 6) | Implemented |
| **GRI 205** | Anti-corruption | ISO 37001 Risk_Level on GL accounts; High-risk categories (Meals & Entertainment, Client Entertainment) flagged | Implemented |
| **GRI 301** | Materials | Office Supplies tagged as ESG_Category "Waste" with GRI 301-1 indicator | Implemented |
| **GRI 302** | Energy | Accommodation and Communication tagged as ESG_Category "Energy" with GRI 302-1 indicator | Implemented |
| **GRI 305** | Emissions (Scope 3) | Travel categories tagged with DEFRA-adapted emission factors; Estimated_Carbon_KG calculated on approval | Implemented |
| **OECD Guidelines** | Responsible business conduct | Approval audit trail; segregation of duties (Two-Key); configurable governance flags | Partial (expense scope) |
| **ISO 26000** | Social responsibility | ESG_Category "Social" on entertainment/meals categories; governance controls | Partial (expense scope) |
| **ISO 37000** | Governance of organisations | Cross-references King IV mapping (P1, P7, P11, P12, P13, P15); Two-Key authorization | Implemented (via King IV) |
| **ISO 37001** | Anti-bribery management | Risk_Level field on GL accounts (Standard/High); enhanced scrutiny on High-risk categories | Implemented |
| **ISSA 5000** | Sustainability assurance | Complete audit trail in Approval_History; ESG metadata on claims; full traceability | Implemented |

## South African Regulatory Alignment

| Regulation | Requirement | ERM System Control | Status |
|-----------|------------|--------------------|--------|
| **King IV P1** | Ethical leadership | Self-approval prevention; LM submitters bypass their own tier | Implemented |
| **King IV P7** | Delegation of authority | Two-tier threshold approval + Two-Key Authorization | Implemented |
| **King IV P11** | Risk management | Risk-based routing; ISO 37001 Risk_Level classification | Implemented |
| **King IV P12** | Technology governance | Automated workflows; configurable thresholds; audit logging | Implemented |
| **King IV P13** | Compliance | SARS S11(a) validation; VAT invoice type enforcement; POPIA consent | Implemented |
| **King IV P15** | Combined assurance | Approval_History audit trail with system actor attribution | Implemented |
| **Companies Act s72** | Social and ethics committee | Compliance_Config ESG_REPORTING flag; ESG categorisation on expenses | Implemented |
| **Companies Act s76** | Director duty of care | Two-Key approval with Key_1/Key_2 approver accountability; audit trail | Implemented |
| **SARS S11(a)** | Deductible expenses | Mandatory receipts; business purpose descriptions; GL code mapping | Implemented |
| **SARS VAT** | Invoice thresholds | VAT_Invoice_Type field (None/Abbreviated/Full Tax Invoice >= R5,000) | Implemented |
| **SARS S29** | 5-year record retention | Retention_Expiry_Date auto-calculated (submission + 5 years) | Implemented |
| **POPIA** | Personal data protection | POPIA_Consent mandatory checkbox; data minimisation in audit records | Implemented |
| **COSO** | Internal control framework | Segregation of duties; configurable thresholds; approval hierarchy | Implemented |

## Conditional Compliance (Org-Type Dependent)

These standards apply based on the `Compliance_Config.ORG_TYPE` setting:

| Standard | Applies To | Config Key | Default |
|----------|-----------|------------|---------|
| **JSE Listings Requirements** | JSE-listed companies | `JSE_CONTROLS_REQUIRED` | false |
| **B-BBEE Act** | All SA entities (varying levels) | `BBBEE_TRACKING` | false |
| **PFMA** | National government / SOEs | `PFMA_APPLICABLE` | false |
| **MFMA** | Local government | `PFMA_APPLICABLE` | false |

### Org-Type Configurations

| ORG_TYPE | JSE_CONTROLS | PFMA | BBBEE | ESG | CARBON |
|----------|-------------|------|-------|-----|--------|
| `PRIVATE` | false | false | optional | true | true |
| `JSE_LISTED` | true | false | true | true | true |
| `SOE` | false | true | true | true | true |
| `MULTINATIONAL` | varies | false | optional | true | true |

## Carbon Emission Factors

DEFRA-adapted estimates for South African energy mix:

| GL Code | Account | ESG Category | kg CO2e / ZAR | GRI Indicator | Basis |
|---------|---------|-------------|---------------|---------------|-------|
| 6200 | Travel - Local Transport | Travel Emissions | 0.12 | GRI 305-3 | Urban transport (Uber/Bolt/taxi) |
| 6210 | Travel - Long Distance | Travel Emissions | 0.22 | GRI 305-3 | Domestic flights + intercity road |
| 6220 | Accommodation | Energy | 0.08 | GRI 302-1 | Hotel energy consumption (SA grid) |
| 6300 | Meals & Entertainment | Social | 0.00 | GRI 205-3 | Anti-corruption focus, not energy |
| 6400 | Office Supplies | Waste | 0.02 | GRI 301-1 | Manufacturing + delivery footprint |
| 6500 | Communication | Energy | 0.01 | GRI 302-1 | Data centre energy (mobile networks) |
| 6600 | Client Entertainment | Social | 0.00 | GRI 205-3 | Anti-corruption focus, not energy |

**Note**: These are estimated factors for initial reporting. Organisations should refine factors based on their specific operations, suppliers, and the latest DEFRA/DFFE guidance.

## Data Flow: Expense to ESG Report

```
Employee submits claim
    |
    v
GL code auto-populated on approval
    |
    v
ESG_Category inherited from GL account
Carbon_Factor * Amount_ZAR = Estimated_Carbon_KG
    |
    v
Approved claims carry ESG metadata
    |
    v
Sustainability Dashboard aggregates:
  - Total Carbon (kg CO2e)
  - Spend by ESG Category
  - Carbon by expense category
    |
    v
Export for ISSB S2 / GRI 305 disclosure
```

## Assurance Readiness (ISSA 5000)

The system supports sustainability assurance engagements by providing:

1. **Traceability**: Every claim has GL code, ESG_Category, and Estimated_Carbon_KG
2. **Audit trail**: Approval_History records every state change with actor and timestamp
3. **Segregation**: Two-Key authorization ensures no single approver controls high-value spend
4. **Configurability**: Compliance_Config allows auditors to verify which standards apply
5. **Data integrity**: Validation rules prevent invalid data from entering the system
