"""Backup and restore service."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from .base import BaseService
from ..utils import encode_path_segment


class BackupService(BaseService):
    def get_full_list(
        self,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> list[dict]:
        data = self.client.send("/api/backups", query=query, headers=headers)
        return list(data or [])

    def create(
        self,
        name: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        payload = dict(body or {})
        payload.setdefault("name", name)
        self.client.send(
            "/api/backups",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def upload(
        self,
        files: Any,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            "/api/backups/upload",
            method="POST",
            body=body,
            query=query,
            headers=headers,
            files=files,
        )

    def delete(
        self,
        key: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            f"/api/backups/{encode_path_segment(key)}",
            method="DELETE",
            body=body,
            query=query,
            headers=headers,
        )

    def restore(
        self,
        key: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            f"/api/backups/{encode_path_segment(key)}/restore",
            method="POST",
            body=body,
            query=query,
            headers=headers,
        )

    def get_download_url(
        self,
        token: str,
        key: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
    ) -> str:
        params = dict(query or {})
        params.setdefault("token", token)
        return self.client.build_url(
            f"/api/backups/{encode_path_segment(key)}",
            params,
        )
