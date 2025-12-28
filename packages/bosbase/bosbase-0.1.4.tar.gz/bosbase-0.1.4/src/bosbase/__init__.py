"""BosBase Python SDK public API."""

from .auth import AuthStore, AsyncAuthStore, BaseAuthStore, LocalAuthStore
from .client import BosBase
from .exceptions import ClientResponseError
from .types import (
    LangChaingoCompletionMessage,
    LangChaingoCompletionRequest,
    LangChaingoCompletionResponse,
    LangChaingoDocumentQueryRequest,
    LangChaingoDocumentQueryResponse,
    LangChaingoModelConfig,
    LangChaingoRAGFilters,
    LangChaingoRAGRequest,
    LangChaingoRAGResponse,
    LangChaingoSourceDocument,
    LangChaingoSQLRequest,
    LangChaingoSQLResponse,
    LangChaingoToolCall,
    LLMDocument,
    LLMDocumentUpdate,
    LLMQueryOptions,
    LLMQueryResult,
    SQLExecuteResponse,
    VectorBatchInsertOptions,
    VectorBatchInsertResponse,
    VectorCollectionConfig,
    VectorCollectionInfo,
    VectorDocument,
    VectorInsertResponse,
    VectorSearchOptions,
    VectorSearchResponse,
    VectorSearchResult,
)

__all__ = [
    "AuthStore",
    "BaseAuthStore",
    "LocalAuthStore",
    "AsyncAuthStore",
    "BosBase",
    "ClientResponseError",
    # vector helpers
    "VectorDocument",
    "VectorSearchOptions",
    "VectorSearchResponse",
    "VectorSearchResult",
    "VectorInsertResponse",
    "VectorBatchInsertOptions",
    "VectorBatchInsertResponse",
    "VectorCollectionConfig",
    "VectorCollectionInfo",
    # LangChaingo helpers
    "LangChaingoModelConfig",
    "LangChaingoCompletionMessage",
    "LangChaingoCompletionRequest",
    "LangChaingoCompletionResponse",
    "LangChaingoToolCall",
    "LangChaingoRAGFilters",
    "LangChaingoRAGRequest",
    "LangChaingoRAGResponse",
    "LangChaingoSourceDocument",
    "LangChaingoDocumentQueryRequest",
    "LangChaingoDocumentQueryResponse",
    "LangChaingoSQLRequest",
    "LangChaingoSQLResponse",
    # LLM helpers
    "LLMDocument",
    "LLMDocumentUpdate",
    "LLMQueryOptions",
    "LLMQueryResult",
    # SQL helpers
    "SQLExecuteResponse",
]
