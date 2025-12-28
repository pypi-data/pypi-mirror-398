# OAuth2 Configuration Guide

This guide explains how to configure OAuth2 authentication providers for auth collections using the BosBase JavaScript SDK.

## Overview

OAuth2 allows users to authenticate with your application using third-party providers like Google, GitHub, Facebook, etc. Before you can use OAuth2 authentication, you need to:

1. **Create an OAuth2 app** in the provider's dashboard
2. **Obtain Client ID and Client Secret** from the provider
3. **Register a redirect URL** (typically: `https://yourdomain.com/api/oauth2-redirect`)
4. **Configure the provider** in your BosBase auth collection using the SDK

## Prerequisites

- An auth collection in your BosBase instance
- OAuth2 app credentials (Client ID and Client Secret) from your chosen provider
- Admin/superuser authentication to configure collections

## Supported Providers

The following OAuth2 providers are supported:

- **google** - Google OAuth2
- **github** - GitHub OAuth2
- **gitlab** - GitLab OAuth2
- **discord** - Discord OAuth2
- **facebook** - Facebook OAuth2
- **microsoft** - Microsoft OAuth2
- **apple** - Apple Sign In
- **twitter** - Twitter OAuth2
- **spotify** - Spotify OAuth2
- **kakao** - Kakao OAuth2
- **twitch** - Twitch OAuth2
- **strava** - Strava OAuth2
- **vk** - VK OAuth2
- **yandex** - Yandex OAuth2
- **patreon** - Patreon OAuth2
- **linkedin** - LinkedIn OAuth2
- **instagram** - Instagram OAuth2
- **vimeo** - Vimeo OAuth2
- **digitalocean** - DigitalOcean OAuth2
- **bitbucket** - Bitbucket OAuth2
- **dropbox** - Dropbox OAuth2
- **planningcenter** - Planning Center OAuth2
- **notion** - Notion OAuth2
- **linear** - Linear OAuth2
- **oidc**, **oidc2**, **oidc3** - OpenID Connect (OIDC) providers

## Basic Usage

### 1. Enable OAuth2 for a Collection

First, enable OAuth2 authentication for your auth collection:

```typescript
import { Bosbase } from 'bosbase';

const pb = new Bosbase('https://your-instance.com');

// Authenticate as admin
await pb.admins.authWithPassword('admin@example.com', 'password');

// Enable OAuth2 for the "users" collection
await pb.collections.enableOAuth2('users');
```

### 2. Add an OAuth2 Provider

Add a provider configuration to your collection. You'll need the URLs and credentials from your OAuth2 app:

```typescript
// Add Google OAuth2 provider
await pb.collections.addOAuth2Provider('users', {
    name: 'google',
    clientId: 'your-google-client-id',
    clientSecret: 'your-google-client-secret',
    authURL: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenURL: 'https://oauth2.googleapis.com/token',
    userInfoURL: 'https://www.googleapis.com/oauth2/v2/userinfo',
    displayName: 'Google',
    pkce: true, // Optional: enable PKCE if supported
});
```

### 3. Configure Field Mapping

Map OAuth2 provider fields to your collection fields:

```typescript
await pb.collections.setOAuth2MappedFields('users', {
    name: 'name',        // OAuth2 "name" → collection "name"
    email: 'email',      // OAuth2 "email" → collection "email"
    avatarUrl: 'avatar', // OAuth2 "avatarUrl" → collection "avatar"
});
```

### 4. Get OAuth2 Configuration

Retrieve the current OAuth2 configuration:

```typescript
const config = await pb.collections.getOAuth2Config('users');
console.log(config.enabled);        // true/false
console.log(config.providers);      // Array of providers
console.log(config.mappedFields);   // Field mappings
```

### 5. Update a Provider

Update an existing provider's configuration:

```typescript
await pb.collections.updateOAuth2Provider('users', 'google', {
    clientId: 'new-client-id',
    clientSecret: 'new-client-secret',
});
```

