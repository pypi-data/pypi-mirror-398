"""Server-Sent Events realtime implementation."""

from __future__ import annotations

import json
import threading
import time
from typing import Any, Callable, Dict, List, Mapping, MutableMapping, Optional
from urllib.parse import quote

import requests

from ..exceptions import ClientResponseError
from .base import BaseService


class RealtimeService(BaseService):
    def __init__(self, client) -> None:
        super().__init__(client)
        self.client_id: str = ""
        self.on_disconnect: Optional[Callable[[List[str]], None]] = None
        self._subscriptions: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self._lock = threading.RLock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._response: Optional[requests.Response] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def subscribe(
        self,
        topic: str,
        callback: Callable[[Dict[str, Any]], None],
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Callable[[], None]:
        if not topic:
            raise ValueError("topic must be set")
        if callback is None:
            raise ValueError("callback must be set")

        key = self._build_subscription_key(topic, query=query, headers=headers)

        with self._lock:
            listeners = self._subscriptions.setdefault(key, [])
            listeners.append(callback)

        self._ensure_thread()
        self.ensure_connected()
        self._submit_subscriptions()

        def unsubscribe() -> None:
            self.unsubscribe_by_topic_and_listener(topic, callback)

        return unsubscribe

    def unsubscribe(self, topic: Optional[str] = None) -> None:
        with self._lock:
            if topic is None:
                changed = bool(self._subscriptions)
                self._subscriptions.clear()
            else:
                keys = self._keys_for_topic(topic)
                changed = bool(keys)
                for key in keys:
                    self._subscriptions.pop(key, None)

        if changed:
            if self._has_subscriptions():
                self._submit_subscriptions()
            else:
                self.disconnect()

    def unsubscribe_by_prefix(self, prefix: str) -> None:
        with self._lock:
            keys = [k for k in self._subscriptions if k.startswith(prefix)]
            for key in keys:
                self._subscriptions.pop(key, None)

        if self._has_subscriptions():
            self._submit_subscriptions()
        else:
            self.disconnect()

    def unsubscribe_by_topic_and_listener(
        self,
        topic: str,
        listener: Callable[[Dict[str, Any]], None],
    ) -> None:
        with self._lock:
            keys = self._keys_for_topic(topic)
            for key in keys:
                listeners = self._subscriptions.get(key)
                if not listeners:
                    continue
                if listener in listeners:
                    listeners.remove(listener)
                if not listeners:
                    self._subscriptions.pop(key, None)

        if self._has_subscriptions():
            self._submit_subscriptions()
        else:
            self.disconnect()

    def disconnect(self) -> None:
        self._stop_event.set()
        if self._response is not None:
            try:
                self._response.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=1.0)
        self._thread = None
        self._response = None
        self._ready_event.clear()
        self.client_id = ""

    def ensure_connected(self, timeout: float = 10.0) -> None:
        self._ensure_thread()
        if not self._ready_event.wait(timeout):
            raise ClientResponseError(
                response={"message": "Realtime connection not established"}
            )

    def ensure_thread_running(self) -> None:
        self._ensure_thread()

    def get_active_subscriptions(self) -> List[str]:
        with self._lock:
            return list(self._subscriptions.keys())

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ensure_thread(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def _run(self) -> None:
        backoff = [0.2, 0.5, 1, 2, 5]
        attempt = 0
        url = self.client.build_url("/api/realtime")

        while not self._stop_event.is_set():
            headers = {
                "Accept": "text/event-stream",
                "Cache-Control": "no-store",
                "Accept-Language": self.client.lang,
                "User-Agent": "bosbase-python-sdk",
            }
            if self.client.auth_store.token:
                headers["Authorization"] = self.client.auth_store.token

            try:
                response = requests.get(
                    url,
                    stream=True,
                    headers=headers,
                    timeout=(
                        10,
                        60,
                    ),
                )
                response.raise_for_status()
                self._response = response
                self._ready_event.clear()
                self._listen(response)
                attempt = 0
            except Exception:
                self._ready_event.clear()
                self.client_id = ""
                if self.on_disconnect:
                    try:
                        self.on_disconnect(self.get_active_subscriptions())
                    except Exception:
                        pass
                if self._stop_event.is_set() or not self._has_subscriptions():
                    break
                delay = backoff[min(attempt, len(backoff) - 1)]
                attempt += 1
                time.sleep(delay)
            finally:
                if self._response is not None:
                    try:
                        self._response.close()
                    except Exception:
                        pass
                self._response = None

    def _listen(self, response: requests.Response) -> None:
        buffer: Dict[str, str] = {"event": "message", "data": "", "id": ""}
        for raw_line in response.iter_lines(decode_unicode=True):
            if self._stop_event.is_set():
                break
            if raw_line is None:
                continue
            line = raw_line.strip("\r")
            if not line:
                self._dispatch_event(buffer)
                buffer = {"event": "message", "data": "", "id": ""}
                continue
            if line.startswith(":"):
                continue
            if ":" in line:
                field, value = line.split(":", 1)
                value = value.lstrip(" ")
            else:
                field, value = line, ""
            if field == "event":
                buffer["event"] = value or "message"
            elif field == "data":
                buffer["data"] += value + "\n"
            elif field == "id":
                buffer["id"] = value

    def _dispatch_event(self, event: Dict[str, str]) -> None:
        name = event.get("event") or "message"
        data_str = (event.get("data") or "").rstrip("\n")
        payload: Dict[str, Any]
        if data_str:
            try:
                payload = json.loads(data_str)
            except json.JSONDecodeError:
                payload = {"raw": data_str}
        else:
            payload = {}

        if name == "PB_CONNECT":
            self.client_id = payload.get("clientId") or event.get("id") or ""
            self._ready_event.set()
            self._submit_subscriptions()
            if self.on_disconnect:
                # signal reconnect completion by simulating no disconnect with active subs
                try:
                    self.on_disconnect([])
                except Exception:
                    pass
            return

        listeners = []
        with self._lock:
            listeners = list(self._subscriptions.get(name, []))

        for listener in listeners:
            try:
                listener(payload)
            except Exception:
                pass  # best-effort delivery

    def _submit_subscriptions(self) -> None:
        if not self.client_id or not self._has_subscriptions():
            return

        payload = {
            "clientId": self.client_id,
            "subscriptions": self.get_active_subscriptions(),
        }
        try:
            self.client.send(
                "/api/realtime",
                method="POST",
                body=payload,
            )
        except ClientResponseError as exc:
            if exc.is_abort:
                return
            raise

    def _build_subscription_key(
        self,
        topic: str,
        *,
        query: Optional[Mapping[str, Any]],
        headers: Optional[MutableMapping[str, str]],
    ) -> str:
        key = topic
        options: Dict[str, Any] = {}
        if query:
            options["query"] = query
        if headers:
            options["headers"] = dict(headers)
        if options:
            serialized = json.dumps(options, separators=(",", ":"), sort_keys=True)
            suffix = "options=" + quote(serialized)
            key += ("&" if "?" in key else "?") + suffix
        return key

    def _keys_for_topic(self, topic: str) -> List[str]:
        result: List[str] = []
        prefix = f"{topic}?"
        for key in self._subscriptions:
            if key == topic or key.startswith(prefix):
                result.append(key)
        return result

    def _has_subscriptions(self) -> bool:
        with self._lock:
            return any(self._subscriptions.values())
