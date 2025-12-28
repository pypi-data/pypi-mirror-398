# Collections - Python SDK Documentation

## Overview

Collections model every table in BosBase. Behind the scenes they are ordinary SQLite tables generated from the collection metadata (name, type, fields, indexes, rules, etc.).

Each row in a collection is a *record*. Records are exposed through the Records API and automatically inherit the access rules defined on the collection.

All examples use synchronous code because the Python SDK is backed by the `requests` library.

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")
pb.collection("_superusers").auth_with_password("admin@example.com", "password")
```

## Collection Types

### Base Collections

Use base collections for custom business data.

```python
article_collection = pb.collections.create_base(
    "articles",
    overrides={
        "fields": [
            {"name": "title", "type": "text", "required": True},
            {"name": "status", "type": "select", "values": ["draft", "ready"]},
        ]
    },
)
```

### Auth Collections

Auth collections extend base collections with built‑in account management features (email, password, verification, MFA, OAuth2).

```python
users = pb.collections.create_auth(
    "users",
    overrides={
        "fields": [
            {"name": "name", "type": "text", "required": True},
            {"name": "role", "type": "select", "values": ["author", "editor"]},
        ]
    },
)
```

### View Collections

View collections are read-only projections defined by SQL.

```python
stats = pb.collections.create_view(
    "post_stats",
    view_query="""
        SELECT posts.id,
               posts.title,
               COUNT(comments.id) AS totalComments
        FROM posts
        LEFT JOIN comments ON comments.post = posts.id
        GROUP BY posts.id
    """,
)
```

## Managing Collections

### List Collections

```python
page = pb.collections.get_list(page=1, per_page=30)
all_collections = pb.collections.get_full_list()
```

### Retrieve a Collection

```python
articles = pb.collections.get_one("articles")
```

### Update or Delete

```python
pb.collections.update(
    "articles",
    body={"viewRule": 'status = "published"'},
)

pb.collections.delete_collection("legacy")
```

### Truncate Records

Delete all records without dropping the schema.

```python
pb.collections.truncate("logs")
```

## Scaffolds and Import/Export

- `get_scaffolds()` returns prebuilt collection templates.
- `create_from_scaffold(type, name, overrides=…)` lets you bootstrap with defaults.
- `import_collections()` loads collections from JSON and optionally deletes missing ones.

```python
scaffolds = pb.collections.get_scaffolds()
pb.collections.import_collections(
    collections=[scaffolds["base"]],
    delete_missing=False,
)
```

## Schema Queries

Use lightweight schema endpoints for AI, tooling, or documentation.

```python
schema = pb.collections.get_schema("articles")
all_schemas = pb.collections.get_all_schemas()
```

The response contains `name`, `type`, and field metadata (`name`, `type`, `required`, `system`, `hidden`).

## Best Practices

1. Keep business logic in access rules whenever possible.
2. Use scaffolds for predictable system fields.
3. Name relations clearly (`post`, `post_comments`) to simplify expand usage.
4. Store schema snapshots (`pb.collections.get_full_list()`) in version control for auditing.
5. Use `truncate()` instead of dropping collections when re-seeding dev data.
