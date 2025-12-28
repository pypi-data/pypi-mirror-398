"""LLM document storage API."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from .. import types as sdk_types
from ..utils import encode_path_segment
from .base import BaseService


class LLMDocumentService(BaseService):
    base_path = "/api/llm-documents"

    def _collection_path(self, collection: str) -> str:
        return f"{self.base_path}/{encode_path_segment(collection)}"

    def list_collections(
        self,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> list[dict]:
        data = self.client.send(
            f"{self.base_path}/collections",
            query=query,
            headers=headers,
        )
        return list(data or [])

    def create_collection(
        self,
        name: str,
        *,
        metadata: Optional[Mapping[str, str]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            f"{self.base_path}/collections/{encode_path_segment(name)}",
            method="POST",
            body={"metadata": metadata},
            query=query,
            headers=headers,
        )

    def delete_collection(
        self,
        name: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            f"{self.base_path}/collections/{encode_path_segment(name)}",
            method="DELETE",
            query=query,
            headers=headers,
        )

    def insert(
        self,
        collection: str,
        document: sdk_types.LLMDocument,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        return self.client.send(
            self._collection_path(collection),
            method="POST",
            body=document.to_dict(),
            query=query,
            headers=headers,
        )

    def get(
        self,
        collection: str,
        document_id: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> sdk_types.LLMDocument:
        data = self.client.send(
            f"{self._collection_path(collection)}/{encode_path_segment(document_id)}",
            query=query,
            headers=headers,
        )
        return sdk_types.LLMDocument.from_dict(data)

    def update(
        self,
        collection: str,
        document_id: str,
        document: sdk_types.LLMDocumentUpdate,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        return self.client.send(
            f"{self._collection_path(collection)}/{encode_path_segment(document_id)}",
            method="PATCH",
            body=document.to_dict(),
            query=query,
            headers=headers,
        )

    def delete(
        self,
        collection: str,
        document_id: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            f"{self._collection_path(collection)}/{encode_path_segment(document_id)}",
            method="DELETE",
            query=query,
            headers=headers,
        )

    def list(
        self,
        collection: str,
        *,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        params = dict(query or {})
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["perPage"] = per_page
        return self.client.send(
            self._collection_path(collection),
            query=params,
            headers=headers,
        )

    def query(
        self,
        collection: str,
        options: sdk_types.LLMQueryOptions,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        return self.client.send(
            f"{self._collection_path(collection)}/documents/query",
            method="POST",
            body=options.to_dict(),
            query=query,
            headers=headers,
        )
