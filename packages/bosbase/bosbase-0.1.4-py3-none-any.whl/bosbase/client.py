"""BosBase HTTP client implementation."""

from __future__ import annotations

import json
import threading
import warnings
from typing import Any, Callable, Dict, List, Mapping, MutableMapping, Optional
from urllib.parse import urlencode, urljoin, urlparse

import requests

from .auth import AuthStore
from .exceptions import ClientResponseError
from .utils import ensure_file_tuples, normalize_query_params, to_serializable
from . import types as sdk_types  # re-exported dataclasses
from .services.backup import BackupService
from .services.batch import BatchService
from .services.cache import CacheService
from .services.collection import CollectionService
from .services.cron import CronService
from .services.file import FileService
from .services.health import HealthService
from .services.plugin import PluginService
from .services.langchaingo import LangChaingoService
from .services.llm_document import LLMDocumentService
from .services.log import LogService
from .services.graphql import GraphQLService
from .services.pubsub import PubSubService
from .services.record import RecordService
from .services.realtime import RealtimeService
from .services.redis import RedisService
from .services.settings import SettingsService
from .services.script import ScriptService
from .services.script_permissions import ScriptPermissionsService
from .services.sql import SQLService
from .services.vector import VectorService

USER_AGENT = "bosbase-python-sdk/0.1.0"


