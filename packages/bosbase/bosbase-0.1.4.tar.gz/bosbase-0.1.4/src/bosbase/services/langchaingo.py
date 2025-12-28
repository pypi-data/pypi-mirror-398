"""LangChaingo API."""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .. import types as sdk_types
from .base import BaseService


class LangChaingoService(BaseService):
    base_path = "/api/langchaingo"

    def completions(
        self,
        payload: sdk_types.LangChaingoCompletionRequest,
        *,
        query: Optional[Mapping[str, str]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> sdk_types.LangChaingoCompletionResponse:
        data = self.client.send(
            f"{self.base_path}/completions",
            method="POST",
            body=payload.to_dict(),
            query=query,
            headers=headers,
        )
        return sdk_types.LangChaingoCompletionResponse.from_dict(data)

    def rag(
        self,
        payload: sdk_types.LangChaingoRAGRequest,
        *,
        query: Optional[Mapping[str, str]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> sdk_types.LangChaingoRAGResponse:
        data = self.client.send(
            f"{self.base_path}/rag",
            method="POST",
            body=payload.to_dict(),
            query=query,
            headers=headers,
        )
        return sdk_types.LangChaingoRAGResponse.from_dict(data)

    def query_documents(
        self,
        payload: sdk_types.LangChaingoDocumentQueryRequest,
        *,
        query: Optional[Mapping[str, str]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> sdk_types.LangChaingoDocumentQueryResponse:
        data = self.client.send(
            f"{self.base_path}/documents/query",
            method="POST",
            body=payload.to_dict(),
            query=query,
            headers=headers,
        )
        return sdk_types.LangChaingoDocumentQueryResponse.from_dict(data)

    def sql(
        self,
        payload: sdk_types.LangChaingoSQLRequest,
        *,
        query: Optional[Mapping[str, str]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> sdk_types.LangChaingoSQLResponse:
        data = self.client.send(
            f"{self.base_path}/sql",
            method="POST",
            body=payload.to_dict(),
            query=query,
            headers=headers,
        )
        return sdk_types.LangChaingoSQLResponse.from_dict(data)
