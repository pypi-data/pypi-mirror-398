# API Rules & Filters - Python SDK

BosBase enforces access control through collection rules (list/view/create/update/delete). The Python SDK mirrors the rule and filter syntax used by the backend, so everything you can express inside the Admin UI can be scripted.

## Filter Helper

`pb.filter(expr, params)` builds safe filter expressions. It accepts strings, numbers, booleans, datetimes, `None`, dicts, lists, and other serializable types.

```python
from datetime import datetime, timedelta

cutoff = datetime.utcnow() - timedelta(days=7)

expr = pb.filter(
    "author = {:author} && status = {:status} && created >= {:cutoff}",
    {"author": "john", "status": "published", "cutoff": cutoff},
)

records = pb.collection("posts").get_list(
    page=1,
    per_page=50,
    query={"filter": expr},
)
```

Internally the helper JSON-serializes non-primitive objects and escapes single quotes, so the resulting string can be used safely with user input.

## Common Operators

- `=`, `!=`, `<`, `<=`, `>`, `>=`
- `&&` and `||`
- `~` (case insensitive match)
- `?~` (regex)
- `@>`, `<@` (array containment)
- `!~` (negative match)
- `:isset`, `:empty`
- `?` placeholders for relation checks when using `expand`

```python
expr = pb.filter("tags @> {:tag}", {"tag": "release"})
```

## API Rules

Rules are written with the same expression language and are evaluated server-side for every request. Typical pattern:

```text
@request.auth.id = createdBy.id
```

`@request` exposes context like:

- `@request.auth` – authenticated record (or `null`)
- `@request.method`
- `@request.body`, `@request.data`
- `@request.headers`
- `@request.query.filter`

`@collection` references other collections, enabling cross-collection lookups.

```text
@collection.categories.id ?= category
```

## Tips for Writing Rules

1. Use the Admin UI to prototype rules, then copy to code.
2. Keep rules symmetrical (list/view) unless there is a specific reason not to.
3. For owner-based access, compare `@request.auth.id` to the record field.
4. Combine with status fields: `@request.auth.role = "admin" || status = "published"`.
5. Use `:isset`/`:empty` to guard optional fields.

## Debugging Access

- The server responds with `403` and includes the rule name that failed (when verbose errors are enabled).
- Attach a rule to logs (`pb.logs.get_list(filter="context.rule = 'listRule'"`) when diagnosing complex expressions.
- `pb.filter()` outputs plain strings; printing them before making calls helps catch typos.

## Security Checklist

- Never concatenate user input manually. Always go through `pb.filter()` or parameterized expressions.
- Restrict admin features to `_superusers`. Normal auth collections should have explicit rules even when used internally.
- Validate `@request.body` inside rules to enforce custom invariants.
- Combine rules with Webhooks or Cron tasks to enforce periodic clean-up as needed.
