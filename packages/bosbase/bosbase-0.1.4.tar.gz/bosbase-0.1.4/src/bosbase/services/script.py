"""Script management APIs."""

from __future__ import annotations

import io
import os
from typing import Any, Mapping, MutableMapping, Optional, Sequence
from urllib.parse import urlparse, urlunparse

import requests

from .base import BaseService
from ..utils import encode_path_segment


class ScriptSSEStream:
    """Simple SSE wrapper that yields raw lines."""

    def __init__(self, response: requests.Response):
        self._response = response

    def __iter__(self):
        return self._response.iter_lines(decode_unicode=True, chunk_size=1)

    def close(self) -> None:
        try:
            self._response.close()
        except Exception:
            pass


class ScriptService(BaseService):
    """Manage and execute scripts (superuser only)."""

    def create(
        self,
        name: str,
        content: str,
        *,
        description: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        if not name or not name.strip():
            raise ValueError("script name is required")
        if not content or not content.strip():
            raise ValueError("script content is required")

        payload = dict(body or {})
        payload.setdefault("name", name.strip())
        payload.setdefault("content", content.strip())
        if description is not None:
            payload.setdefault("description", description)

        return self.client.send(
            "/api/scripts",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def command(
        self,
        command: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        if not command or not command.strip():
            raise ValueError("command is required")
        payload = dict(body or {})
        payload.setdefault("command", command.strip())
        return self.client.send(
            "/api/scripts/command",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def command_async(
        self,
        command: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        if not command or not command.strip():
            raise ValueError("command is required")
        payload = dict(body or {})
        payload.setdefault("command", command.strip())
        payload.setdefault("async", True)
        return self.client.send(
            "/api/scripts/command",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def command_status(
        self,
        job_id: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        if not job_id or not job_id.strip():
            raise ValueError("command id is required")
        return self.client.send(
            f"/api/scripts/command/{encode_path_segment(job_id.strip())}",
            query=query,
            headers=headers,
        )

    def upload(
        self,
        file: Any,
        *,
        path: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        if file is None:
            raise ValueError("file is required")

        payload = dict(body or {})
        if path:
            payload.setdefault("path", path)

        opened: Optional[Any] = None
        file_tuple = file

        if isinstance(file, (str, os.PathLike)):
            opened = open(file, "rb")
            filename = os.path.basename(str(file))
            file_tuple = (filename, opened, "application/octet-stream")
        elif isinstance(file, (bytes, bytearray)):
            opened = io.BytesIO(file)
            file_tuple = ("upload.bin", opened, "application/octet-stream")
        elif isinstance(file, tuple):
            file_tuple = file
        else:
            filename = os.path.basename(getattr(file, "name", "")) or "upload.bin"
            file_tuple = (filename, file, "application/octet-stream")

        try:
            return self.client.send(
                "/api/scripts/upload",
                method="POST",
                body=payload,
                query=query,
                headers=headers,
                files={"file": file_tuple},
            )
        finally:
            if opened is not None:
                try:
                    opened.close()
                except Exception:
                    pass

    def get(
        self,
        name: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        normalized = self._normalize_name(name)
        return self.client.send(
            f"/api/scripts/{encode_path_segment(normalized)}",
            query=query,
            headers=headers,
        )

    def list(
        self,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> list[dict]:
        data = self.client.send("/api/scripts", query=query, headers=headers)
        items = data.get("items", []) if isinstance(data, dict) else data or []
        return list(items)

    def update(
        self,
        name: str,
        *,
        content: Optional[str] = None,
        description: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        if content is None and description is None:
            raise ValueError("content or description must be provided")
        normalized = self._normalize_name(name)
        payload = dict(body or {})
        if content is not None:
            payload["content"] = content
        if description is not None:
            payload["description"] = description

        return self.client.send(
            f"/api/scripts/{encode_path_segment(normalized)}",
            method="PATCH",
            body=payload,
            query=query,
            headers=headers,
        )

    def execute(
        self,
        name: str,
        *,
        arguments: Optional[Sequence[Any]] = None,
        function_name: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        normalized = self._normalize_name(name)
        payload = dict(body or {})
        if arguments is not None:
            payload["arguments"] = [
                str(arg) if not isinstance(arg, str) else arg for arg in arguments
            ]
        if function_name is not None:
            payload["function_name"] = function_name
        return self.client.send(
            f"/api/scripts/{encode_path_segment(normalized)}/execute",
            method="POST",
            body=payload or None,
            query=query,
            headers=headers,
        )

    def execute_sse(
        self,
        name: str,
        *,
        arguments: Optional[Sequence[Any]] = None,
        function_name: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> ScriptSSEStream:
        normalized = self._normalize_name(name)
        url = self._build_execute_url(
            f"/api/scripts/{encode_path_segment(normalized)}/execute/sse",
            arguments=arguments,
            function_name=function_name,
            query=query,
            include_token=True,
        )
        req_headers: dict[str, str] = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-store",
            "Accept-Language": self.client.lang,
            "User-Agent": "bosbase-python-sdk",
        }
        if headers:
            req_headers.update(headers)
        if "Authorization" not in req_headers and self.client.auth_store.token:
            req_headers["Authorization"] = self.client.auth_store.token

        response = requests.get(url, stream=True, headers=req_headers, timeout=(10, 60))
        response.raise_for_status()
        return ScriptSSEStream(response)

    def execute_websocket(
        self,
        name: str,
        *,
        arguments: Optional[Sequence[Any]] = None,
        function_name: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
        websocket_protocols: Optional[Sequence[str]] = None,
    ):
        normalized = self._normalize_name(name)
        url = self._build_execute_url(
            f"/api/scripts/{encode_path_segment(normalized)}/execute/ws",
            arguments=arguments,
            function_name=function_name,
            query=query,
            include_token=True,
        )
        parsed = urlparse(url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        ws_url = urlunparse(parsed._replace(scheme=scheme))

        header_list: list[str] = []
        if headers:
            header_list = [f"{k}: {v}" for k, v in headers.items()]

        from websocket import create_connection  # type: ignore

        return create_connection(ws_url, header=header_list, subprotocols=websocket_protocols)

    def execute_async(
        self,
        name: str,
        *,
        arguments: Optional[Sequence[Any]] = None,
        function_name: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        normalized = self._normalize_name(name)
        payload = dict(body or {})
        if arguments is not None:
            payload["arguments"] = [
                str(arg) if not isinstance(arg, str) else arg for arg in arguments
            ]
        if function_name is not None:
            payload["function_name"] = function_name
        return self.client.send(
            f"/api/scripts/async/{encode_path_segment(normalized)}/execute",
            method="POST",
            body=payload or None,
            query=query,
            headers=headers,
        )

    def execute_async_status(
        self,
        job_id: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        if not job_id or not job_id.strip():
            raise ValueError("execution job id is required")
        return self.client.send(
            f"/api/scripts/async/{encode_path_segment(job_id.strip())}",
            query=query,
            headers=headers,
        )

    def wasm(
        self,
        options: str,
        wasm_name: str,
        *,
        params: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        if not wasm_name or not wasm_name.strip():
            raise ValueError("wasm name is required")
        payload = dict(body or {})
        payload.setdefault("options", (options or "").strip())
        payload.setdefault("wasm", wasm_name.strip())
        payload.setdefault("params", (params or "").strip())
        return self.client.send(
            "/api/scripts/wasm",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def wasm_async(
        self,
        options: str,
        wasm_name: str,
        *,
        params: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        if not wasm_name or not wasm_name.strip():
            raise ValueError("wasm name is required")
        payload = dict(body or {})
        payload.setdefault("options", (options or "").strip())
        payload.setdefault("wasm", wasm_name.strip())
        payload.setdefault("params", (params or "").strip())
        return self.client.send(
            "/api/scripts/wasm/async",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def wasm_async_status(
        self,
        job_id: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        if not job_id or not job_id.strip():
            raise ValueError("wasm execution job id is required")
        return self.client.send(
            f"/api/scripts/wasm/async/{encode_path_segment(job_id.strip())}",
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
        normalized = self._normalize_name(name)
        self.client.send(
            f"/api/scripts/{encode_path_segment(normalized)}",
            method="DELETE",
            query=query,
            headers=headers,
        )

    def _normalize_name(self, name: str) -> str:
        if not name or not name.strip():
            raise ValueError("script name is required")
        return name.strip()

    def _build_execute_url(
        self,
        path: str,
        *,
        arguments: Optional[Sequence[Any]] = None,
        function_name: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        include_token: bool = False,
    ) -> str:
        params = dict(query or {})
        if arguments:
            params["arguments"] = [
                str(arg) if not isinstance(arg, str) else arg for arg in arguments
            ]
        if function_name:
            params["function_name"] = function_name
        if include_token and self.client.auth_store.token:
            params.setdefault("token", self.client.auth_store.token)
        return self.client.build_url(path, params)
