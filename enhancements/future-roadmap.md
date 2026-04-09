# Future Roadmap

## Overview

Planned enhancements beyond v0.7.0 (International Standards Alignment + ESG Tracking).

## Completed Enhancements (for reference)

| Enhancement | Version | Status |
|-------------|---------|--------|
| Two-Key Threshold Authorization | v0.5.0 | Complete |
| Access-to-Zoho Import Pipeline | v0.6.0 | Complete |
| Hybrid Cross-Environment Linter | v0.6.0 | Complete |
| Mock Data Generation (7 personas, 175 claims) | v0.6.0 | Complete |
| International Standards Alignment (ISSB/GRI/ISO) | v0.7.0 | Complete |
| ESG Tracking + Carbon Estimation | v0.7.0 | Complete |
| Compliance_Config (org-type controls) | v0.7.0 | Complete |
| Sustainability Dashboard | v0.7.0 | Complete |

## Near-Term: Zoho Creator REST API Integration

The import pipeline is built and tested in mock mode. Next step is live API integration:

- **OAuth 2.0 authentication** via Zoho API Console (self-client, refresh token flow)
- **Record-by-record import** through the Creator form API -- each record hits the same `on_validate` rules as a human submission
- **Import audit trail** (`exports/csv/import_audit.csv`) logs successful imports AND validation rejections with exact error messages
- **175 synthetic claims** ready to stress-test every approval pathway including Two-Key and ESG tracking

The tooling (`tools/upload_to_creator.py`) runs in mock mode by default. Add `--live` when API credentials are configured in `config/zoho-api.yaml`.

## Near-Term: Custom API Builder Exploration

Zoho Creator's Custom API Builder (Microservices > Custom API) allows defining custom REST endpoints backed by Deluge scripts. Unlike the REST API v2.1 (fixed CRUD), Custom APIs execute arbitrary logic and return user-defined JSON responses.

**Research completed** — see `docs/zoho-custom-api-builder-research.md` for full reference.

**Priority use cases identified**:
- **Get_Dashboard_Summary** — aggregated claim stats for external dashboards (High)
- **Get_Claim_Status** — external systems query claim status by reference number (High)
- **Get_ESG_Summary** — carbon/ESG data feed for sustainability reporting (Medium)
- **Get_SLA_Breaches** — proactive SLA management (Medium)
- **Create_Journal_Entry** — Zoho Books integration endpoint (Medium)

**Tooling support added**: `custom-api` context in manifest, scaffold, and linter (DG020/DG021).

**Next step**: Create a test Custom API (`Test_Ping`) in Creator UI to verify endpoint URL format, parameter access syntax, and response construction. Requires Standard plan or above.

## Near-Term: Hardcoded Email Remediation (G-05)

The last open governance gap -- 8 hardcoded demo email addresses across 6 `.dg` files need replacement with a config-table-based lookup or role-based email resolution. Options:

1. **Compliance_Config table** -- add email config keys (fits existing pattern)
2. **Zoho roles API** -- resolve email from role assignment at runtime
3. **Email_Config form** -- dedicated lookup table for notification routing

## Mid-Term: Planned Integrations

- **Zoho Books**: Automated journal entry creation on claim approval (GL code already mapped)
- **Zoho Analytics**: Advanced reporting dashboards and trend analysis beyond built-in Creator reports
- **Zoho Expense**: Receipt OCR integration and mileage tracking

## Mid-Term: Planned Features

- **Mobile Optimization**: Enhanced phone/tablet layouts for field staff submissions
- **Batch Processing**: Bulk approval workflows for managers with multiple pending claims
- **Currency Support**: Multi-currency claims with exchange rate lookups (relevant for MULTINATIONAL org type)
- **Supplier/Vendor Tracking**: Enable B-BBEE preferential procurement tracking (Compliance_Config flag exists, data model pending)
- **Distance-Based Carbon**: Integrate with travel booking systems for km-based emission factors (currently spend-based via DEFRA factors)

## Long-Term: Technical Improvements

- Migrate SLA enforcement from daily to hourly schedule (requires Standard plan upgrade)
- Implement proper `hoursBetween` for SLA calculations (not available on Free Trial)
- Add comprehensive error handling and retry logic for email notifications
- Tree-sitter grammar for Deluge AST tooling if managing multiple Creator apps (see `enhancements/omega-script-vision.md`)

## Long-Term: Compliance Expansion

- **ISSA 5000 assurance pack**: Pre-formatted export templates for sustainability auditors
- **Carbon factor refinement**: Replace DEFRA estimates with supplier-specific emission data
- **JSE Listings compliance**: Full internal controls disclosure workflow (flag exists in Compliance_Config)
- **PFMA/MFMA controls**: Government expenditure workflow extensions for SOE org type
