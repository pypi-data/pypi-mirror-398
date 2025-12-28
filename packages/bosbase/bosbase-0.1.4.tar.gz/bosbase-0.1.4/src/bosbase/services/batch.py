"""Transactional batch API."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional

from ..utils import ensure_file_tuples, to_serializable, build_relative_url, encode_path_segment
from .base import BaseService


class BatchService(BaseService):
    def __init__(self, client) -> None:
        super().__init__(client)
        self._requests: list[Dict[str, Any]] = []
        self._collections: dict[str, SubBatchService] = {}

    def collection(self, collection_id_or_name: str) -> "SubBatchService":
        if collection_id_or_name not in self._collections:
            self._collections[collection_id_or_name] = SubBatchService(
                self, collection_id_or_name
            )
        return self._collections[collection_id_or_name]

    def queue_request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[MutableMapping[str, str]] = None,
        body: Optional[Mapping[str, Any]] = None,
        files: Optional[Iterable[tuple[str, tuple[str, Any, str]]]] = None,
    ) -> None:
        self._requests.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers or {}),
                "body": to_serializable(body) if body is not None else {},
                "files": list(files or []),
            }
        )

    def send(
        self,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> list[dict]:
        requests_payload = []
        attachments = []

        for index, req in enumerate(self._requests):
            requests_payload.append(
                {
                    "method": req["method"],
                    "url": req["url"],
                    "headers": req["headers"],
                    "body": req["body"],
                }
            )
            for field, file_tuple in req["files"]:
                attachments.append((f"requests.{index}.{field}", file_tuple))

        payload = dict(body or {})
        payload["requests"] = requests_payload

        response = self.client.send(
            "/api/batch",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
            files=attachments or None,
        )

        self._requests.clear()
        return response or []


class SubBatchService:
    def __init__(self, batch: BatchService, collection_id_or_name: str) -> None:
        self._batch = batch
        self._collection = collection_id_or_name

    def _collection_url(self) -> str:
        encoded = encode_path_segment(self._collection)
        return f"/api/collections/{encoded}/records"

    def create(
        self,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        files: Optional[Any] = None,
        headers: Optional[MutableMapping[str, str]] = None,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
    ) -> None:
        params = dict(query or {})
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)
        url = build_relative_url(self._collection_url(), params)
        self._batch.queue_request(
            "POST",
            url,
            headers=headers,
            body=body,
            files=ensure_file_tuples(files),
        )

    def upsert(
        self,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        files: Optional[Any] = None,
        headers: Optional[MutableMapping[str, str]] = None,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
    ) -> None:
        params = dict(query or {})
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)
        url = build_relative_url(self._collection_url(), params)
        self._batch.queue_request(
            "PUT",
            url,
            headers=headers,
            body=body,
            files=ensure_file_tuples(files),
        )

    def update(
        self,
        record_id: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        files: Optional[Any] = None,
        headers: Optional[MutableMapping[str, str]] = None,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
    ) -> None:
        params = dict(query or {})
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)
        encoded_id = encode_path_segment(record_id)
        url = build_relative_url(f"{self._collection_url()}/{encoded_id}", params)
        self._batch.queue_request(
            "PATCH",
            url,
            headers=headers,
            body=body,
            files=ensure_file_tuples(files),
        )

    def delete(
        self,
        record_id: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        encoded_id = encode_path_segment(record_id)
        url = build_relative_url(f"{self._collection_url()}/{encoded_id}", query)
        self._batch.queue_request(
            "DELETE",
            url,
            headers=headers,
            body=body,
        )
