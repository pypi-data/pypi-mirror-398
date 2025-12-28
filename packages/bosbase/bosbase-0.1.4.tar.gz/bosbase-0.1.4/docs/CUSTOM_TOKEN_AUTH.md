# Custom Token Binding and Login

The JS SDK and BosBase service now support binding a custom token to an auth record (both `users` and `_superusers`) and signing in with that token. The server stores bindings in the `_token_bindings` table (created automatically on first bind; legacy `_tokenBindings`/`tokenBindings` are auto-renamed). Tokens are stored as hashes so raw values aren't persisted.

## API endpoints
- `POST /api/collections/{collection}/bind-token`
- `POST /api/collections/{collection}/unbind-token`
- `POST /api/collections/{collection}/auth-with-token`

## Binding a token
```ts
import Client from "@bosbase/js-sdk";

const pb = new Client("http://127.0.0.1:8090");

// bind for a regular user
await pb.collection("users").bindCustomToken(
    "user@example.com",
    "user-password",
    "my-app-token",
);

// bind for a superuser
await pb.collection("_superusers").bindCustomToken(
    "admin@example.com",
    "admin-password",
    "admin-app-token",
);
```

## Unbinding a token
```ts
// stop accepting the token for the user
await pb.collection("users").unbindCustomToken(
    "user@example.com",
    "user-password",
    "my-app-token",
);

// stop accepting the token for a superuser
await pb.collection("_superusers").unbindCustomToken(
    "admin@example.com",
    "admin-password",
    "admin-app-token",
);
```

## Logging in with a token
```ts
// login with the previously bound token
const auth = await pb.collection("users").authWithToken("my-app-token");

console.log(auth.token);  // BosBase auth token
console.log(auth.record); // authenticated record

// superuser token login
const superAuth = await pb.collection("_superusers").authWithToken("admin-app-token");
console.log(superAuth.token);
console.log(superAuth.record);
```

Notes:
- Binding and unbinding require a valid email and password for the target account.
- The same token value can be used for either `users` or `_superusers` collections; the collection is enforced during login.
- MFA and existing auth rules still apply when authenticating with a token.
