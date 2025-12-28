# Vector API - Python SDK

Vector collections store embeddings for similarity search, hybrid retrieval, and recommendation features.

```python
from bosbase import (
    VectorDocument,
    VectorBatchInsertOptions,
    VectorSearchOptions,
    VectorCollectionConfig,
)

vectors = pb.vectors
```

## Collections

```python
vectors.create_collection(
    "kb_vectors",
    VectorCollectionConfig(dimension=384, distance="cosine"),
)

collections = vectors.list_collections()
vectors.update_collection("kb_vectors", VectorCollectionConfig(distance="dot"))
vectors.delete_collection("old_vectors")
```

## Insert Documents

```python
doc = VectorDocument(
    vector=[0.1, 0.2, 0.3],
    metadata={"article": "123"},
    content="Reset your password from settings.",
)

vectors.insert(doc, collection="kb_vectors")
```

Batch insert:

```python
batch = VectorBatchInsertOptions(
    documents=[
        VectorDocument(vector=[0.1, 0.2], metadata={"id": "a"}),
        VectorDocument(vector=[0.5, 0.7], metadata={"id": "b"}),
    ],
    skip_duplicates=True,
)

vectors.batch_insert(batch, collection="kb_vectors")
```

## Search

```python
search = vectors.search(
    VectorSearchOptions(
        query_vector=[0.1, 0.2, 0.3],
        limit=5,
        filter={"article": "123"},
        include_content=True,
    ),
    collection="kb_vectors",
)

for result in search.results:
    print(result.document.metadata, result.score)
```

## Update / Delete / Get

```python
vectors.update("DOC_ID", doc, collection="kb_vectors")
vectors.delete("DOC_ID", collection="kb_vectors")
vectors.get("DOC_ID", collection="kb_vectors")
```

## Tips

1. Keep metadata minimal—use plain dicts that can be serialized to JSON.
2. Use `skip_duplicates` during ingestion to make the batch idempotent.
3. Store the original text in `content` to avoid round-trips for display.
4. When combining with LangChaingo RAG, keep collection names consistent between the two services.
