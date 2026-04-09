# King IV Principles Mapping

## Overview

Maps King IV governance principles to specific system controls implemented in the Expense Reimbursement Manager. Includes ISO 37000 (Governance of organisations) cross-references.

## Principle Mapping

| Principle | Description | System Control | ISO 37000 Cross-Reference |
|-----------|-------------|----------------|--------------------------|
| P1 | Ethical leadership | Self-approval prevention -- LM submitters bypass their own tier. Two-Key segregation prevents single-approver high-value spend | ISO 37000 6.2: Ethical and effective leadership |
| P7 | Delegation of authority | Two-tier threshold-based approval (LM R999.99 / HoD R10,000) + Two-Key Authorization for claims > R5,000 (Finance Director as Key 2) | ISO 37000 6.5: Delegation |
| P11 | Risk management | Risk-based routing -- higher amounts escalate to senior authority. ISO 37001 Risk_Level classification on GL accounts. ESG_Category tracks sustainability risk | ISO 37000 6.9: Risk governance |
| P12 | Technology governance | Automated workflows, configurable thresholds, audit logging. Compliance_Config enables org-type-specific controls. ESG auto-population on approval | ISO 37000 6.11: Technology and information |
| P13 | Compliance | SARS S11(a) validation (receipts, 90-day window, positive amounts). POPIA consent. VAT invoice type enforcement. ESG/ISSB/GRI reporting readiness | ISO 37000 6.10: Compliance governance |
| P15 | Combined assurance | Comprehensive audit trail in Approval_History with every state change. ESG metadata (category, carbon estimate) logged with each approval | ISO 37000 6.12: Assurance |

## International Standards Alignment

The King IV mapping is complemented by alignment with:
- **ISSB IFRS S1/S2**: Sustainability and climate-related disclosures via ESG_Category and Carbon_Factor
- **GRI Standards**: Anti-corruption (GRI 205), Energy (GRI 302), Emissions (GRI 305), Materials (GRI 301)
- **ISO 37001**: Anti-bribery management via Risk_Level on GL accounts
- **ISSA 5000**: Sustainability assurance readiness via complete audit trail
- **Companies Act s72/s76**: Social and ethics committee support; director duty of care

See `docs/compliance/international-standards-mapping.md` for the full alignment matrix.

## Implementation Details

| Control | Evidence | Verified |
|---------|----------|----------|
| Self-approval prevention | LM self-submit bypasses to HoD; Key 2 same-person block | Yes |
| Threshold-based approval | Configurable via Approval_Thresholds seed data | Yes |
| Two-Key Authorization | Finance Director Key 2; dispute reconsideration flow | Yes |
| Audit trail completeness | Every status transition logged with actor, timestamp, comments | Yes |
| ESG metadata population | Approval scripts populate ESG_Category and Estimated_Carbon_KG | Yes |
| Risk classification | GL accounts carry Risk_Level (Standard/High) per ISO 37001 | Yes |
| Compliance configurability | Compliance_Config table with org-type and standard flags | Yes |
