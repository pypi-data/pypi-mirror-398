# BosBase Python SDK

BosBase provides a batteries-included backend with collections, authentication, files,
vector search, LangChaingo flows, realtime subscriptions, and more.  
This package is the official Python SDK that mirrors the JavaScript and Dart SDKs
in this repository so Python developers can talk to the BosBase API with a familiar API surface.

## Installation

```bash
pip install bosbase
```

## Quick start

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

# Authenticate as auth collection record
auth = pb.collection("users").auth_with_password("test@example.com", "123456")
print(auth.token)

# List records
posts = pb.collection("posts").get_list(page=1, per_page=10, query={"expand": "author"})
for post in posts["items"]:
    print(post["title"])

# Create a record with a file
with open("cover.png", "rb") as handle:
    pb.collection("posts").create(
        body={"title": "Hello", "status": "published"},
        files={"cover": ("cover.png", handle, "image/png")},
    )

# Realtime subscription
unsubscribe = pb.collection("posts").subscribe("*", lambda event: print(event["action"]))
# ...
unsubscribe()
```

## High-level features

- `pb.collection("...")` – CRUD helpers, auth flows, OTP/MFA helpers, impersonation.
- `pb.collections` – Manage collections, scaffolds, schema queries.
- `pb.files` – Token generation and URL building for protected files.
- `pb.logs`, `pb.crons`, `pb.backups`, `pb.vectors`, `pb.llm_documents`, `pb.langchaingo`, `pb.caches` – Service wrappers that mirror the JavaScript SDK.
- `pb.sql` – Superuser SQL execution with column/row responses; `pb.collections.register_sql_tables()` and `pb.collections.import_sql_tables()` expose existing SQL tables as BosBase collections.
- `pb.realtime` – SSE based realtime subscriptions with automatic reconnection.
- `pb.create_batch()` – Transactional batch writes across collections.

The SDK exposes the same filter builder (`pb.filter()`), `before_send` / `after_send` hooks,
and auth store semantics as the other SDKs, so existing examples port to Python with minimal changes.

## Documentation

The `docs/` directory mirrors the JavaScript SDK guides, adapted for Python. Highlights:

- `COLLECTIONS.md`: collection types, scaffolds, schema queries.
- `API_RECORDS.md`: CRUD, batch operations, auth helpers.
- `REALTIME.md`: realtime subscriptions, connection lifecycle.
- `FILES.md`, `FILE_API.md`: uploads, tokens, download URLs.
- `LANGCHAINGO_API.md`, `LLM_DOCUMENTS.md`, `VECTOR_API.md`: AI and RAG workflows.
- `SQL_EXECUTION_API.md`, `SQL_TABLE_REGISTRATION.md`: superuser SQL workflows and mapping existing tables to collections.

Every topic from the JS SDK now has a Python-specific counterpart with code samples.

See `SDK_DOCUMENTATION.md` in the repo for feature-specific guides.
