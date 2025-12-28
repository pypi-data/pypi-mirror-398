"""Vector API helpers."""

from __future__ import annotations

from typing import Any, Dict, Mapping, MutableMapping, Optional, Union

from .. import types as sdk_types
from ..utils import encode_path_segment
from .base import BaseService


class VectorService(BaseService):
    base_path = "/api/vectors"

    def _collection_path(self, collection: Optional[str]) -> str:
        if collection:
            return f"{self.base_path}/{encode_path_segment(collection)}"
        return self.base_path

    def _normalize_document(
        self, document: Union[sdk_types.VectorDocument, Mapping[str, Any]]
    ) -> Dict[str, Any]:
        if isinstance(document, sdk_types.VectorDocument):
            return document.to_dict()
        if isinstance(document, Mapping):
            return dict(document)
        raise TypeError("document must be a VectorDocument or mapping")

    def _normalize_batch_options(
        self, options: Union[sdk_types.VectorBatchInsertOptions, Mapping[str, Any]]
    ) -> Dict[str, Any]:
        if isinstance(options, sdk_types.VectorBatchInsertOptions):
            return options.to_dict()
        if isinstance(options, Mapping):
            return dict(options)
        raise TypeError("options must be VectorBatchInsertOptions or mapping")

    def insert(
        self,
        document: Union[sdk_types.VectorDocument, Mapping[str, Any]],
        *,
        collection: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> sdk_types.VectorInsertResponse:
        data = self.client.send(
            self._collection_path(collection),
            method="POST",
            body=self._normalize_document(document),
            query=query,
            headers=headers,
        )
        return sdk_types.VectorInsertResponse.from_dict(data)

    def batch_insert(
        self,
        options: Union[sdk_types.VectorBatchInsertOptions, Mapping[str, Any]],
        *,
        collection: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> sdk_types.VectorBatchInsertResponse:
        data = self.client.send(
            f"{self._collection_path(collection)}/documents/batch",
            method="POST",
            body=self._normalize_batch_options(options),
            query=query,
            headers=headers,
        )
        return sdk_types.VectorBatchInsertResponse.from_dict(data)

    def update(
        self,
        document_id: str,
        document: Union[sdk_types.VectorDocument, Mapping[str, Any]],
        *,
        collection: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> sdk_types.VectorInsertResponse:
        data = self.client.send(
            f"{self._collection_path(collection)}/{encode_path_segment(document_id)}",
            method="PATCH",
            body=self._normalize_document(document),
            query=query,
            headers=headers,
        )
        return sdk_types.VectorInsertResponse.from_dict(data)

    def delete(
        self,
        document_id: str,
        *,
        collection: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            f"{self._collection_path(collection)}/{encode_path_segment(document_id)}",
            method="DELETE",
            body=body,
            query=query,
            headers=headers,
        )

    def search(
        self,
        options: sdk_types.VectorSearchOptions,
        *,
        collection: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> sdk_types.VectorSearchResponse:
        data = self.client.send(
            f"{self._collection_path(collection)}/documents/search",
            method="POST",
            body=options.to_dict(),
            query=query,
            headers=headers,
        )
        return sdk_types.VectorSearchResponse.from_dict(data)

    def get(
        self,
        document_id: str,
        *,
        collection: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> sdk_types.VectorDocument:
        data = self.client.send(
            f"{self._collection_path(collection)}/{encode_path_segment(document_id)}",
            query=query,
            headers=headers,
        )
        return sdk_types.VectorDocument.from_dict(data)

    def list(
        self,
        *,
        collection: Optional[str] = None,
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

    def create_collection(
        self,
        name: str,
        config: sdk_types.VectorCollectionConfig,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            f"{self.base_path}/collections/{encode_path_segment(name)}",
            method="POST",
            body=config.to_dict(),
            query=query,
            headers=headers,
        )

    def update_collection(
        self,
        name: str,
        config: sdk_types.VectorCollectionConfig,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            f"{self.base_path}/collections/{encode_path_segment(name)}",
            method="PATCH",
            body=config.to_dict(),
            query=query,
            headers=headers,
        )

    def delete_collection(
        self,
        name: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            f"{self.base_path}/collections/{encode_path_segment(name)}",
            method="DELETE",
            body=body,
            query=query,
            headers=headers,
        )

    def list_collections(
        self,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> list[sdk_types.VectorCollectionInfo]:
        data = self.client.send(
            f"{self.base_path}/collections",
            query=query,
            headers=headers,
        )
        return [
            sdk_types.VectorCollectionInfo.from_dict(item)
            for item in data or []
        ]
