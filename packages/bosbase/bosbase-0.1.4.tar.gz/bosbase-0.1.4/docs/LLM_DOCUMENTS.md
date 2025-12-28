# LLM Documents - Python SDK

LLM Documents store text chunks plus optional embeddings for use with RAG, search, or custom ML pipelines.

```python
from bosbase import LLMDocument, LLMDocumentUpdate, LLMQueryOptions

docs = pb.llm_documents
```

## Collections

```python
docs.create_collection("kb", metadata={"tenant": "default"})
collections = docs.list_collections()
docs.delete_collection("old_kb")
```

## Insert & Retrieve

```python
doc = docs.insert(
    "kb",
    LLMDocument(
        content="Reset your password from Settings → Account.",
        metadata={"category": "auth"},
        embedding=[0.12, 0.93, ...],  # optional
    ),
)

fetched = docs.get("kb", doc["id"])
```

## Update & Delete

```python
docs.update(
    "kb",
    doc["id"],
    LLMDocumentUpdate(content="Updated instructions", metadata={"category": "security"}),
)

docs.delete("kb", doc["id"])
```

## Listing Documents

```python
page = docs.list("kb", page=1, per_page=100)
```

## Querying

```python
matches = docs.query(
    "kb",
    LLMQueryOptions(
        query_text="reset password",
        limit=5,
        where={"category": "auth"},
    ),
)

for item in matches["items"]:
    print(item["content"], item["similarity"])
```

## Tips

1. Use deterministic IDs when you want to upsert documents repeatedly.
2. Store metadata that helps you filter—e.g. `tenant`, `locale`, `product`.
3. Combine LLM documents with the LangChaingo RAG endpoint for end‑to‑end chatbots.