### 6. Remove a Provider

Remove an OAuth2 provider:

```typescript
await pb.collections.removeOAuth2Provider('users', 'google');
```

### 7. Disable OAuth2

Disable OAuth2 authentication for a collection:

```typescript
await pb.collections.disableOAuth2('users');
```

## Complete Example

Here's a complete example of setting up Google OAuth2:

```typescript
import { Bosbase } from 'bosbase';

const pb = new Bosbase('https://your-instance.com');

// Authenticate as admin
await pb.admins.authWithPassword('admin@example.com', 'password');

try {
    // 1. Enable OAuth2
    await pb.collections.enableOAuth2('users');
    
    // 2. Add Google provider
    await pb.collections.addOAuth2Provider('users', {
        name: 'google',
        clientId: 'your-google-client-id.apps.googleusercontent.com',
        clientSecret: 'your-google-client-secret',
        authURL: 'https://accounts.google.com/o/oauth2/v2/auth',
        tokenURL: 'https://oauth2.googleapis.com/token',
        userInfoURL: 'https://www.googleapis.com/oauth2/v2/userinfo',
        displayName: 'Google',
        pkce: true,
    });
    
    // 3. Configure field mappings
    await pb.collections.setOAuth2MappedFields('users', {
        name: 'name',
        email: 'email',
        avatarUrl: 'avatar',
    });
    
    console.log('OAuth2 configuration completed successfully!');
} catch (error) {
    console.error('Error configuring OAuth2:', error);
}
```

## Provider-Specific Examples

### GitHub

```typescript
await pb.collections.addOAuth2Provider('users', {
    name: 'github',
    clientId: 'your-github-client-id',
    clientSecret: 'your-github-client-secret',
    authURL: 'https://github.com/login/oauth/authorize',
    tokenURL: 'https://github.com/login/oauth/access_token',
    userInfoURL: 'https://api.github.com/user',
    displayName: 'GitHub',
    pkce: false,
});
```

### Discord

```typescript
await pb.collections.addOAuth2Provider('users', {
    name: 'discord',
    clientId: 'your-discord-client-id',
    clientSecret: 'your-discord-client-secret',
    authURL: 'https://discord.com/api/oauth2/authorize',
    tokenURL: 'https://discord.com/api/oauth2/token',
    userInfoURL: 'https://discord.com/api/users/@me',
    displayName: 'Discord',
    pkce: true,
});
```

### Microsoft

```typescript
await pb.collections.addOAuth2Provider('users', {
    name: 'microsoft',
    clientId: 'your-microsoft-client-id',
    clientSecret: 'your-microsoft-client-secret',
    authURL: 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
    tokenURL: 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
    userInfoURL: 'https://graph.microsoft.com/v1.0/me',
    displayName: 'Microsoft',
    pkce: true,
});
```

## Important Notes

1. **Redirect URL**: When creating your OAuth2 app in the provider's dashboard, you must register the redirect URL as: `https://yourdomain.com/api/oauth2-redirect`

2. **Provider Names**: The `name` field must match one of the supported provider names exactly (case-sensitive).

3. **PKCE Support**: Some providers support PKCE (Proof Key for Code Exchange) for enhanced security. Check your provider's documentation to determine if PKCE should be enabled.

4. **Client Secret Security**: Never expose your client secret in client-side code. These configuration methods should only be called from server-side code or with proper authentication.

5. **Field Mapping**: The mapped fields determine how OAuth2 user data is mapped to your collection fields. Common OAuth2 fields include:
   - `name` - User's full name
   - `email` - User's email address
   - `avatarUrl` - User's avatar/profile picture URL
   - `username` - User's username

6. **Multiple Providers**: You can add multiple OAuth2 providers to the same collection. Users can choose which provider to use during authentication.

## Error Handling

All methods throw `ClientResponseError` if something goes wrong:

