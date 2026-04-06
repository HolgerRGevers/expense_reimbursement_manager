# Test Scenarios

## Overview

5 end-to-end test cases covering the core expense claim lifecycle, governance controls, and edge cases.

## Test Cases

To be populated with detailed test scenarios including:

1. **Happy path**: Employee submits under-threshold claim -> LM approves -> GL populated -> Approved
2. **Threshold escalation**: Employee submits over-threshold claim -> LM approves -> escalates to HoD -> HoD approves
3. **Self-approval prevention**: Line Manager submits claim -> bypasses LM tier -> routes to HoD
4. **Rejection and resubmission**: Employee submits -> LM rejects -> Employee edits and resubmits -> version incremented
5. **SLA enforcement**: Claim sits pending > 3 days -> auto-escalation to HoD

Each scenario specifies: preconditions, test steps, expected results, and audit trail verification.
