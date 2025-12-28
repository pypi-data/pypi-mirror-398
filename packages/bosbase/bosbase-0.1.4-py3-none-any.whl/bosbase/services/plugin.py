"""Plugin proxy helpers."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional, Sequence
from urllib.parse import urlparse, urlunparse

import requests
# websocket-client is optional; import lazily in _open_websocket to avoid hard dependency at import time.

# Local user agent to avoid circular import with client -> services
USER_AGENT = "bosbase-python-sdk"
from ..utils import normalize_query_params
from .base import BaseService

_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
_SSE_METHODS = {"SSE"}
_WS_METHODS = {"WS", "WEBSOCKET"}
_ALLOWED_METHODS = _HTTP_METHODS | _SSE_METHODS | _WS_METHODS


class PluginSSEStream:
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


class PluginService(BaseService):
    """Forward requests to configured plugins."""

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
        body: Optional[Any] = None,
        files: Optional[Any] = None,
        websocket_protocols: Optional[Sequence[str]] = None,
    ):
        normalized_method = (method or "").upper()
        if normalized_method not in _ALLOWED_METHODS:
            raise ValueError(f"Unsupported plugin method {method!r}")

        normalized_path = self._normalize_path(path)
        merged_query = self._merge_query(path, query)

        if normalized_method in _SSE_METHODS:
            return self._open_sse(normalized_path, merged_query, headers=headers)

        if normalized_method in _WS_METHODS:
            return self._open_websocket(
                normalized_path,
                merged_query,
                headers=headers,
                protocols=websocket_protocols,
            )

        return self.client.send(
            normalized_path,
            method=normalized_method,
            query=merged_query,
            headers=headers,
            body=body,
            files=files,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _normalize_path(self, path: str) -> str:
        trimmed = (path or "").strip()
        if not trimmed:
            return "/api/plugins"

        # strip leading slashes to avoid double "//"
        while trimmed.startswith("/"):
            trimmed = trimmed[1:]

        # preserve inline query for later merge
        clean_path = trimmed.split("?", 1)[0]

        if clean_path.startswith("api/plugins"):
            return f"/{clean_path}"

        return f"/api/plugins/{clean_path}"

    def _merge_query(
        self, path: str, extra: Optional[Mapping[str, Any]]
    ) -> Mapping[str, Any]:
        merged: dict[str, Any] = dict(extra or {})
        if "?" not in path:
            return merged

        inline = path.split("?", 1)[1]
        try:
            inline_pairs = normalize_query_params(
                dict(item.split("=", 1) for item in inline.split("&") if item)
            )
        except Exception:
            inline_pairs = {}

        for key, values in inline_pairs.items():
            if key not in merged:
                merged[key] = values if len(values) > 1 else values[0]

        return merged

    def _build_url(self, path: str, query: Optional[Mapping[str, Any]]) -> str:
        enriched = dict(query or {})
        if self.client.auth_store.token:
            enriched.setdefault("token", self.client.auth_store.token)
        return self.client.build_url(path, enriched)

    def _open_sse(
        self,
        path: str,
        query: Optional[Mapping[str, Any]],
        *,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> PluginSSEStream:
        url = self._build_url(path, query)
        req_headers: dict[str, str] = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-store",
            "Accept-Language": self.client.lang,
            "User-Agent": USER_AGENT,
        }
        if headers:
            req_headers.update(headers)

        if "Authorization" not in req_headers and self.client.auth_store.token:
            req_headers["Authorization"] = self.client.auth_store.token

        response = requests.get(
            url,
            stream=True,
            headers=req_headers,
            timeout=(10, 60),
        )
        response.raise_for_status()
        return PluginSSEStream(response)

    def _open_websocket(
        self,
        path: str,
        query: Optional[Mapping[str, Any]],
        *,
        headers: Optional[Mapping[str, str]] = None,
        protocols: Optional[Sequence[str]] = None,
    ):
        url = self._build_url(path, query)
        parsed = urlparse(url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        ws_url = urlunparse(parsed._replace(scheme=scheme))

        header_list: list[str] = []
        if headers:
            header_list = [f"{k}: {v}" for k, v in headers.items()]

        from websocket import create_connection  # type: ignore

        return create_connection(ws_url, header=header_list, subprotocols=protocols)
