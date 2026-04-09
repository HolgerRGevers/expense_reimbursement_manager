# Deluge Language Reference

Comprehensive reference for Zoho Deluge scripting, extracted from official Zoho documentation.
Source: https://www.zoho.com/deluge/help/

---

## 1. Data Types

Deluge is dynamically typed -- no type declarations needed.

| Type | Literal Syntax | Examples |
|------|---------------|----------|
| Text | Double quotes only | `"hello"`, `"line1\nline2"` |
| Number | Integer literal | `42`, `-7`, `0` |
| Decimal | Float literal | `3.14`, `-0.5` |
| Boolean | Keywords | `true`, `false` |
| Date | Single quotes | `'2026-04-06'` |
| DateTime | Single quotes | `'2026-04-06 14:30:00'` |
| Time | Single quotes | `'14:30:00'` |
| List | Curly braces | `{"a", "b", "c"}` or `List()` |
| Map (Key-Value) | Curly braces with colons | `{"key": "value", "num": 42}` |
| File | From upload or fetch | (no literal) |
| Null | Keyword | `null` |

### Important type rules
- Text MUST use double quotes (single quotes are for dates/times only)
- Lists and maps both use `{}` -- context determines type
- `null` is a valid value for any type -- always guard with `ifnull()`
- Type coercion is implicit in many contexts (e.g., number + text = text concatenation)

---

## 2. Variables

### Declaration
Assignment creates the variable:
```
count = 0;
name = "Alice";
items = {"a", "b"};
```

### Naming rules
- Must start with: letter (a-z, A-Z) or underscore
- Can contain: letters, numbers, underscores
- NO spaces (use underscores)
- Case-sensitive: `var` != `Var`
- Reserved words (cannot use as names): `true`, `false`, `null`, `void`, `return`

### Scope
Variables have **local scope only** -- accessible only within the script where declared. No global variables.

---

## 3. Operators

### Arithmetic

| Operator | Name | Types | Notes |
|----------|------|-------|-------|
| `+` | Addition | Number, Decimal, Text | Text + anything = concatenation |
| `-` | Subtraction | Number, Decimal, DateTime | DateTime subtraction supported |
| `*` | Multiplication | Number, Decimal | |
| `/` | Division | Number, Decimal | Division by zero = runtime error |
| `%` | Modulus | Number, Decimal | |

### Assignment

| Operator | Name | Types |
|----------|------|-------|
| `=` | Simple assign | All types |
| `+=` | Add-assign | Text, Number, Decimal |
| `-=` | Subtract-assign | Number, Decimal |
| `*=` | Multiply-assign | Number, Decimal |
| `/=` | Divide-assign | Number, Decimal |
| `%=` | Modulus-assign | Number, Decimal |

### Relational

| Operator | Name | Types |
|----------|------|-------|
| `==` | Equals | Number, Decimal, DateTime, Text |
| `!=` | Not equals | Number, Decimal, DateTime |
| `<` | Less than | Number, Decimal, DateTime |
| `>` | Greater than | Number, Decimal, DateTime |
| `<=` | Less than or equal | Number, Decimal, DateTime |
| `>=` | Greater than or equal | Number, Decimal, DateTime |

Note: Text comparison with `==` is supported, but `<`, `>` etc. on text are NOT.

### Logical

| Operator | Name | Behavior |
|----------|------|----------|
| `&&` | AND | Both conditions must be true |
| `\|\|` | OR | At least one condition must be true |
| `!` | NOT | Negates a single condition |

### Precedence (Zoho Creator specific)
1. `!` (NOT)
2. `||` (OR)
3. `&&` (AND)

**Warning**: Creator uses OR before AND (opposite of most languages). Use parentheses to make intent explicit.

---

## 4. Control Flow

### If / Else If / Else
```
if (condition)
{
    // statements
}
else if (condition2)
{
    // statements
}
else
{
    // statements
}
```

### For Each (collection)
```
for each item in collection
{
    // statements
}
```

### For Each (records with criteria)
```
for each rec in FormName[field == value]
{
    // access rec.fieldName
}
```

With sorting:
```
for each rec in FormName[field > 0] sort by field asc
{
    // sorted iteration
}
```

---

## 5. Zoho System Variables (Read-Only)

### Date/Time
| Variable | Returns | Scope |
|----------|---------|-------|
| `zoho.currentdate` | Current date | All Zoho apps |
| `zoho.currenttime` | Current datetime | All Zoho apps |

### User Identity
| Variable | Returns | Scope |
|----------|---------|-------|
| `zoho.loginuser` | Username of logged-in user | All apps ("Public" for public users) |
| `zoho.loginuser.name` | Full name of logged-in user | Creator only |
| `zoho.loginuserid` | Email of logged-in user | All apps (null for unauthenticated) |
| `zoho.adminuser` | Username of app owner | All apps |
| `zoho.adminuserid` | Email of app owner | All apps |

