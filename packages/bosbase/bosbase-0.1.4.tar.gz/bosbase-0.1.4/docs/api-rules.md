# API Rules Documentation (Python SDK)

This guide mirrors the `API_RULES_AND_FILTERS.md` content using a simplified, shareable format. For the full breakdown, including filter helpers and rule expressions, read `API_RULES_AND_FILTERS.md`.

Key reminders:

1. Every collection has `list`, `view`, `create`, `update`, and `delete` rules. Auth collections also expose `authRule` and `manageRule`.
2. Rule values:
   - `null` → locked down (superusers only).
   - `""` → publicly accessible.
   - expression → evaluated for each request (see the main rules guide).
3. Manage rules with the Collection API:

```python
pb.collections.update(
    "products",
    body={"listRule": '@request.auth.id != ""'},
)
```

4. Validate complex logic in the Admin UI first, then keep the expressions in source control.
