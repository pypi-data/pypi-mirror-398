"""Unit tests for BosBase service helpers."""

from __future__ import annotations

from typing import Any, Dict, Mapping, MutableMapping, Optional
from urllib.parse import parse_qs, urlparse, urlencode, urljoin

import bosbase.services.plugin as plugin_module
from bosbase.services.plugin import PluginService
from bosbase.services.redis import RedisService
from bosbase.services.script import ScriptService
from bosbase.services.script_permissions import ScriptPermissionsService


class FakeAuthStore:
    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or ""

    def is_valid(self) -> bool:
        return bool(self.token)


class FakeClient:
    def __init__(self, token: Optional[str] = None, lang: str = "en-US") -> None:
        self.base_url = "http://example.com"
        self.lang = lang
        self.auth_store = FakeAuthStore(token)
        self.sent: Dict[str, Any] = {}

    def build_url(self, path: str, query: Optional[Mapping[str, Any]] = None) -> str:
        base = self.base_url
        if not base.endswith("/"):
            base += "/"
        rel = path.lstrip("/")
        url = urljoin(base, rel)
        if query:
            pairs = []
            for key, value in query.items():
                if value is None:
                    continue
                if isinstance(value, (list, tuple)):
                    for item in value:
                        pairs.append((key, item))
                else:
                    pairs.append((key, value))
            if pairs:
                url = f"{url}?{urlencode(pairs)}"
        return url

    def send(
        self,
        path: str,
        *,
        method: str = "GET",
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
        body: Optional[Any] = None,
        files: Optional[Any] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        self.sent = {
            "path": path,
            "method": method,
            "query": dict(query or {}),
            "headers": dict(headers or {}),
            "body": body,
            "files": files,
            "timeout": timeout,
        }
        return {"ok": True, "query": self.sent["query"], "body": body}


def test_script_create_validates_required_fields():
    client = FakeClient()
    svc = ScriptService(client)
    try:
        svc.create("", "content")
        assert False, "expected ValueError for missing name"
    except ValueError:
        pass

    try:
        svc.create("name", "   ")
        assert False, "expected ValueError for missing content"
    except ValueError:
        pass


def test_script_update_requires_payload():
    client = FakeClient()
    svc = ScriptService(client)
    try:
        svc.update("demo")
        assert False, "expected ValueError when no content or description"
    except ValueError:
        pass


def test_script_permissions_validations():
    client = FakeClient()
    svc = ScriptPermissionsService(client)

    try:
        svc.create(script_name=" ", content="user")
        assert False, "expected ValueError for missing script name"
    except ValueError:
        pass

    try:
        svc.create(script_name="demo", content="  ")
        assert False, "expected ValueError for missing content"
    except ValueError:
        pass


def test_plugin_http_merges_inline_query():
    client = FakeClient()
    svc = PluginService(client)

    response = svc.request("GET", "custom/path?inline=1", query={"a": 1})
    assert client.sent["path"] == "/api/plugins/custom/path"
    assert client.sent["method"] == "GET"
    # inline query should merge when not overridden
    assert response["query"]["a"] == 1
    assert response["query"]["inline"] == "1"


def test_plugin_sse_includes_token_and_headers(monkeypatch):
    client = FakeClient(token="tkn")
    svc = PluginService(client)
    captured: Dict[str, Any] = {}

    class DummyResponse:
        def __init__(self, url: str, headers: Mapping[str, str]):
            self.url = url
            self.headers = headers

        def iter_lines(self, decode_unicode: bool, chunk_size: int):
            return iter([])

        def raise_for_status(self) -> None:
            return None

        def close(self) -> None:
            return None

    def fake_get(url: str, stream: bool, headers: Mapping[str, str], timeout):
        captured["url"] = url
        captured["headers"] = headers
        return DummyResponse(url, headers)

    monkeypatch.setattr(plugin_module.requests, "get", fake_get)

    stream = svc.request(
        "SSE",
        "/demo",
        query={"q": "1"},
        headers={"X-Test": "yes"},
    )
    assert stream is not None

    parsed = urlparse(captured["url"])
    params = parse_qs(parsed.query)
    assert params.get("token") == ["tkn"]
    assert params.get("q") == ["1"]
    assert captured["headers"]["Authorization"] == "tkn"
    assert captured["headers"]["X-Test"] == "yes"


def test_redis_create_key_sets_defaults():
    client = FakeClient()
    svc = RedisService(client)
    svc.create_key("demo", {"a": 1}, ttl_seconds=5)

    assert client.sent["path"] == "/api/redis/keys"
    assert client.sent["method"] == "POST"
    assert client.sent["body"]["key"] == "demo"
    assert client.sent["body"]["ttlSeconds"] == 5
