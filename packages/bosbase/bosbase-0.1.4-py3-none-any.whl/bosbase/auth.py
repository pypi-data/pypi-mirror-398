"""Authentication store helpers."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import threading
import warnings
from datetime import datetime, timezone
from email.utils import format_datetime
from http import cookies
from inspect import isawaitable
from queue import Queue
from typing import Any, Callable, Dict, Mapping, Optional

DEFAULT_COOKIE_KEY = "pb_auth"
DEFAULT_LOCAL_STORAGE_KEY = "bosbase_auth"
DEFAULT_LOCAL_STORAGE_FILENAME = ".bosbase_auth.json"
SUPERUSER_COLLECTION_IDS = {"pbc_3142635823", "_pbc_2773867675"}


def _strip_bearer(token: str) -> str:
    raw = (token or "").strip()
    if raw.lower().startswith("bearer "):
        return raw[7:].strip()
    return raw


def get_token_payload(token: str) -> Dict[str, Any]:
    token = _strip_bearer(token)
    parts = token.split(".")
    if len(parts) != 3:
        return {}
    payload_part = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        payload_raw = base64.urlsafe_b64decode(payload_part.encode("utf-8"))
        payload = json.loads(payload_raw.decode("utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def is_token_expired(token: str, threshold: int = 0) -> bool:
    if not token:
        return True
    payload = get_token_payload(token)
    exp = payload.get("exp")
    if exp is None:
        return True
    try:
        exp_value = int(exp)
    except (TypeError, ValueError):
        return True
    import time

    return exp_value <= int(time.time()) + int(threshold)


def _parse_cookie(cookie_header: str) -> Dict[str, str]:
    jar = cookies.SimpleCookie()
    jar.load(cookie_header or "")
    return {key: morsel.value for key, morsel in jar.items()}


def _serialize_cookie(
    key: str,
    value: str,
    options: Mapping[str, Any],
) -> str:
    jar = cookies.SimpleCookie()
    jar[key] = value
    morsel = jar[key]

    if options.get("path"):
        morsel["path"] = options["path"]
    if options.get("domain"):
        morsel["domain"] = options["domain"]
    if options.get("secure"):
        morsel["secure"] = True
    if options.get("httpOnly") or options.get("http_only") or options.get("httponly"):
        morsel["httponly"] = True

    same_site = (
        options.get("sameSite")
        if "sameSite" in options
        else options.get("same_site", options.get("samesite"))
    )
    if same_site is True:
        same_site = "Strict"
    if isinstance(same_site, str) and same_site:
        morsel["samesite"] = same_site

    max_age = options.get("maxAge")
    if max_age is None:
        max_age = options.get("max_age")
    if max_age is not None:
        morsel["max-age"] = str(int(max_age))

    expires = options.get("expires")
    if isinstance(expires, datetime):
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        morsel["expires"] = format_datetime(expires, usegmt=True)
    elif isinstance(expires, str) and expires:
        morsel["expires"] = expires

    return morsel.OutputString()


class BaseAuthStore:
    """In-memory authentication store shared across services."""

    def __init__(self) -> None:
        self._token: str = ""
        self._record: Optional[Dict[str, Any]] = None
        self._lock = threading.RLock()
        self._listeners: list[Callable[[str, Optional[Dict[str, Any]]], None]] = []

    @property
    def token(self) -> str:
        return self._token

    @property
    def record(self) -> Optional[Dict[str, Any]]:
        return self._record

    @property
    def model(self) -> Optional[Dict[str, Any]]:
        warnings.warn(
            "AuthStore.model is deprecated; use AuthStore.record instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.record

    def is_valid(self) -> bool:
        """Return True when a non-expired JWT token is stored."""
        return not is_token_expired(self.token)

    @property
    def is_superuser(self) -> bool:
        payload = get_token_payload(self.token)
        if payload.get("type") != "auth":
            return False

        record = self.record or {}
        collection_name = record.get("collectionName")
        collection_id = record.get("collectionId") or payload.get("collectionId")

        if collection_name == "_superusers":
            return True

        if collection_id in SUPERUSER_COLLECTION_IDS or collection_id == "_superusers":
            return True

        return False

    @property
    def is_admin(self) -> bool:
        warnings.warn(
            "AuthStore.is_admin is deprecated; use AuthStore.is_superuser instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.is_superuser

    @property
    def is_auth_record(self) -> bool:
        warnings.warn(
            "AuthStore.is_auth_record is deprecated; use not AuthStore.is_superuser instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        payload = get_token_payload(self.token)
        return payload.get("type") == "auth" and not self.is_superuser

    def add_listener(
        self, callback: Callable[[str, Optional[Dict[str, Any]]], None]
    ) -> None:
        with self._lock:
            self._listeners.append(callback)

    def remove_listener(
        self, callback: Callable[[str, Optional[Dict[str, Any]]], None]
    ) -> None:
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def on_change(
        self,
        callback: Callable[[str, Optional[Dict[str, Any]]], None],
        *,
        fire_immediately: bool = False,
    ) -> Callable[[], None]:
        self.add_listener(callback)
        if fire_immediately:
            callback(self._token, self._record)

        def unsubscribe() -> None:
            self.remove_listener(callback)

        return unsubscribe

    def save(self, token: str, record: Optional[Dict[str, Any]]) -> None:
        with self._lock:
            self._token = token or ""
            self._record = record
            listeners = list(self._listeners)

        for listener in listeners:
            try:
                listener(self._token, self._record)
            except Exception:
                # best-effort notification
                pass

    def clear(self) -> None:
        self.save("", None)

    def load_from_cookie(self, cookie_header: str, key: str = DEFAULT_COOKIE_KEY) -> None:
        raw = _parse_cookie(cookie_header or "").get(key, "")
        data: Dict[str, Any] = {}
        try:
            parsed = json.loads(raw) if raw else {}
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            data = {}

        self.save(data.get("token", ""), data.get("record") or data.get("model"))

    def export_to_cookie(
        self,
        options: Optional[Mapping[str, Any]] = None,
        key: str = DEFAULT_COOKIE_KEY,
    ) -> str:
        defaults: Dict[str, Any] = {
            "secure": True,
            "sameSite": True,
            "httpOnly": True,
            "path": "/",
        }

        payload = get_token_payload(self.token)
        exp = payload.get("exp")
        if exp is not None:
            try:
                defaults["expires"] = datetime.fromtimestamp(int(exp), tz=timezone.utc)
            except (TypeError, ValueError):
                defaults["expires"] = datetime(1970, 1, 1, tzinfo=timezone.utc)
        else:
            defaults["expires"] = datetime(1970, 1, 1, tzinfo=timezone.utc)

        merged = dict(defaults)
        if options:
            merged.update(options)

        raw_data = {"token": self.token, "record": self.record or None}
        try:
            serialized = json.dumps(raw_data, separators=(",", ":"))
        except TypeError:
            raw_data["record"] = None
            serialized = json.dumps(raw_data, separators=(",", ":"))
        cookie_str = _serialize_cookie(key, serialized, merged)

        if len(cookie_str.encode("utf-8")) > 4096 and raw_data["record"]:
            minimal = {
                "id": raw_data["record"].get("id"),
                "email": raw_data["record"].get("email"),
                "collectionId": raw_data["record"].get("collectionId"),
                "collectionName": raw_data["record"].get("collectionName"),
                "verified": raw_data["record"].get("verified"),
            }
            raw_data["record"] = minimal
            serialized = json.dumps(raw_data, separators=(",", ":"))
            cookie_str = _serialize_cookie(key, serialized, merged)

        return cookie_str


class AuthStore(BaseAuthStore):
    """Backwards-compatible alias for BaseAuthStore."""


class LocalAuthStore(BaseAuthStore):
    """Persist auth state to a local JSON file (fallbacks to in-memory)."""

    def __init__(
        self,
        storage_key: str = DEFAULT_LOCAL_STORAGE_KEY,
        storage_path: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._storage_key = storage_key
        self._storage_path = storage_path or os.path.join(
            os.path.expanduser("~"),
            DEFAULT_LOCAL_STORAGE_FILENAME,
        )
        self._storage_fallback: Dict[str, Any] = {}
        self._storage_lock = threading.RLock()

    @property
    def token(self) -> str:
        data = self._storage_get()
        return data.get("token", "")

    @property
    def record(self) -> Optional[Dict[str, Any]]:
        data = self._storage_get()
        return data.get("record") or data.get("model")

    def save(self, token: str, record: Optional[Dict[str, Any]]) -> None:
        self._storage_set({"token": token, "record": record})
        super().save(token, record)

    def clear(self) -> None:
        self._storage_remove()
        super().clear()

    # ------------------------------------------------------------------
    # Storage helpers
    # ------------------------------------------------------------------

    def _storage_get(self) -> Dict[str, Any]:
        with self._storage_lock:
            if not self._storage_path:
                return self._storage_fallback.get(self._storage_key, {})

            try:
                with open(self._storage_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle) or {}
            except FileNotFoundError:
                data = {}
            except Exception:
                data = {}

            if not isinstance(data, dict):
                return {}
            return data.get(self._storage_key, {}) or {}

    def _storage_set(self, payload: Dict[str, Any]) -> None:
        with self._storage_lock:
            if not self._storage_path:
                self._storage_fallback[self._storage_key] = payload
                return

            data: Dict[str, Any] = {}
            try:
                if os.path.exists(self._storage_path):
                    with open(self._storage_path, "r", encoding="utf-8") as handle:
                        data = json.load(handle) or {}
            except Exception:
                data = {}

            if not isinstance(data, dict):
                data = {}

            data[self._storage_key] = payload

            dir_path = os.path.dirname(self._storage_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            with open(self._storage_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, separators=(",", ":"))

    def _storage_remove(self) -> None:
        with self._storage_lock:
            if not self._storage_path:
                self._storage_fallback.pop(self._storage_key, None)
                return

            try:
                if not os.path.exists(self._storage_path):
                    return
                with open(self._storage_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle) or {}
                if isinstance(data, dict):
                    data.pop(self._storage_key, None)
                    if data:
                        with open(self._storage_path, "w", encoding="utf-8") as handle:
                            json.dump(data, handle, separators=(",", ":"))
                    else:
                        os.remove(self._storage_path)
            except Exception:
                return


class AsyncAuthStore(BaseAuthStore):
    """Auth store that persists state using user-provided async callbacks."""

    def __init__(
        self,
        *,
        save: Callable[[str], Any],
        clear: Optional[Callable[[], Any]] = None,
        initial: Optional[Any] = None,
    ) -> None:
        super().__init__()
        self._save_func = save
        self._clear_func = clear
        self._queue: "Queue[Callable[[], None]]" = Queue()
        self._worker = threading.Thread(target=self._run_queue, daemon=True)
        self._worker.start()

        if initial is not None:
            self._enqueue(lambda: self._load_initial(initial))

    def save(self, token: str, record: Optional[Dict[str, Any]]) -> None:
        super().save(token, record)
        try:
            serialized = json.dumps({"token": token, "record": record}, separators=(",", ":"))
        except Exception:
            serialized = ""
        self._enqueue(lambda: self._call_async(self._save_func, serialized))

    def clear(self) -> None:
        super().clear()
        if self._clear_func:
            self._enqueue(lambda: self._call_async(self._clear_func))
        else:
            self._enqueue(lambda: self._call_async(self._save_func, ""))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _enqueue(self, func: Callable[[], None]) -> None:
        self._queue.put(func)

    def _run_queue(self) -> None:
        while True:
            task = self._queue.get()
            try:
                task()
            except Exception:
                pass
            finally:
                self._queue.task_done()

    def _call_async(self, func: Callable[..., Any], *args: Any) -> None:
        result = func(*args)
        if isawaitable(result):
            self._run_coroutine(result)

    def _run_coroutine(self, coro: Any) -> None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(coro)
        finally:
            try:
                loop.close()
            except Exception:
                pass

    def _load_initial(self, payload: Any) -> None:
        try:
            if callable(payload):
                payload = payload()
            if isawaitable(payload):
                payload = self._await_value(payload)
            if isinstance(payload, str):
                payload = json.loads(payload) if payload else {}
            if isinstance(payload, dict):
                self.save(payload.get("token", ""), payload.get("record") or payload.get("model"))
        except Exception:
            return

    def _await_value(self, coro: Any) -> Any:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            try:
                loop.close()
            except Exception:
                pass
