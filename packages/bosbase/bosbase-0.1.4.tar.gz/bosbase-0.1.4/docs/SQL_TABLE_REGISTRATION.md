# Register Existing SQL Tables with the Python SDK

Use the SQL table helpers to expose existing tables (or run SQL to create them) and automatically generate REST collections. Both calls are **superuser-only**.

- `pb.collections.register_sql_tables(tables)` – map existing tables to collections without running SQL.
- `pb.collections.import_sql_tables(definitions)` – optionally run SQL to create tables first, then register them. Returns `{"created": [...], "skipped": [...]}`.

## Requirements

- Authenticate with a `_superusers` token.
- Each table must contain a `TEXT` primary key column named `id`.
- Missing audit columns (`created`, `updated`, `createdBy`, `updatedBy`) are automatically added so the default API rules can be applied.
- Non-system columns are mapped by best effort (text, number, bool, date/time, JSON).

## Basic Usage

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")
pb.collection("_superusers").auth_with_password("admin@example.com", "password")

collections = pb.collections.register_sql_tables(["projects", "accounts"])
print([c["name"] for c in collections])
# -> ["projects", "accounts"]
```

## With Request Options

You can pass headers, query params, or a timeout like any other request.

```python
collections = pb.collections.register_sql_tables(
    ["legacy_orders"],
    headers={"x-trace-id": "reg-123"},
    query={"q": 1},
)
```

## Create-or-register Flow

`import_sql_tables()` accepts `{ "name": str, "sql"?: str }` items, runs the SQL (if provided), and registers collections. Existing collection names are reported under `skipped`.

```python
result = pb.collections.import_sql_tables(
    [
        {
            "name": "legacy_orders",
            "sql": """
              CREATE TABLE IF NOT EXISTS legacy_orders (
                id TEXT PRIMARY KEY,
                customer_email TEXT NOT NULL
              );
            """,
        },
        {"name": "reporting_view"},  # assumes table already exists
    ]
)

print([c["name"] for c in result["created"]])
print(result["skipped"])
```

## What It Does

- Creates BosBase collection metadata for the provided tables.
- Generates REST endpoints for CRUD against those tables.
- Applies the standard default API rules (authenticated create; update/delete scoped to the creator).
- Ensures audit columns exist (`created`, `updated`, `createdBy`, `updatedBy`) and leaves all other existing SQL schema and data untouched; no further field mutations or table syncs are performed.
- Marks created collections with `externalTable: True` so you can distinguish them from regular BosBase-managed tables.

## Troubleshooting

- `ValueError`: you passed an empty table list.
- 400: ensure `id` exists as `TEXT PRIMARY KEY` and the table name is not system-reserved (no leading `_`).
- 401/403: confirm you are authenticated as a superuser.
- Default audit fields are auto-added if they are missing so the default owner rules validate successfully.
