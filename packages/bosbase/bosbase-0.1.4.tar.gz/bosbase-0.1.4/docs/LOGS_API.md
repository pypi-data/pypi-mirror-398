# Logs API - Python SDK

Use the Logs API to inspect request logs, audit admin activity, and track rule failures.

## List Logs

```python
logs = pb.logs.get_list(
    page=1,
    per_page=50,
    filter='status >= 400 || collection = "posts"',
    sort="-created",
)

for entry in logs["items"]:
    print(entry["status"], entry["method"], entry["url"])
```

### Retrieve a Single Log

```python
entry = pb.logs.get_one("LOG_ID")
print(entry["response"])
```

## Statistics

```python
stats = pb.logs.get_stats(query={"groupBy": "collection"})
for row in stats:
    print(row["collection"], row["total"])
```

Available aggregations mirror the dashboard (status, IP, collection, origin, etc.).

## Filtering & Fields

Supported query params:

- `filter`: expression using log fields (`status`, `ip`, `collection`, `rule`, etc.)
- `fields`: control payload size (`fields="id,status,collection"`)
- `sort`: e.g. `"-created"` or `"status"`
- `page` / `perPage`

## Use Cases

- **Debugging Rules:** filter on `rule` or `collection` to see which rules reject requests.
- **Monitoring:** send stats to Prometheus or other observability stacks.
- **Audit Trail:** export logs nightly using `get_full_list()` for compliance archives.

## Tips

1. Logs are only available to authenticated superusers.
2. Use filters to limit retained data when exporting (e.g. last 24 hours).
3. Pair log downloads with the Backups API to capture both metadata and content for DR plans.
