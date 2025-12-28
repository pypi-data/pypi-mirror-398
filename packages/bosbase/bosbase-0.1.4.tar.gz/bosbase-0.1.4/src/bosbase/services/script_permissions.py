"""Script permission APIs."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from .base import BaseService
from ..utils import encode_path_segment


class ScriptPermissionsService(BaseService):
    """Manage script execution permissions (superuser only)."""

    def create(
        self,
        *,
        script_name: str,
        content: str,
        script_id: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        payload = dict(body or {})
        payload.setdefault("script_name", self._normalize_name(script_name))
        payload.setdefault("content", content.strip() if content else "")
        if script_id:
            payload.setdefault("script_id", script_id.strip())
        if not payload["content"]:
            raise ValueError("content is required")
        return self.client.send(
            "/api/script-permissions",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def get(
        self,
        script_name: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        normalized = self._normalize_name(script_name)
        return self.client.send(
            f"/api/script-permissions/{encode_path_segment(normalized)}",
            query=query,
            headers=headers,
        )

    def update(
        self,
        script_name: str,
        *,
        content: Optional[str] = None,
        script_id: Optional[str] = None,
        new_script_name: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        normalized = self._normalize_name(script_name)
        payload = dict(body or {})
        if content is not None:
            payload["content"] = content.strip()
        if script_id is not None:
            payload["script_id"] = script_id.strip()
        if new_script_name is not None:
            payload["script_name"] = self._normalize_name(new_script_name)

        return self.client.send(
            f"/api/script-permissions/{encode_path_segment(normalized)}",
            method="PATCH",
            body=payload,
            query=query,
            headers=headers,
        )

    def delete(
        self,
        script_name: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        normalized = self._normalize_name(script_name)
        self.client.send(
            f"/api/script-permissions/{encode_path_segment(normalized)}",
            method="DELETE",
            query=query,
            headers=headers,
        )

    def _normalize_name(self, name: str) -> str:
        if not name or not name.strip():
            raise ValueError("scriptName is required")
        return name.strip()