### Application
| Variable | Returns | Scope |
|----------|---------|-------|
| `zoho.appname` | Application link name | Creator only |
| `zoho.appuri` | App path: `/<admin>/<app_link>/` | Creator only |
| `zoho.ipaddress` | Public IP of user | All apps (null outside session) |
| `zoho.device.type` | `"web"`, `"phone"`, or `"tablet"` | Creator only |

### Important notes
- Gmail addresses CANNOT be used as sender in sendmail (since Feb 2024)
- `zoho.device.type` defaults to `"web"` in scheduled workflows
- `zoho.loginuserid` returns null for public/unauthenticated users

---

## 6. Built-in Functions

### Text Functions (71 functions)
**Search/Test**: contains, notContains, containsIgnoreCase, isEmpty, startsWith, startsWithIgnoreCase, endsWith, endsWithIgnoreCase, equalsIgnoreCase, matches

**Extract**: getAlpha, getAlphaNumeric, getPrefix, getPrefixIgnoreCase, getSuffix, getSuffixIgnoreCase, getOccurenceCount, left, right, mid, subText, substring, find, indexOf, lastIndexOf

**Transform**: toUpperCase, toLowerCase, proper, trim, ltrim, rtrim, reverse, leftpad, rightpad, concat, repeat, text

**Remove**: remove, removeAllAlpha, removeAllAlphaNumeric, removeFirstOccurence, removeLastOccurence

**Replace**: replaceAll, replaceAllIgnoreCase, replaceFirst, replaceFirstIgnoreCase

**Convert**: toList, toMap, toLong, toNumber, toString, toText, toJSONList, toListString, toDecimal, toTime, toDate

**Measure**: len, length, isAscii

**Encoding**: hexToText, textToHex

### Number Functions (38 functions)
**Math**: abs, ceil, floor, round, frac, sqrt, power, exp, log, log10

**Trig**: sin, cos, tan, asin, acos, atan, atan2, sinh, cosh, tanh, asinh, acosh, atanh

**Statistics**: average, median, max, min, largest, smallest, nthLargest, nthSmallest

**Conversion**: toHex, toDecimal, toLong, toWords

**Check**: isNumber, randomNumber

### Date-Time Functions (51 functions)
**Add**: addDay, addBusinessDay, addWeek, addMonth, addYear, addHour, addMinutes, addSeconds

**Subtract**: subDay, subBusinessDay, subWeek, subMonth, subYear, subHour, subMinutes, subSeconds

**Extract**: day, getDay, getDayOfYear, getHour, getMinutes, getMonth, getSeconds, getWeekOfYear, getYear, hour, minute, month, second, weekday

**Calculate**: daysBetween, hoursBetween, monthsBetween, yearsBetween, days360, totalMonth, totalYear

**Navigate**: toStartOfMonth, toStartOfWeek, nextWeekDay, previousWeekDay, edate, eomonth, workday

**Get current**: now, today

**Convert**: toString, toTime, toDate, toDateTimeString, unixEpoch

**Check**: isDate

### List Functions (25 functions)
**Modify**: add, addAll, clear, remove, removeAll, removeElement, insert, sort, distinct, subList

**Query**: contains, notContains, get, indexOf, lastIndexOf, isEmpty, size, intersect

**Stats**: average, largest, smallest, median, nthLargest, nthSmallest

**Convert**: toJSONList, toList

### Map (Key-Value) Functions (13 functions)
**Modify**: put, putAll, remove, clear

**Query**: get, containKey, containValue, notContains, isEmpty, size, keys

**Convert**: toMap, toJSONList

### Collection Functions (23 functions)
clear, containsKey, containsValue, delete, deleteAll, deleteKey, deleteKeys, distinct, duplicate, get, getKey, getLastKey, insert, insertAll, intersect, isEmpty, keys, size, sort, sortKey, update, values, notContains

### Logical Functions (3 functions)
| Function | Description |
|----------|-------------|
| `isBlank` | True if value is blank (empty string or null) |
| `isEmpty` | True if value is empty string |
| `isNull` | True if value is null |

### Type Check Functions (4 functions)
| Function | Description |
|----------|-------------|
| `isDate` | True if value is a valid date |
| `isFile` | True if value is a file |
| `isNumber` | True if value is numeric |
| `isText` | True if value is text |

### Type Conversion Functions (8 functions)
toDate, toDecimal, toJSONList, toLong, toString, toTime, toList, toMap

### Boolean-Returning Functions (complete list)
**Text**: contains, containsIgnoreCase, endsWith, endsWithIgnoreCase, equalsIgnoreCase, matches, notContains, startsWith, startsWithIgnoreCase

**List**: contains

**Map**: containKey, containValue

**Logical**: isBlank, isEmpty, isNull

**Number**: isEven, isOdd

**Type check**: isDate, isFile, isNumber, isText

