"""Redis helper APIs."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from .base import BaseService
from ..utils import encode_path_segment


class RedisService(BaseService):
    """Expose Redis key helpers."""

    def list_keys(
        self,
        *,
        cursor: Optional[str] = None,
        pattern: Optional[str] = None,
        count: Optional[int] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        merged = dict(query or {})
        if cursor is not None:
            merged["cursor"] = cursor
        if pattern is not None:
            merged["pattern"] = pattern
        if count is not None:
            merged["count"] = count

        return self.client.send("/api/redis/keys", query=merged, headers=headers)

    def create_key(
        self,
        key: str,
        value: Any,
        *,
        ttl_seconds: Optional[int] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        payload = dict(body or {})
        payload.setdefault("key", key)
        payload.setdefault("value", value)
        if ttl_seconds is not None:
            payload.setdefault("ttlSeconds", ttl_seconds)

        return self.client.send(
            "/api/redis/keys",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def get_key(
        self,
        key: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        return self.client.send(
            f"/api/redis/keys/{encode_path_segment(key)}",
            query=query,
            headers=headers,
        )

    def update_key(
        self,
        key: str,
        value: Any,
        *,
        ttl_seconds: Optional[int] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        payload = dict(body or {})
        payload.setdefault("value", value)
        if ttl_seconds is not None:
            payload.setdefault("ttlSeconds", ttl_seconds)

        return self.client.send(
            f"/api/redis/keys/{encode_path_segment(key)}",
            method="PUT",
            body=payload,
            query=query,
            headers=headers,
        )

    def delete_key(
        self,
        key: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            f"/api/redis/keys/{encode_path_segment(key)}",
            method="DELETE",
            query=query,
            headers=headers,
        )
