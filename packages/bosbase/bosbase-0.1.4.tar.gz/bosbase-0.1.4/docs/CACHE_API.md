# Cache API - Python SDK

The Cache API lets you manage BosBase's built-in key/value caches programmatically.

## Listing Caches

```python
caches = pb.caches.list()
for cache in caches:
    print(cache["name"], cache["sizeBytes"])
```

## Creating & Updating Caches

```python
pb.caches.create(
    "locks",
    size_bytes=1_000_000,
    default_ttl_seconds=300,
    read_timeout_ms=500,
)

pb.caches.update(
    "locks",
    body={"defaultTTLSeconds": 600},
)
```

## Deleting Caches

```python
pb.caches.delete("locks")
```

## Working with Entries

```python
pb.caches.set_entry("locks", "job:123", {"status": "running"}, ttl_seconds=60)

entry = pb.caches.get_entry("locks", "job:123")
print(entry["value"])

pb.caches.renew_entry("locks", "job:123", ttl_seconds=120)
pb.caches.delete_entry("locks", "job:123")
```

Entries are arbitrary JSON values. Use TTLs for auto-expiry.

## Tips

1. Keep cache names short and lowercase; they map to file paths on disk.
2. Monitor cache hit/miss via request logs (look for cache endpoints).
3. Use caches for distributed locks, memoization, or throttling state.
4. Set conservative timeouts (`readTimeoutMs`) when storing values that require synchronous lookups during API requests.
