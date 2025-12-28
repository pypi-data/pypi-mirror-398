"""WebSocket-based publish/subscribe implementation."""

from __future__ import annotations

import json
import threading
import time
from typing import Any, Callable, Dict, List, Optional

try:  # pragma: no cover - optional dependency for runtime pubsub
    import websocket  # type: ignore
except Exception:  # pragma: no cover
    websocket = None  # type: ignore

from ..exceptions import ClientResponseError
from .base import BaseService


class PubSubMessage:
    def __init__(self, id: str, topic: str, created: str, data: Any) -> None:
        self.id = id
        self.topic = topic
        self.created = created
        self.data = data


class PublishAck:
    def __init__(self, id: str, topic: str, created: str) -> None:
        self.id = id
        self.topic = topic
        self.created = created


class _PendingAck:
    def __init__(self, resolve: Callable[[Dict[str, Any]], None], reject: Callable[[Exception], None], timer: threading.Timer) -> None:
        self.resolve = resolve
        self.reject = reject
        self.timer = timer


class PubSubService(BaseService):
    def __init__(self, client) -> None:
        super().__init__(client)
        self._ws: Optional[websocket.WebSocketApp] = None
        self._thread: Optional[threading.Thread] = None
        self._subscriptions: Dict[str, List[Callable[[PubSubMessage], None]]] = {}
        self._pending_acks: Dict[str, _PendingAck] = {}
        self._pending_connects: List[threading.Event] = []
        self._lock = threading.RLock()
        self._reconnect_attempts = 0
        self._manual_close = False
        self._connect_timer: Optional[threading.Timer] = None
        self._reconnect_timer: Optional[threading.Timer] = None
        self._ack_timeout = 10.0
        self._connect_timeout = 15.0
        self._is_ready = False
        self._client_id = ""
        self._reconnect_intervals = [0.2, 0.3, 0.5, 1.0, 1.2, 1.5, 2.0]

    @property
    def is_connected(self) -> bool:
        with self._lock:
            return self._is_ready

    def publish(self, topic: str, data: Any) -> PublishAck:
        if not topic:
            raise ValueError("topic must be set.")

        self.ensure_socket()

        request_id = self._next_request_id()
        ack_future = self._wait_for_ack(
            request_id,
            lambda payload: PublishAck(
                id=str(payload.get("id", "")),
                topic=str(payload.get("topic") or topic),
                created=str(payload.get("created", "")),
            ),
        )

        self._send_envelope(
            {
                "type": "publish",
                "topic": topic,
                "data": data,
                "requestId": request_id,
            }
        )

        return ack_future

    def subscribe(self, topic: str, callback: Callable[[PubSubMessage], None]) -> Callable[[], None]:
        if not topic:
            raise ValueError("topic must be set.")

        is_first_listener = False
        with self._lock:
            listeners = self._subscriptions.setdefault(topic, [])
            if not listeners:
                is_first_listener = True
            listeners.append(callback)

        self.ensure_socket()

        if is_first_listener:
            request_id = self._next_request_id()
            self._wait_for_ack(request_id, lambda _: True)
            self._send_envelope({"type": "subscribe", "topic": topic, "requestId": request_id})

        def unsubscribe() -> None:
            with self._lock:
                listeners = self._subscriptions.get(topic, [])
                if callback in listeners:
                    listeners.remove(callback)
                if not listeners:
                    self._subscriptions.pop(topic, None)
                    self._send_unsubscribe(topic)
            if not self._has_subscriptions():
                self.disconnect()

        return unsubscribe

    def unsubscribe(self, topic: Optional[str] = None) -> None:
        if topic:
            self._subscriptions.pop(topic, None)
            self._send_unsubscribe(topic)
            if not self._has_subscriptions():
                self.disconnect()
        else:
            self._subscriptions.clear()
            self._send_envelope({"type": "unsubscribe"})
            self.disconnect()

    def disconnect(self) -> None:
        self._manual_close = True
        self._reject_all_pending(ClientResponseError(url=None, status=0, response={"message": "pubsub connection closed"}))
        self._close_socket()
        with self._lock:
            for ev in self._pending_connects:
                ev.set()
            self._pending_connects.clear()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def ensure_socket(self) -> None:
        if websocket is None:
            raise ImportError("websocket-client is required for pubsub")
        with self._lock:
            if self._is_ready:
                return
            ev = threading.Event()
            self._pending_connects.append(ev)
            should_start = len(self._pending_connects) == 1
        if should_start:
            self._init_connect()
        # block until connected or failure
        ev.wait()

    def _init_connect(self) -> None:
        self._close_socket(keep_subscriptions=True)
        self._manual_close = False
        self._is_ready = False

        try:
            url = self._build_ws_url()
        except Exception as exc:
            self._connect_error_handler(exc)
            return

        self._connect_timer = threading.Timer(self._connect_timeout, lambda: self._connect_error_handler(Exception("WebSocket connect took too long.")))
        self._connect_timer.start()

        self._ws = websocket.WebSocketApp(
            url,
            on_message=lambda _ws, msg: self._handle_message(msg),
            on_error=lambda _ws, err: self._connect_error_handler(err),
            on_close=lambda _ws, code, reason: self._handle_close(),
        )

        self._thread = threading.Thread(target=self._ws.run_forever, daemon=True)
        self._thread.start()

    def _build_ws_url(self) -> str:
        query: Dict[str, Any] = {}
        if self.client.auth_store.token:
            query["token"] = self.client.auth_store.token
        base = self.client.build_url("/api/pubsub", query)
        if base.startswith("https"):
            return base.replace("https", "wss", 1)
        if base.startswith("http"):
            return base.replace("http", "ws", 1)
        return "ws://" + base.lstrip("/")

    def _handle_message(self, payload: str) -> None:
        self._connect_timer.cancel() if self._connect_timer else None
        try:
            data = json.loads(payload)
        except Exception:
            return

        if not isinstance(data, dict):
            return

        msg_type = data.get("type")
        if msg_type == "ready":
            self._client_id = str(data.get("clientId", ""))
            self._handle_connected()
            return

        if msg_type == "message":
            topic = str(data.get("topic", ""))
            listeners = list(self._subscriptions.get(topic, []))
            if not listeners:
                return
            message = PubSubMessage(
                id=str(data.get("id", "")),
                topic=topic,
                created=str(data.get("created", "")),
                data=data.get("data"),
            )
            for listener in listeners:
                try:
                    listener(message)
                except Exception:
                    pass
            return

        if msg_type in {"published", "subscribed", "unsubscribed", "pong"}:
            req_id = data.get("requestId")
            if req_id:
                self._resolve_pending(str(req_id), data)
            return

        if msg_type == "error":
            req_id = data.get("requestId")
            if req_id:
                self._reject_pending(
                    str(req_id),
                    ClientResponseError(
                        url=None,
                        status=0,
                        response={"message": data.get("message", "pubsub error")},
                    ),
                )

    def _handle_connected(self) -> None:
        should_resubscribe = self._reconnect_attempts > 0
        self._reconnect_attempts = 0
        self._reconnect_timer.cancel() if self._reconnect_timer else None
        self._connect_timer.cancel() if self._connect_timer else None

        with self._lock:
            self._is_ready = True
            pending = list(self._pending_connects)
            self._pending_connects.clear()
        for ev in pending:
            ev.set()

        if should_resubscribe:
            for topic in list(self._subscriptions.keys()):
                request_id = self._next_request_id()
                self._wait_for_ack(request_id, lambda _: True)
                self._send_envelope({"type": "subscribe", "topic": topic, "requestId": request_id})

    def _handle_close(self) -> None:
        self._ws = None
        self._is_ready = False

        if self._manual_close:
            return

        self._reject_all_pending(ClientResponseError(url=None, status=0, response={"message": "pubsub connection closed"}))

        if not self._has_subscriptions():
            with self._lock:
                for ev in self._pending_connects:
                    ev.set()
                self._pending_connects.clear()
            return

        delay = self._reconnect_intervals[min(self._reconnect_attempts, len(self._reconnect_intervals) - 1)]
        self._reconnect_attempts += 1
        self._reconnect_timer = threading.Timer(delay, self._init_connect)
        self._reconnect_timer.start()

    def _send_envelope(self, data: Dict[str, Any]) -> None:
        if not self._ws or not self._is_ready:
            self.ensure_socket()
        if not self._ws:
            raise ClientResponseError(url=None, status=0, response={"message": "Unable to send websocket message - socket not initialized."})
        try:
            self._ws.send(json.dumps(data))
        except Exception as exc:
            raise ClientResponseError(url=None, status=0, response={"message": str(exc)}) from exc

    def _send_unsubscribe(self, topic: str) -> None:
        if not self._ws:
            return
        request_id = self._next_request_id()
        self._wait_for_ack(request_id, lambda _: True)
        self._send_envelope({"type": "unsubscribe", "topic": topic, "requestId": request_id})

    def _connect_error_handler(self, err: Exception) -> None:
        if self._reconnect_attempts > 1e6 or self._manual_close:
            self._reject_all_pending(ClientResponseError(url=None, status=0, response={"message": str(err)}))
            self._close_socket()
            with self._lock:
                for ev in self._pending_connects:
                    ev.set()
                self._pending_connects.clear()
            return
        self._close_socket(keep_subscriptions=True)
        delay = self._reconnect_intervals[min(self._reconnect_attempts, len(self._reconnect_intervals) - 1)]
        self._reconnect_attempts += 1
        self._reconnect_timer = threading.Timer(delay, self._init_connect)
        self._reconnect_timer.start()

    def _close_socket(self, keep_subscriptions: bool = False) -> None:
        try:
            if self._ws:
                self._ws.close()
        except Exception:
            pass
        if self._connect_timer:
            self._connect_timer.cancel()
            self._connect_timer = None
        if self._reconnect_timer:
            self._reconnect_timer.cancel()
            self._reconnect_timer = None
        self._ws = None
        self._is_ready = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        if not keep_subscriptions:
            self._subscriptions.clear()
            self._pending_acks.clear()

    def _wait_for_ack(self, request_id: str, mapper: Callable[[Dict[str, Any]], Any]) -> Any:
        result: Dict[str, Any] = {}
        finished = threading.Event()

        def resolve(payload: Dict[str, Any]) -> None:
            nonlocal result
            if finished.is_set():
                return
            try:
                result["value"] = mapper(payload)
            except Exception as exc:
                result["error"] = exc
            finished.set()

        def reject(exc: Exception) -> None:
            if finished.is_set():
                return
            result["error"] = exc
            finished.set()

        timer = threading.Timer(self._ack_timeout, lambda: reject(Exception("Timed out waiting for pubsub response.")))
        timer.start()

        self._pending_acks[request_id] = _PendingAck(resolve, reject, timer)
        finished.wait()

        pending = self._pending_acks.pop(request_id, None)
        if pending:
            pending.timer.cancel()

        if "error" in result:
            raise result["error"]  # type: ignore[misc]
        return result.get("value")

    def _resolve_pending(self, request_id: str, payload: Dict[str, Any]) -> None:
        pending = self._pending_acks.pop(request_id, None)
        if pending:
            pending.timer.cancel()
            pending.resolve(payload)

    def _reject_pending(self, request_id: str, err: Exception) -> None:
        pending = self._pending_acks.pop(request_id, None)
        if pending:
            pending.timer.cancel()
            pending.reject(err)

    def _reject_all_pending(self, err: Exception) -> None:
        for pending in list(self._pending_acks.values()):
            pending.timer.cancel()
            pending.reject(err)
        self._pending_acks.clear()

    def _has_subscriptions(self) -> bool:
        with self._lock:
            return any(self._subscriptions.values())

    def _next_request_id(self) -> str:
        return hex(int(time.time() * 1000))[2:] + hex(id(self))[2:]
