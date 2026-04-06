# Claim Lifecycle State Machine

## Status Values

From the Expense_Claims status picklist: Draft, Submitted, Pending LM Approval, Pending HoD Approval, Approved, Rejected, Resubmitted.

## State Transitions

```
                    +-------+
                    | Draft |
                    +---+---+
                        |
                  [form submit]
                        |
                  +-----v------+
                  | Submitted  |  (On Validate sets status)
                  +-----+------+
                        |
              +---------+---------+
              |                   |
     [normal employee]    [submitter is LM]
              |                   |
    +---------v--------+   +-----v--------------+
    | Pending LM       |   | Pending HoD        |
    | Approval         |   | Approval           |
    +---+---------+----+   +---+------------+----+
        |         |            |            |
   [LM approves] [LM rejects] |            |
        |         |            |            |
        |    +----v----+  [HoD approves] [HoD rejects]
        |    | Rejected |      |            |
        |    +----+-----+  +--v------+  +--v-------+
        |         |         | Approved|  | Rejected |
        |         |         +---------+  +----+-----+
        |         |                           |
        |         +----------+----------------+
        |                    |
        |              [employee edits
        |               and resubmits]
        |                    |
        |              +-----v-------+
        |              | Resubmitted |
        |              +-----+-------+
        |                    |
        |         +----------+---------+
        |         |                    |
        |  [normal employee]   [submitter is LM]
        |         |                    |
        |  +------v---------+  +------v--------------+
        |  | Pending LM     |  | Pending HoD         |
        |  | Approval       |  | Approval             |
        |  +----------------+  +----------------------+
        |
   [amount <= threshold]----> Approved (final)
        |
   [amount > threshold]----> Pending HoD Approval
        |                          |
        |                    [HoD approves]----> Approved
        |                    [HoD rejects]-----> Rejected
        |
   [SLA >= 3 days]---------> Pending HoD Approval (auto-escalation)
   [SLA >= 2 days]---------> Reminder sent to LM
```

## Terminal States

- **Approved**: Claim fully approved, GL code populated
- **Rejected**: Claim rejected (can be resubmitted)

## Key Governance Controls

1. **Self-approval prevention**: If submitter holds LM role, system bypasses LM tier
2. **Threshold-based routing**: LM can give final approval only under R999.99 (Tier 1)
3. **SLA enforcement**: 2-day reminder, 3-day auto-escalation (v2.1 targets)
4. **Version tracking**: Each resubmission increments Version counter
5. **Audit trail**: Every state transition logged in Approval_History
