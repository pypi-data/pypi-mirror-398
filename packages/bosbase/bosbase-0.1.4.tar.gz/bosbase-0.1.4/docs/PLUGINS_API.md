# Plugins Proxy API - JavaScript SDK

## Overview

The `plugins` helper forwards HTTP requests from the JS SDK to the Go backend, which then proxies them to your Python plugin (the target is set with `PLUGIN_URL` in `docker-compose`). It works with the standard HTTP verbs and does not require user or superuser authentication.

**Key points**
- Supports `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`, plus `SSE` and `WEBSOCKET` helpers.
- Paths are routed through `/api/plugins/{your-plugin-path}` (leading slashes are trimmed; `/api/plugins/...` is accepted as-is).
- Query params, request bodies, and headers are passed through unchanged to the plugin service.
- HTTP requests respect global `beforeSend`/`afterSend` hooks and all regular `SendOptions`.
- Public endpoint—no auth required (the SDK will still include your auth token if one is set).

## Quick start

```javascript
import BosBase from "bosbase";

const pb = new BosBase("http://127.0.0.1:8080");

// Simple GET to your plugin (e.g., FastAPI /health)
const health = await pb.plugins("GET", "/health");

console.log(health); // { status: "ok" }
```

## Send bodies and headers

```javascript
await pb.plugins("POST", "tasks", {
    body: { title: "Generate docs", priority: "high" },
    headers: { "X-Plugin-Key": "demo-secret" },
});
```

## Work with query parameters

```javascript
const summary = await pb.plugins("GET", "reports/summary", {
    query: { since: "2024-01-01", limit: 50, tags: ["ops", "ml"] },
});
```

## Other verbs

```javascript
// Update
await pb.plugins("PATCH", "tasks/42", { body: { status: "done" } });

// Delete
await pb.plugins("DELETE", "tasks/42");

// Check liveness without a body
await pb.plugins("HEAD", "health");

// Discover plugin-supported methods
await pb.plugins("OPTIONS", "tasks");
```

## Server-Sent Events (SSE)

Use the `SSE` method to open an `EventSource` stream to your plugin (query params are appended automatically). When an auth token is present it is sent as `?token=...` because SSE cannot set custom headers in the browser (headers are still passed if your runtime/ponyfill supports them, e.g. Node `eventsource`).

```javascript
const stream = pb.plugins("SSE", "events/updates", {
    query: { topic: "team-alpha" },
    eventSourceInit: { withCredentials: true }, // forwarded to new EventSource(url, init)
    headers: { "X-Plugin-Key": "secret" }, // forwarded when supported by the runtime
});

stream.addEventListener("message", (event) => {
    const payload = JSON.parse(event.data);
    console.log("update:", payload);
});

// Remember to close when done
stream.addEventListener("end", () => stream.close());
```

## WebSockets

Use the `WEBSOCKET` (or `WS`) method to open a WebSocket to your plugin. The SDK converts your base URL to `ws://`/`wss://`, preserves query params, and appends `token` if you are authenticated. Custom headers are passed to environments that support them (e.g. Node's `ws` library); browsers ignore them because the standard API doesn't allow custom handshake headers.

```javascript
const socket = pb.plugins("WEBSOCKET", "ws/chat", {
    query: { room: "general" },
    websocketProtocols: ["json"], // optional subprotocols
    headers: { "X-Plugin-Key": "secret" },
});

socket.onopen = () => {
    socket.send(JSON.stringify({ type: "join", name: "lea" }));
};

socket.onmessage = (event) => {
    console.log("chat message:", event.data);
};

socket.onerror = console.error;
```

## Notes and behavior
- Implemented SSE and WebSocket support on plugins, forwarding via /api/plugins, preserving query params, and now passing headers to EventSource/WebSocket constructors when supported. 
- Requests are sent to `/api/plugins/...` on the Go backend, which forwards them to the Python plugin service 
- All `SendOptions` are supported: `headers`, `body`, `query`, `requestKey`/`$cancelKey`, and custom `fetch` functions.
- Body serialization and FormData conversion follow the normal client rules; set `Content-Type` yourself when you need a different encoding.
- Because the endpoint is public, add any plugin-side checks you need (tokens, IP allowlists, etc.) without changing the SDK.
- `SSE` returns a native `EventSource`; `WEBSOCKET` returns a `WebSocket`. These helpers skip `beforeSend`/`afterSend` because they do not use `fetch`.
- When a user token is present, SSE/WebSocket URLs include `?token=...` so your plugin can still authenticate the caller even though custom headers are unavailable.
- Headers are forwarded to SSE/WebSocket constructors when supported by the runtime; in browsers the token query param is the portable way to authenticate.
