# Health API - Python SDK

Use the Health API to verify that the BosBase instance is online and to integrate with load balancers or monitoring systems.

## Health Check

```python
status = pb.health.check()
print(status["code"], status["message"])
```

The response contains:

- `code`: `200` if everything is OK.
- `message`: `"OK"` or an error string.
- `data`: optional extended diagnostics.

## Monitoring Strategy

1. Add a periodic job that calls `pb.health.check()` and pushes the result to your telemetry platform.
2. If you run BosBase behind a reverse proxy, configure upstream health checks to point at `/api/health`.
3. Combine with realtime alerts: when the health check fails, pause cron triggers or queue processing.

## Troubleshooting

- `code >= 500`: usually indicates a server panic or database connection issue. Inspect container logs.
- `code = 503`: the instance is booting or a long migration is running.
- If you can’t reach `/api/health`, verify that the proxy forwards SSE connections correctly—misconfigured proxies can hang sockets and starve the server.