### Utility Functions (2 functions)
encodeUrl, getJSON

---

## 7. Built-in Tasks

### sendmail
```
sendmail
[
    from : zoho.adminuserid
    to : "recipient@domain.com"
    subject : "Subject line"
    message : "Message body"
]
```
Optional params: `cc`, `bcc`, `replyto`, `content_type`

**Required fields**: from, to, subject, message
**Constraint**: from/to must include zoho.adminuserid or zoho.loginuserid

### info (debug)
```
info expression;
```
Logs to the Deluge console. Does not affect execution.

### alert (user-facing)
```
alert "Message to user";
```

### cancel submit
```
cancel submit;
```
Aborts form submission (use in On Validate).

### return
```
return;
```
Exits the current script.

### Integration tasks
General syntax: `zoho.<service>.<action>(<parameters>)`
~260 built-in integrations across 35 Zoho services.

### invokeUrl (custom HTTP)
```
response = invokeUrl
[
    url : "https://api.example.com/endpoint"
    type : GET
    headers : headerMap
    parameters : paramMap
    connection : "connectionName"
];
```

---

## 8. Record Operations

### Insert
```
row = insert into FormName
[
    field1 = value1
    field2 = value2
    Added_User = zoho.loginuser
];
```
Note: Uses `=` for field assignment (not `:` like sendmail).

### Query
```
records = FormName[criteria];
singleRec = FormName[ID == recordId];
```
Always null-guard: `if (records != null && records.count() > 0)`

### Update
```
rec.FieldName = newValue;
```
On fetched records only.

### Delete
```
delete from FormName[criteria];
```

---

## 9. Common Error Messages

### Save Errors (caught before execution)
| Error | Cause | Fix |
|-------|-------|-----|
| "Variable 'x' is not defined" | Using undeclared variable | Declare before use |
| "Expecting '}' but found 'EOF'" | Unclosed brace | Match all `{` with `}` |
| "Missing ';'" | Missing semicolon or unquoted text | Add `;` or wrap text in `""` |
| "Number of Arguments mismatches" | Wrong param count | Check function signature |
| "From: address is not zoho.adminuserid" | Invalid sendmail sender | Use zoho.adminuserid or zoho.loginuserid |
| "Not able to find 'X' function" | Undefined function | Check function name/spelling |
| "Type mismatch left/right expression" | Comparing incompatible types | Match operand types |

### Runtime Errors (caught during execution)
| Error | Cause | Fix |
|-------|-------|-----|
| "Divide by zero error" | Division by 0 | Check divisor before dividing |
| "Null value occurred" | Operation on null | Use `ifnull()` or null check |
| "Given index > list size" | List index out of bounds | Check `size()` first |
| "Invalid JSON Format String" | Bad JSON text | Validate JSON structure |
| "UnParsable date" | Invalid date format | Use correct date format |
| "can not be cast to 'MAP'" | Wrong type where map expected | Provide correct collection type |

---

## 10. Creator-Specific Features

### Form field access
- `input.FieldName` -- current form record (in workflows)
- `input.ID` -- auto-generated record ID

### Approval process scripts
- On Approve / On Reject scripts run in approval context
- `input` refers to the record being approved

### Scheduled workflows
- Can be daily (Free Trial) or hourly (paid plans)
- `zoho.device.type` defaults to `"web"` in scheduled context
- No `hoursBetween` on Free Trial daily schedules -- use `daysBetween`

### Role checking
```
if (thisapp.permissions.isUserInRole("Role Name"))
{
    // user has this role
}
```
**WARNING**: `zoho.loginuserrole` does NOT exist. Always use `thisapp.permissions.isUserInRole()`.

### Field rules vs workflows
- Field rules: client-side, instant UI updates
- Workflows: server-side, run on form events (validate, success, edit)

### Custom API scripts
- Custom APIs are defined via the Custom API Builder wizard (Microservices > Custom API)
- Scripts run in API context, NOT form context
- No `input.FieldName` -- parameters come from the Request step definition
- No `alert`, `cancel submit`, or other form-specific tasks
- Must populate response keys matching the Response step definition
- Can query any form/report, perform inserts/updates, call external services via `invokeUrl`
- Authentication: Same OAuth 2.0 as REST API v2.1
- **UNCERTAIN**: Exact parameter access and response construction syntax needs Creator verification
- See `docs/zoho-custom-api-builder-research.md` for full reference

---

## 11. Style & Syntax Rules

1. Strings always use double quotes: `"text"` (never `'text'`)
2. Dates use single quotes: `'2026-04-06'`
3. Semicolons are generally optional but required after task blocks
4. Comments: `//` for single-line, `/* ... */` for multi-line
5. `insert into` uses `=` for fields; `sendmail` uses `:` for params
6. No `lpad()` function exists -- use manual string padding
7. `ifnull(value, fallback)` for every query result
8. Always include `Added_User = zoho.loginuser` in audit inserts
