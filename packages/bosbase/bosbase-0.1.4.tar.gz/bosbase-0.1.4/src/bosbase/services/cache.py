"""Cache APIs."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from .base import BaseService
from ..utils import encode_path_segment


class CacheService(BaseService):
    def list(
        self,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> list[dict]:
        data = self.client.send("/api/cache", query=query, headers=headers)
        return list(data.get("items", []) if isinstance(data, dict) else data or [])

    def create(
        self,
        name: str,
        *,
        size_bytes: Optional[int] = None,
        default_ttl_seconds: Optional[int] = None,
        read_timeout_ms: Optional[int] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        payload = dict(body or {})
        payload["name"] = name
        if size_bytes is not None:
            payload["sizeBytes"] = size_bytes
        if default_ttl_seconds is not None:
            payload["defaultTTLSeconds"] = default_ttl_seconds
        if read_timeout_ms is not None:
            payload["readTimeoutMs"] = read_timeout_ms

        return self.client.send(
            "/api/cache",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def update(
        self,
        name: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        return self.client.send(
            f"/api/cache/{encode_path_segment(name)}",
            method="PATCH",
            body=body,
            query=query,
            headers=headers,
        )

    def delete(
        self,
        name: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            f"/api/cache/{encode_path_segment(name)}",
            method="DELETE",
            query=query,
            headers=headers,
        )

    def set_entry(
        self,
        cache: str,
        key: str,
        value: Any,
        *,
        ttl_seconds: Optional[int] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        payload = dict(body or {})
        payload["value"] = value
        if ttl_seconds is not None:
            payload["ttlSeconds"] = ttl_seconds
        return self.client.send(
            f"/api/cache/{encode_path_segment(cache)}/entries/{encode_path_segment(key)}",
            method="PUT",
            body=payload,
            query=query,
            headers=headers,
        )

    def get_entry(
        self,
        cache: str,
        key: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        return self.client.send(
            f"/api/cache/{encode_path_segment(cache)}/entries/{encode_path_segment(key)}",
            query=query,
            headers=headers,
        )

    def renew_entry(
        self,
        cache: str,
        key: str,
        *,
        ttl_seconds: Optional[int] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        payload = dict(body or {})
        if ttl_seconds is not None:
            payload["ttlSeconds"] = ttl_seconds
        return self.client.send(
            f"/api/cache/{encode_path_segment(cache)}/entries/{encode_path_segment(key)}",
            method="PATCH",
            body=payload,
            query=query,
            headers=headers,
        )

    def delete_entry(
        self,
        cache: str,
        key: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            f"/api/cache/{encode_path_segment(cache)}/entries/{encode_path_segment(key)}",
            method="DELETE",
            query=query,
            headers=headers,
        )