class BosBase:
    """Main entry point to the BosBase API."""

    def __init__(
        self,
        base_url: str,
        *,
        lang: str = "en-US",
        auth_store: Optional[AuthStore] = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/") or "/"
        self.lang = lang
        self.timeout = timeout
        self.auth_store = auth_store or AuthStore()
        self.before_send: Optional[
            Callable[[str, Dict[str, Any]], Optional[Dict[str, Any]]]
        ] = None
        self.after_send: Optional[Callable[[requests.Response, Any], Any]] = None

        self.collections = CollectionService(self)
        self.files = FileService(self)
        self.logs = LogService(self)
        self.realtime = RealtimeService(self)
        self.settings = SettingsService(self)
        self.health = HealthService(self)
        self.backups = BackupService(self)
        self.crons = CronService(self)
        self.vectors = VectorService(self)
        self.langchaingo = LangChaingoService(self)
        self.llm_documents = LLMDocumentService(self)
        self.caches = CacheService(self)
        self.plugins = PluginService(self)
        self.graphql = GraphQLService(self)
        self.redis = RedisService(self)
        self.scripts = ScriptService(self)
        self.scripts_permissions = ScriptPermissionsService(self)
        self.sql = SQLService(self)
        self.pubsub = PubSubService(self)

        self._record_services: Dict[str, RecordService] = {}
        self._lock = threading.RLock()
        self._cancel_lock = threading.RLock()
        self._cancel_tokens: Dict[str, threading.Event] = {}
        self._enable_auto_cancellation = True

    def __del__(self) -> None:  # pragma: no cover - best effort clean up
        try:
            self.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def close(self) -> None:
        self.realtime.disconnect()
        self.pubsub.disconnect()

    @property
    def admins(self) -> RecordService:
        warnings.warn(
            "BosBase.admins is deprecated; use collection('_superusers') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.collection("_superusers")

    def collection(self, collection_id_or_name: str) -> RecordService:
        with self._lock:
            if collection_id_or_name not in self._record_services:
                self._record_services[collection_id_or_name] = RecordService(
                    self, collection_id_or_name
                )
            return self._record_services[collection_id_or_name]

    def filter(self, expr: str, params: Optional[Mapping[str, Any]] = None) -> str:
        if not params:
            return expr
        for key, value in params.items():
            placeholder = "{:%s}" % key
            if isinstance(value, str):
                safe_val = value.replace("'", "\\'")
                expr = expr.replace(placeholder, f"'{safe_val}'")
            elif value is None:
                expr = expr.replace(placeholder, "null")
            elif isinstance(value, bool):
                expr = expr.replace(placeholder, "true" if value else "false")
            elif hasattr(value, "isoformat"):
                expr = expr.replace(
                    placeholder,
                    f"'{value.isoformat(sep=' ', timespec='seconds')}'",
                )
            else:
                try:
                    serialized = json.dumps(value, default=str)
                except TypeError:
                    serialized = json.dumps(str(value))
                escaped = serialized.replace("'", "\\'")
                expr = expr.replace(placeholder, "'" + escaped + "'")
        return expr

    def build_url(
        self, path: str, query: Optional[Mapping[str, Any]] = None
    ) -> str:
        base = self.base_url
        if not base.endswith("/"):
            base += "/"

        rel = path.lstrip("/")
        url = urljoin(base, rel)

        if query:
            normalized = normalize_query_params(query)
            if normalized:
                query_string = urlencode(normalized, doseq=True)
                separator = "&" if urlparse(url).query else "?"
                url = f"{url}{separator}{query_string}"

        return url

    def create_batch(self) -> BatchService:
        return BatchService(self)

    def auto_cancellation(self, enable: bool) -> "BosBase":
        self._enable_auto_cancellation = bool(enable)
        return self

    def cancel_request(self, request_key: str) -> "BosBase":
        if not request_key:
            return self
        with self._cancel_lock:
            token = self._cancel_tokens.pop(request_key, None)
        if token:
            token.set()
        return self

    def cancel_all_requests(self) -> "BosBase":
        with self._cancel_lock:
            tokens = list(self._cancel_tokens.values())
            self._cancel_tokens.clear()
        for token in tokens:
            token.set()
        return self

    def get_file_url(
        self,
        record: Mapping[str, Any],
        filename: str,
        *,
        thumb: Optional[str] = None,
        token: Optional[str] = None,
        download: Optional[bool] = None,
        query: Optional[Mapping[str, Any]] = None,
    ) -> str:
        return self.files.get_url(
            record,
            filename,
            thumb=thumb,
            token=token,
            download=download,
            query=query,
        )

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def send(
        self,
        path: str,
        *,
        method: str = "GET",
        headers: Optional[MutableMapping[str, str]] = None,
        query: Optional[Mapping[str, Any]] = None,
        body: Optional[Any] = None,
        files: Optional[Any] = None,
        timeout: Optional[float] = None,
        request_key: Optional[str] = None,
        auto_cancel: Optional[bool] = None,
    ) -> Any:
        cancel_event: Optional[threading.Event] = None
        cancel_key: Optional[str] = None
        if auto_cancel is None:
            auto_cancel = self._enable_auto_cancellation
        if auto_cancel or request_key is not None:
            cancel_key = request_key or f"{method.upper()}{path}"
            if cancel_key:
                cancel_event = threading.Event()
                with self._cancel_lock:
                    previous = self._cancel_tokens.get(cancel_key)
                    if previous and auto_cancel:
                        previous.set()
                    self._cancel_tokens[cancel_key] = cancel_event

        current_query = dict(query or {})
        url = self.build_url(path, current_query)

        req_headers: Dict[str, str] = {
            "Accept-Language": self.lang,
            "User-Agent": USER_AGENT,
        }
        if headers:
            req_headers.update(headers)
        if "Authorization" not in req_headers and self.auth_store.token:
            req_headers["Authorization"] = self.auth_store.token

        payload = to_serializable(body) if body is not None else None
        files_payload = files

        request_kwargs: Dict[str, Any] = {
            "method": method.upper(),
            "url": url,
            "timeout": timeout or self.timeout,
        }

        normalized_files = ensure_file_tuples(files_payload)
        if not normalized_files and payload is not None:
            req_headers.setdefault("Content-Type", "application/json")

        hook_options = {
            "method": request_kwargs["method"],
            "headers": dict(req_headers),
            "body": payload,
            "query": dict(query or {}),
            "files": normalized_files,
        }

        if self.before_send:
            override = self.before_send(url, hook_options)
            hook_method = hook_options.get("method")
            if hook_method:
                request_kwargs["method"] = hook_method.upper()
            req_headers = hook_options.get("headers", req_headers)
            if "body" in hook_options:
                payload = hook_options["body"]
            if "files" in hook_options:
                files_payload = hook_options["files"]
                normalized_files = ensure_file_tuples(files_payload)
            hook_query = hook_options.get("query", current_query)
            current_query = hook_query
            url = self.build_url(path, current_query)

            if override:
                if "url" in override:
                    url = override["url"]
                new_options = override.get("options") or {}
                if "method" in new_options:
                    request_kwargs["method"] = str(new_options["method"]).upper()
                if "headers" in new_options:
                    req_headers = dict(new_options["headers"])
                if "body" in new_options:
                    payload = new_options["body"]
                if "files" in new_options:
                    files_payload = new_options["files"]
                    normalized_files = ensure_file_tuples(files_payload)
                if "query" in new_options:
                    current_query = dict(new_options["query"] or {})
                    url = self.build_url(path, current_query)
                if "timeout" in new_options:
                    request_kwargs["timeout"] = new_options["timeout"]

        payload = to_serializable(payload) if payload is not None else None

        request_kwargs["url"] = url
        request_kwargs["headers"] = req_headers
        request_kwargs["method"] = request_kwargs["method"].upper()

        if normalized_files:
            request_kwargs["files"] = normalized_files
            request_kwargs["data"] = {"@jsonPayload": json.dumps(payload or {})}
            request_kwargs.pop("json", None)
        else:
            request_kwargs.pop("files", None)
            request_kwargs.pop("data", None)
            if payload is not None:
                request_kwargs["json"] = payload
            elif "json" in request_kwargs:
                request_kwargs.pop("json")

        try:
            try:
                response = requests.request(**request_kwargs)
            except requests.RequestException as exc:  # pragma: no cover - network errors
                if cancel_event and cancel_event.is_set():
                    raise ClientResponseError(
                        url=url,
                        status=0,
                        response={"message": "Request aborted"},
                        is_abort=True,
                        original_error=exc,
                    ) from exc
                raise ClientResponseError(url=url, original_error=exc) from exc

            data: Any = None
            if response.status_code != 204:
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type.lower():
                    try:
                        data = response.json()
                    except ValueError:
                        data = {}
                else:
                    data = response.content

            if cancel_event and cancel_event.is_set():
                raise ClientResponseError(
                    url=url,
                    status=0,
                    response={"message": "Request aborted"},
                    is_abort=True,
                )

            if response.status_code >= 400:
                raise ClientResponseError(
                    url=url,
                    status=response.status_code,
                    response=data if isinstance(data, dict) else {},
                )

            if self.after_send:
                data = self.after_send(response, data)

            if cancel_event and cancel_event.is_set():
                raise ClientResponseError(
                    url=url,
                    status=0,
                    response={"message": "Request aborted"},
                    is_abort=True,
                )

            return data
        finally:
            if cancel_key and cancel_event:
                with self._cancel_lock:
                    if self._cancel_tokens.get(cancel_key) is cancel_event:
                        self._cancel_tokens.pop(cancel_key, None)
