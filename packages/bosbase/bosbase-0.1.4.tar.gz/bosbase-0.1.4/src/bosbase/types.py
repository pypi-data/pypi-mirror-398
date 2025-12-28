"""Typed helpers for rich BosBase payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Vector helpers
# ---------------------------------------------------------------------------


@dataclass
class VectorDocument:
    vector: List[float]
    id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"vector": self.vector}
        if self.id is not None:
            payload["id"] = self.id
        if self.metadata is not None:
            payload["metadata"] = self.metadata
        if self.content is not None:
            payload["content"] = self.content
        return payload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorDocument":
        return cls(
            id=data.get("id"),
            vector=[float(x) for x in data.get("vector", [])],
            metadata=data.get("metadata"),
            content=data.get("content"),
        )


@dataclass
class VectorSearchOptions:
    query_vector: List[float]
    limit: Optional[int] = None
    filter: Optional[Dict[str, Any]] = None
    min_score: Optional[float] = None
    max_distance: Optional[float] = None
    include_distance: Optional[bool] = None
    include_content: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"queryVector": self.query_vector}
        if self.limit is not None:
            payload["limit"] = self.limit
        if self.filter is not None:
            payload["filter"] = self.filter
        if self.min_score is not None:
            payload["minScore"] = self.min_score
        if self.max_distance is not None:
            payload["maxDistance"] = self.max_distance
        if self.include_distance is not None:
            payload["includeDistance"] = self.include_distance
        if self.include_content is not None:
            payload["includeContent"] = self.include_content
        return payload


@dataclass
class VectorSearchResult:
    document: VectorDocument
    score: float
    distance: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorSearchResult":
        return cls(
            document=VectorDocument.from_dict(data.get("document", {})),
            score=float(data.get("score", 0)),
            distance=(
                float(data["distance"]) if data.get("distance") is not None else None
            ),
        )


@dataclass
class VectorSearchResponse:
    results: List[VectorSearchResult]
    total_matches: Optional[int] = None
    query_time: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorSearchResponse":
        return cls(
            results=[
                VectorSearchResult.from_dict(item)
                for item in data.get("results", []) or []
            ],
            total_matches=data.get("totalMatches"),
            query_time=data.get("queryTime"),
        )


@dataclass
class VectorBatchInsertOptions:
    documents: List[VectorDocument]
    skip_duplicates: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "documents": [doc.to_dict() for doc in self.documents]
        }
        if self.skip_duplicates is not None:
            payload["skipDuplicates"] = self.skip_duplicates
        return payload


@dataclass
class VectorInsertResponse:
    id: str
    success: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorInsertResponse":
        return cls(id=data.get("id", ""), success=bool(data.get("success", False)))


@dataclass
class VectorBatchInsertResponse:
    inserted_count: int
    failed_count: int
    ids: List[str] = field(default_factory=list)
    errors: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorBatchInsertResponse":
        return cls(
            inserted_count=int(data.get("insertedCount", 0)),
            failed_count=int(data.get("failedCount", 0)),
            ids=[str(x) for x in data.get("ids", []) or []],
            errors=[str(x) for x in data.get("errors", [])] if data.get("errors") else None,
        )


@dataclass
class VectorCollectionConfig:
    dimension: Optional[int] = None
    distance: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if self.dimension is not None:
            payload["dimension"] = self.dimension
        if self.distance is not None:
            payload["distance"] = self.distance
        if self.options is not None:
            payload["options"] = self.options
        return payload


@dataclass
class VectorCollectionInfo:
    name: str
    count: Optional[int] = None
    dimension: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorCollectionInfo":
        return cls(
            name=data.get("name", ""),
            count=data.get("count"),
            dimension=data.get("dimension"),
        )


# ---------------------------------------------------------------------------
# LangChaingo types
# ---------------------------------------------------------------------------


@dataclass
class LangChaingoModelConfig:
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if self.provider is not None:
            payload["provider"] = self.provider
        if self.model is not None:
            payload["model"] = self.model
        if self.api_key is not None:
            payload["apiKey"] = self.api_key
        if self.base_url is not None:
            payload["baseUrl"] = self.base_url
        return payload


@dataclass
class LangChaingoCompletionMessage:
    content: str
    role: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {"content": self.content}
        if self.role is not None:
            payload["role"] = self.role
        return payload


@dataclass
class LangChaingoCompletionRequest:
    model: Optional[LangChaingoModelConfig] = None
    prompt: Optional[str] = None
    messages: Optional[List[LangChaingoCompletionMessage]] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    candidate_count: Optional[int] = None
    stop: Optional[List[str]] = None
    json_response: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if self.model:
            payload["model"] = self.model.to_dict()
        if self.prompt is not None:
            payload["prompt"] = self.prompt
        if self.messages is not None:
            payload["messages"] = [message.to_dict() for message in self.messages]
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        if self.max_tokens is not None:
            payload["maxTokens"] = self.max_tokens
        if self.top_p is not None:
            payload["topP"] = self.top_p
        if self.candidate_count is not None:
            payload["candidateCount"] = self.candidate_count
        if self.stop is not None:
            payload["stop"] = self.stop
        if self.json_response is not None:
            payload["json"] = self.json_response
        return payload


@dataclass
class LangChaingoFunctionCall:
    name: str
    arguments: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LangChaingoFunctionCall":
        return cls(name=data.get("name", ""), arguments=data.get("arguments", ""))


@dataclass
class LangChaingoToolCall:
    id: str
    type: str
    function_call: Optional[LangChaingoFunctionCall] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LangChaingoToolCall":
        func = data.get("functionCall")
        return cls(
            id=data.get("id", ""),
            type=data.get("type", ""),
            function_call=LangChaingoFunctionCall.from_dict(func)
            if isinstance(func, dict)
            else None,
        )


@dataclass
class LangChaingoCompletionResponse:
    content: str
    stop_reason: Optional[str] = None
    generation_info: Optional[Dict[str, Any]] = None
    function_call: Optional[LangChaingoFunctionCall] = None
    tool_calls: Optional[List[LangChaingoToolCall]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LangChaingoCompletionResponse":
        func = data.get("functionCall")
        return cls(
            content=data.get("content", ""),
            stop_reason=data.get("stopReason"),
            generation_info=data.get("generationInfo"),
            function_call=LangChaingoFunctionCall.from_dict(func)
            if isinstance(func, dict)
            else None,
            tool_calls=[
                LangChaingoToolCall.from_dict(item)
                for item in data.get("toolCalls", []) or []
            ]
            if data.get("toolCalls")
            else None,
        )


@dataclass
class LangChaingoRAGFilters:
    where: Optional[Dict[str, str]] = None
    where_document: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if self.where is not None:
            payload["where"] = self.where
        if self.where_document is not None:
            payload["whereDocument"] = self.where_document
        return payload


@dataclass
class LangChaingoRAGRequest:
    collection: str
    question: str
    model: Optional[LangChaingoModelConfig] = None
    top_k: Optional[int] = None
    score_threshold: Optional[float] = None
    filters: Optional[LangChaingoRAGFilters] = None
    prompt_template: Optional[str] = None
    return_sources: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "collection": self.collection,
            "question": self.question,
        }
        if self.model:
            payload["model"] = self.model.to_dict()
        if self.top_k is not None:
            payload["topK"] = self.top_k
        if self.score_threshold is not None:
            payload["scoreThreshold"] = self.score_threshold
        if self.filters is not None:
            payload["filters"] = self.filters.to_dict()
        if self.prompt_template is not None:
            payload["promptTemplate"] = self.prompt_template
        if self.return_sources is not None:
            payload["returnSources"] = self.return_sources
        return payload


@dataclass
class LangChaingoSourceDocument:
    content: str
    metadata: Optional[Dict[str, Any]] = None
    score: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LangChaingoSourceDocument":
        return cls(
            content=data.get("content", ""),
            metadata=data.get("metadata"),
            score=float(data["score"]) if data.get("score") is not None else None,
        )


@dataclass
class LangChaingoRAGResponse:
    answer: str
    sources: Optional[List[LangChaingoSourceDocument]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LangChaingoRAGResponse":
        return cls(
            answer=data.get("answer", ""),
            sources=[
                LangChaingoSourceDocument.from_dict(item)
                for item in data.get("sources", []) or []
            ]
            if data.get("sources")
            else None,
        )


@dataclass
class LangChaingoDocumentQueryRequest:
    collection: str
    query: str
    model: Optional[LangChaingoModelConfig] = None
    top_k: Optional[int] = None
    score_threshold: Optional[float] = None
    filters: Optional[LangChaingoRAGFilters] = None
    prompt_template: Optional[str] = None
    return_sources: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "collection": self.collection,
            "query": self.query,
        }
        if self.model:
            payload["model"] = self.model.to_dict()
        if self.top_k is not None:
            payload["topK"] = self.top_k
        if self.score_threshold is not None:
            payload["scoreThreshold"] = self.score_threshold
        if self.filters is not None:
            payload["filters"] = self.filters.to_dict()
        if self.prompt_template is not None:
            payload["promptTemplate"] = self.prompt_template
        if self.return_sources is not None:
            payload["returnSources"] = self.return_sources
        return payload


# DocumentQueryResponse is the same as RAGResponse
LangChaingoDocumentQueryResponse = LangChaingoRAGResponse


@dataclass
class LangChaingoSQLRequest:
    query: str
    model: Optional[LangChaingoModelConfig] = None
    tables: Optional[List[str]] = None
    top_k: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "query": self.query,
        }
        if self.model:
            payload["model"] = self.model.to_dict()
        if self.tables is not None:
            payload["tables"] = self.tables
        if self.top_k is not None:
            payload["topK"] = self.top_k
        return payload


@dataclass
class LangChaingoSQLResponse:
    sql: str
    answer: str
    columns: Optional[List[str]] = None
    rows: Optional[List[List[str]]] = None
    raw_result: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LangChaingoSQLResponse":
        rows_raw = data.get("rows")
        return cls(
            sql=data.get("sql", ""),
            answer=data.get("answer", ""),
            columns=data.get("columns"),
            rows=(
                [[str(cell) for cell in row] for row in rows_raw]
                if rows_raw is not None
                else None
            ),
            raw_result=data.get("rawResult"),
        )


# ---------------------------------------------------------------------------
# LLM document helpers
# ---------------------------------------------------------------------------


@dataclass
class LLMDocument:
    content: str
    id: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"content": self.content}
        if self.id is not None:
            payload["id"] = self.id
        if self.metadata is not None:
            payload["metadata"] = self.metadata
        if self.embedding is not None:
            payload["embedding"] = self.embedding
        return payload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMDocument":
        embedding_raw = data.get("embedding")
        return cls(
            id=data.get("id"),
            content=data.get("content", ""),
            metadata=data.get("metadata"),
            embedding=(
                [float(val) for val in embedding_raw] if isinstance(embedding_raw, list) else None
            ),
        )


@dataclass
class LLMDocumentUpdate:
    content: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if self.content is not None:
            payload["content"] = self.content
        if self.metadata is not None:
            payload["metadata"] = self.metadata
        if self.embedding is not None:
            payload["embedding"] = self.embedding
        return payload


@dataclass
class LLMQueryOptions:
    query_text: Optional[str] = None
    query_embedding: Optional[List[float]] = None
    limit: Optional[int] = None
    where: Optional[Dict[str, str]] = None
    negative: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if self.query_text is not None:
            payload["queryText"] = self.query_text
        if self.query_embedding is not None:
            payload["queryEmbedding"] = self.query_embedding
        if self.limit is not None:
            payload["limit"] = self.limit
        if self.where is not None:
            payload["where"] = self.where
        if self.negative is not None:
            payload["negative"] = self.negative
        return payload


@dataclass
class LLMQueryResult:
    id: str
    content: str
    metadata: Dict[str, str]
    similarity: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMQueryResult":
        metadata = data.get("metadata") or {}
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            metadata={str(k): str(v) for k, v in metadata.items()},
            similarity=float(data.get("similarity", 0)),
        )


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------


@dataclass
class SQLExecuteResponse:
    columns: Optional[List[str]] = None
    rows: Optional[List[List[str]]] = None
    rows_affected: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SQLExecuteResponse":
        rows_raw = data.get("rows")
        return cls(
            columns=[str(col) for col in data.get("columns", []) or []]
            if data.get("columns") is not None
            else None,
            rows=(
                [[str(cell) for cell in row] for row in rows_raw]
                if rows_raw is not None
                else None
            ),
            rows_affected=(
                int(data["rowsAffected"]) if data.get("rowsAffected") is not None else None
            ),
        )
