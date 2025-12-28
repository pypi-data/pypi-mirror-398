# Redis API (JS SDK)

Redis support is powered by [rueidis](https://github.com/redis/rueidis) and is **disabled unless `REDIS_URL` is provided** on the server. `REDIS_PASSWORD` is optional for instances that don’t use auth. Routes are superuser-only; regular users and misconfigured nodes simply won't expose the endpoints.

- Set `REDIS_URL` (eg. `redis://redis:6379` or `rediss://cache:6379`). Optionally set `REDIS_PASSWORD`.
- Authenticate as a superuser before calling the Redis endpoints.
- When `ttlSeconds` is omitted during updates, the existing TTL is preserved. Use `ttlSeconds: 0` to remove a TTL, or a positive value to set a new one.

## Discover keys

```ts
import BosBase from "bosbase";

const pb = new BosBase("http://127.0.0.1:8090");
await pb.admins.authWithPassword("root@example.com", "hunter2");

// Scan keys with an optional cursor, match pattern, and count hint.
const page = await pb.redis.listKeys({ pattern: "session:*", count: 100 });
console.log(page.cursor); // pass this back into listKeys to continue scanning
console.log(page.items);  // [{ key: "session:123" }, ...]
```

## Create, read, update, delete keys

```ts
// Create a key if it does NOT already exist.
await pb.redis.createKey({
  key: "session:123",
  value: { prompt: "hello", tokens: 42 },
  ttlSeconds: 3600, // optional
});

// Read the value back with the current TTL (if any).
const entry = await pb.redis.getKey<{ prompt: string; tokens: number }>("session:123");
console.log(entry.value, entry.ttlSeconds); // ttlSeconds is undefined when the key is persistent

// Update an existing key (preserves TTL when ttlSeconds is omitted).
await pb.redis.updateKey("session:123", {
  value: { prompt: "updated", tokens: 99 },
  // ttlSeconds: 0   // uncomment to remove TTL
  // ttlSeconds: 120 // or set a new TTL
});

// Delete the key.
await pb.redis.deleteKey("session:123");
```

API responses:
- `listKeys` returns `{ cursor: string, items: Array<{ key: string }> }`.
- `createKey`, `getKey`, and `updateKey` return `{ key, value, ttlSeconds? }`.
- `createKey` fails with HTTP 409 if the key already exists.