```typescript
try {
    await pb.collections.addOAuth2Provider('users', providerConfig);
} catch (error) {
    if (error.status === 400) {
        console.error('Invalid provider configuration:', error.data);
    } else if (error.status === 403) {
        console.error('Permission denied. Make sure you are authenticated as admin.');
    } else {
        console.error('Unexpected error:', error);
    }
}
```

## API Reference

### `enableOAuth2(collectionIdOrName, options?)`

Enables OAuth2 authentication for an auth collection.

**Parameters:**
- `collectionIdOrName` (string) - Collection id or name
- `options` (CommonOptions, optional) - Request options

**Returns:** `Promise<CollectionModel>`

**Throws:** Error if collection is not an auth collection

---

### `disableOAuth2(collectionIdOrName, options?)`

Disables OAuth2 authentication for an auth collection.

**Parameters:**
- `collectionIdOrName` (string) - Collection id or name
- `options` (CommonOptions, optional) - Request options

**Returns:** `Promise<CollectionModel>`

**Throws:** Error if collection is not an auth collection

---

### `getOAuth2Config(collectionIdOrName, options?)`

Gets the OAuth2 configuration for an auth collection.

**Parameters:**
- `collectionIdOrName` (string) - Collection id or name
- `options` (CommonOptions, optional) - Request options

**Returns:** `Promise<{ enabled: boolean; mappedFields: { [key: string]: string }; providers: Array<any> }>`

**Throws:** Error if collection is not an auth collection

---

### `setOAuth2MappedFields(collectionIdOrName, mappedFields, options?)`

Sets the OAuth2 mapped fields for an auth collection.

**Parameters:**
- `collectionIdOrName` (string) - Collection id or name
- `mappedFields` (object) - Object mapping OAuth2 fields to collection fields
- `options` (CommonOptions, optional) - Request options

**Returns:** `Promise<CollectionModel>`

**Throws:** Error if collection is not an auth collection

---

### `addOAuth2Provider(collectionIdOrName, provider, options?)`

Adds a new OAuth2 provider to an auth collection.

**Parameters:**
- `collectionIdOrName` (string) - Collection id or name
- `provider` (object) - OAuth2 provider configuration:
  - `name` (string, required) - Provider name
  - `clientId` (string, required) - OAuth2 client ID
  - `clientSecret` (string, required) - OAuth2 client secret
  - `authURL` (string, required) - Authorization URL
  - `tokenURL` (string, required) - Token exchange URL
  - `userInfoURL` (string, required) - User info API URL
  - `displayName` (string, optional) - Display name for the provider
  - `pkce` (boolean, optional) - Enable PKCE
  - `extra` (object, optional) - Additional provider-specific configuration
- `options` (CommonOptions, optional) - Request options

**Returns:** `Promise<CollectionModel>`

**Throws:** Error if collection is not an auth collection or provider is invalid

---

### `updateOAuth2Provider(collectionIdOrName, providerName, updates, options?)`

Updates an existing OAuth2 provider in an auth collection.

**Parameters:**
- `collectionIdOrName` (string) - Collection id or name
- `providerName` (string) - Name of the provider to update
- `updates` (object) - Partial provider configuration to update
- `options` (CommonOptions, optional) - Request options

**Returns:** `Promise<CollectionModel>`

**Throws:** Error if collection is not an auth collection or provider not found

---

### `removeOAuth2Provider(collectionIdOrName, providerName, options?)`

Removes an OAuth2 provider from an auth collection.

**Parameters:**
- `collectionIdOrName` (string) - Collection id or name
- `providerName` (string) - Name of the provider to remove
- `options` (CommonOptions, optional) - Request options

**Returns:** `Promise<CollectionModel>`

**Throws:** Error if collection is not an auth collection or provider not found

---

## Next Steps

After configuring OAuth2 providers, users can authenticate using the `authWithOAuth2()` method. See the [Authentication Guide](./AUTHENTICATION.md) for details on using OAuth2 authentication in your application.

