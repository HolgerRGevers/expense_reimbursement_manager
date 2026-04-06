# Expense Reimbursement Manager — Project Memory

## What this repo is
Version archive and documentation hub for a Zoho Creator expense reimbursement app. 
No CI/CD — Creator has no structural deployment API. Code is applied manually in Creator UI.

## Tech stack
- **Platform**: Zoho Creator (Free Trial → Standard)
- **Scripting**: Deluge (event-driven, not general-purpose)
- **File convention**: `.dg` = Deluge script files (plain text)

## Key Deluge rules (always follow these)
- `zoho.loginuserrole` does NOT exist — use `thisapp.permissions.isUserInRole("Role Name")`
- `lpad()` does not exist in Deluge
- `hoursBetween` not available on Free Trial daily schedules — use `daysBetween`
- All `insert into approval_history` blocks MUST include `Added_User = zoho.loginuser`
- Threshold fallback value is `999.99` (matches seed data), not `1000`
- GL query always needs null guard: `glRec != null && glRec.count() > 0`
- Strings use double quotes only (never single quotes)
- `ifnull(value, fallback)` for every query result

## Repo structure convention
- `src/deluge/` — scripts organised by Creator UI location (form-workflows, approval-scripts, scheduled)
- `docs/` — architecture, compliance, build-guide, testing
- `config/seed-data/` — JSON source of truth for lookup/config tables
- `exports/` — manual .ds snapshots from Creator

## Governance context
South African compliance: King IV principles, SARS S11(a), segregation of duties.
This is not optional flavour — it drives architectural decisions (self-approval prevention, audit trail writes, configurable thresholds).

## Deluge quick-reference

### Data types
- **Text**: double quotes only (`"hello"`, never `'hello'`)
- **Number**: integer (`42`)
- **Decimal**: float (`3.14`)
- **Boolean**: `true` / `false`
- **Date**: single quotes (`'2026-04-06'`) — only dates use single quotes
- **DateTime**: `'2026-04-06 14:30:00'`
- **List**: `{"a", "b", "c"}` or `List()`
- **Map/Key-Value**: `{"key": "value", "key2": "value2"}`
- **Null**: `null` — always guard with `ifnull()`

### Variables
Dynamically typed. Assignment creates the variable:
```
count = 0;
name = "Alice";
```

### Operators
- Arithmetic: `+`, `-`, `*`, `/`
- Comparison: `==`, `!=`, `>`, `<`, `>=`, `<=`
- Logical: `&&`, `||`
- String/collection: `contains`, `in`

### Control flow
```
if (condition)
{
    // ...
}
else if (condition2)
{
    // ...
}
else
{
    // ...
}
```

### Loops
```
for each item in collection
{
    info item;
}
```
Record loop with criteria:
```
for each rec in FormName[field == value]
{
    // ...
}
```

### Built-in tasks (bracket syntax)
```
sendmail
[
    from : zoho.adminuserid
    to : "email@domain.com"
    subject : "Subject"
    message : "Body"
];
```

### Common built-ins
- `zoho.currentdate` — today's date
- `zoho.currenttime` — current datetime
- `zoho.loginuser` — logged-in user name
- `zoho.loginuserid` — logged-in user email
- `zoho.adminuserid` — app admin email
- `thisapp.permissions.isUserInRole("Role")` — role check (NOT `zoho.loginuserrole`)
- `ifnull(value, fallback)` — null coalescing
- `daysBetween(date1, date2)` — days between two dates
- `input.FieldName` — current form field value
- `alert "message"` — show user alert
- `cancel submit` — abort form submission
- `info expression` — debug log

### Collection methods
- `list.add(element)` — append to list
- `list.size()` — list length
- `map.put("key", value)` — add to map
- `map.get("key")` — retrieve from map
- `collection.count()` — record count from query

### Record operations
```
// Insert
row = insert into FormName [field1 = value1  field2 = value2  Added_User = zoho.loginuser];

// Query (returns collection)
recs = FormName[criteria];

// Update (on fetched record)
rec.FieldName = newValue;
```

### Gotchas (project-specific)
See "Key Deluge rules" section above. Additionally:
- No `lpad()`, no `hoursBetween` on Free Trial
- Semicolons optional on most statements but required after task blocks
- `insert into` field assignments use `=` not `:` (unlike sendmail)
- Record queries return collections — always null-guard before accessing fields

## Version convention
v0.0 (Launchpad Generated) → v0.1 (Scaffold Remediation) → v1.0 (Demo Ready)

