# SQL Execution API - Python SDK

## Overview

The SQL Execution API lets superusers run ad-hoc SQL against the BosBase database and retrieve the raw results. Use it for controlled maintenance or diagnostics tasks—never expose it to untrusted input.

**Key points**
- Superuser authentication is required.
- Supports both read and write statements.
- Returns column names, rows, and `rowsAffected` for writes.
- Respects the SDK request hooks, headers, and timeouts.

**Endpoint**
- `POST /api/sql/execute`
- Body: `{ "query": "<your SQL statement>" }`

## Authentication

Authenticate as a superuser before calling `pb.sql.execute()`:

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")
pb.collection("_superusers").auth_with_password("admin@example.com", "password")
```

## Executing a SELECT

```python
result = pb.sql.execute("SELECT id, text FROM demo1 ORDER BY id LIMIT 5")

print(result.columns)  # ["id", "text"]
print(result.rows)     # [["84nmscqy84lsi1t", "test"], ...]
```

## Executing a Write Statement

```python
update = pb.sql.execute(
    "UPDATE demo1 SET text='updated via api' WHERE id='84nmscqy84lsi1t'",
)

print(update.rows_affected)  # 1
print(update.columns)        # ["rows_affected"]
print(update.rows)           # [["1"]]
```

## Inserts and Deletes

```python
# Insert
insert = pb.sql.execute(
    "INSERT INTO demo1 (id, text) VALUES ('new-id', 'hello from SQL API')",
)
print(insert.rows_affected)  # 1

# Delete
removed = pb.sql.execute("DELETE FROM demo1 WHERE id='new-id'")
print(removed.rows_affected)  # 1
```

## Response Shape

```python
{
    "columns": ["col1", "col2"],  # omitted when empty
    "rows": [["v1", "v2"]],       # omitted when empty
    "rows_affected": 3,           # only present for write operations
}
```

`pb.sql.execute()` returns a `SQLExecuteResponse` dataclass with the same attributes.

## Error Handling

- Empty queries raise `ValueError` before a request is sent.
- Database or syntax errors raise `ClientResponseError`.
- You can pass headers, query params, or a custom timeout via keyword args.

## Safety Tips

- Never pass user-controlled SQL into this API.
- Prefer explicit single statements.
- Keep superuser credentials scoped and rotated regularly.
