"""File service wrapper."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from .base import BaseService
from ..utils import encode_path_segment


class FileService(BaseService):
    def get_url(
        self,
        record: Mapping[str, Any],
        filename: str,
        *,
        thumb: Optional[str] = None,
        token: Optional[str] = None,
        download: Optional[bool] = None,
        query: Optional[Mapping[str, Any]] = None,
    ) -> str:
        record_id = record.get("id") or ""
        if not record_id or not filename:
            return ""
        collection = record.get("collectionId") or record.get("collectionName") or ""

        params = dict(query or {})
        if thumb is not None:
            params.setdefault("thumb", thumb)
        if token is not None:
            params.setdefault("token", token)
        if download:
            params["download"] = ""

        return self.client.build_url(
            f"/api/files/{encode_path_segment(collection)}/{encode_path_segment(record_id)}/{encode_path_segment(filename)}",
            params,
        )

    def get_token(
        self,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> str:
        data = self.client.send(
            "/api/files/token",
            method="POST",
            body=body,
            query=query,
            headers=headers,
        )
        return data.get("token", "")
