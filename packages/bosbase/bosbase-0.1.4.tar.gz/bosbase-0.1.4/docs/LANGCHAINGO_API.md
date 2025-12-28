# LangChaingo API - Python SDK

The LangChaingo service exposes completions and RAG workflows directly from BosBase.

## Completions

```python
from bosbase import (
    LangChaingoCompletionRequest,
    LangChaingoCompletionMessage,
    LangChaingoModelConfig,
)

req = LangChaingoCompletionRequest(
    model=LangChaingoModelConfig(provider="openai", model="gpt-4o-mini"),
    messages=[
        LangChaingoCompletionMessage(role="system", content="You are a release bot."),
        LangChaingoCompletionMessage(role="user", content="Summarize the changelog."),
    ],
    temperature=0.2,
)

resp = pb.langchaingo.completions(req)
print(resp.content)
```

The response includes optional tool/function call metadata if the provider returns it.

## RAG

```python
from bosbase import (
    LangChaingoRAGRequest,
    LangChaingoModelConfig,
    LangChaingoRAGFilters,
)

req = LangChaingoRAGRequest(
    collection="kb_articles",
    question="How do I reset my password?",
    top_k=5,
    score_threshold=0.6,
    filters=LangChaingoRAGFilters(where={"category": "auth"}),
    return_sources=True,
)

resp = pb.langchaingo.rag(req)
print(resp.answer)
for src in resp.sources or []:
    print(src.content, src.score)
```

### LLM Document Queries

> **Note**: This interface is only available to superusers.

When you want to pose a question to a specific `llmDocuments` collection and have LangChaingo+OpenAI synthesize an answer, use `query_documents`. It mirrors the RAG arguments but takes a `query` field:

```python
from bosbase import (
    LangChaingoDocumentQueryRequest,
    LangChaingoModelConfig,
    LangChaingoRAGFilters,
)

req = LangChaingoDocumentQueryRequest(
    collection="knowledge-base",
    query="List three bullet points about Rayleigh scattering.",
    top_k=3,
    return_sources=True,
)

resp = pb.langchaingo.query_documents(req)
print(resp.answer)
if resp.sources:
    for source in resp.sources:
        print(source.content, source.score)
```

### SQL Generation + Execution

> **Important Notes**:
> - This interface is only available to superusers. Requests authenticated with regular `users` tokens return a `401 Unauthorized`.
> - It is recommended to execute query statements (SELECT) only.
> - **Do not use this interface for adding or modifying table structures.** Collection interfaces should be used instead for managing database schema.
> - Directly using this interface for initializing table structures and adding or modifying database tables will cause errors that prevent the automatic generation of APIs.

Superuser tokens (`_superusers` records) can ask LangChaingo to have OpenAI propose a SQL statement, execute it, and return both the generated SQL and execution output.

```python
from bosbase import (
    LangChaingoSQLRequest,
    LangChaingoModelConfig,
)

req = LangChaingoSQLRequest(
    query="Add a demo project row if it doesn't exist, then list the 5 most recent projects.",
    tables=["projects"],  # optional hint to limit which tables the model sees
    top_k=5,
)

result = pb.langchaingo.sql(req)
print(result.sql)    # Generated SQL
print(result.answer) # Model's summary of the execution
print(result.columns, result.rows)
```

Use `tables` to restrict which table definitions and sample rows are passed to the model, and `top_k` to control how many rows the model should target when building queries. You can also pass the optional `model` block described above to override the default OpenAI model or key for this call.

## Tips

1. Configure provider credentials under *Settings → LangChaingo* before calling the API.
2. Embed documents via the Vector or LLM Document APIs to make them searchable by LangChaingo.
3. Always log prompt/response metadata when automating customer-facing workflows for traceability.
