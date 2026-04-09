# Companies Act Alignment

Mapping of the South African Companies Act No. 71 of 2008 to ERM system controls.

## Section 72: Social and Ethics Committee

**Requirement**: Certain companies must establish a social and ethics committee to monitor the company's activities with respect to social and economic development, good corporate citizenship, the environment, and labour.

**ERM Alignment**:

| s72 Requirement | System Control |
|----------------|---------------|
| Monitor environmental impact | ESG_Category and Estimated_Carbon_KG on approved claims provide environmental spend data |
| Good corporate citizenship | Compliance_Config tracks org-type and applicable standards |
| Anti-corruption | ISO 37001 Risk_Level on GL accounts; high-risk categories flagged |
| Consumer relationships | Client Entertainment tracking with enhanced scrutiny |

**Applicability**: Companies meeting the threshold in Regulation 43 (public companies, SOEs, or companies scoring above 500 public interest points).

**Config**: `Compliance_Config.ORG_TYPE` determines which s72 reporting requirements apply.

## Section 76: Standards of Directors' Conduct

**Requirement**: Directors must act in good faith, for a proper purpose, with the degree of care, skill, and diligence that may reasonably be expected of a person carrying out the same functions.

**ERM Alignment**:

| s76 Principle | System Control |
|--------------|---------------|
| **Duty of care** | Two-Key Authorization: high-value claims require two independent approvers (Key 1 + Key 2) |
| **Good faith** | Self-approval prevention: managers cannot approve their own claims |
| **Proper purpose** | Business purpose mandatory in claim description (SARS S11(a) alignment) |
| **Reasonable diligence** | SLA enforcement: 2-day reminder, 3-day auto-escalation for pending approvals |
| **Financial responsibility** | Configurable approval thresholds; GL code auto-assignment; audit trail |

**Audit Evidence**: Every approval decision is recorded in Approval_History with:
- Actor (who approved/rejected)
- Timestamp (when)
- Comments (why — including GL code, ESG category, carbon estimate)
- Action type (what action was taken)

## Section 77: Liability of Directors

**Mitigation**: The ERM's governance controls demonstrate that the organisation has implemented reasonable internal controls over expense management:

1. **Segregation of duties**: No single person can submit and approve the same claim
2. **Threshold-based routing**: Amounts above configurable limits require senior approval
3. **Two-Key Authorization**: High-value claims require dual-approval (King IV P7 + COSO)
4. **Automated audit trail**: Every state change logged with immutable timestamps
5. **Configurable compliance**: Compliance_Config adapts controls to the organisation's regulatory environment

## Regulation 43: Social and Ethics Committee

For companies that must establish a social and ethics committee, the ERM provides:

| Reg 43 Area | ERM Data Available |
|-------------|-------------------|
| Social and economic development | Expense spend by department, client, category |
| Good corporate citizenship | ESG-tagged expense data; carbon footprint estimates |
| Environment, health, safety | Estimated_Carbon_KG aggregates for Scope 3 reporting |
| Consumer relationships | Client Entertainment spend with Risk_Level flags |
| Labour and employment | Employee expense patterns by department |

## Integration with King IV

The Companies Act s72/s76 alignment complements the existing King IV mapping:

| King IV | Companies Act | Combined Control |
|---------|--------------|-----------------|
| P1 (Ethical leadership) | s76 (Good faith) | Self-approval prevention + audit accountability |
| P7 (Delegation of authority) | s76 (Duty of care) | Two-Key Authorization + threshold controls |
| P11 (Risk management) | s77 (Liability mitigation) | Risk-based routing + ISO 37001 classification |
| P13 (Compliance) | s72 (Social & ethics) | ESG reporting + SARS validation + POPIA consent |
| P15 (Combined assurance) | s76 (Reasonable diligence) | Approval_History audit trail + SLA enforcement |
