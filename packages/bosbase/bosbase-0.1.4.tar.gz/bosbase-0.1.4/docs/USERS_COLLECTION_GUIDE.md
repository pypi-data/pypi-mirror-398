# Built-in Users Collection Guide - JavaScript SDK

This guide explains how to use the built-in `users` collection for authentication, registration, and API rules. **The `users` collection is automatically created when BosBase is initialized and does not need to be created manually.**

## Table of Contents

1. [Overview](#overview)
2. [Users Collection Structure](#users-collection-structure)
3. [User Registration](#user-registration)
4. [User Login/Authentication](#user-loginauthentication)
5. [API Rules and Filters with Users](#api-rules-and-filters-with-users)
6. [Using Users with Other Collections](#using-users-with-other-collections)
7. [Complete Examples](#complete-examples)

---

## Overview

The `users` collection is a **built-in auth collection** that is automatically created when BosBase starts. It has:

- **Collection ID**: `_pb_users_auth_`
- **Collection Name**: `users`
- **Type**: `auth` (authentication collection)
- **Purpose**: User accounts, authentication, and authorization

**Important**: 
- ✅ **DO NOT** create a new `users` collection manually
- ✅ **DO** use the existing built-in `users` collection
- ✅ The collection already has proper API rules configured
- ✅ It supports password, OAuth2, and OTP authentication

### Getting Users Collection Information

```javascript
// Get the users collection details
const usersCollection = await pb.collections.getOne('users');
// or by ID
const usersCollection = await pb.collections.getOne('_pb_users_auth_');

console.log('Collection ID:', usersCollection.id);
console.log('Collection Name:', usersCollection.name);
console.log('Collection Type:', usersCollection.type);
console.log('Fields:', usersCollection.fields);
console.log('API Rules:', {
  listRule: usersCollection.listRule,
  viewRule: usersCollection.viewRule,
  createRule: usersCollection.createRule,
  updateRule: usersCollection.updateRule,
  deleteRule: usersCollection.deleteRule,
});
```

---

## Users Collection Structure

### System Fields (Automatically Created)

These fields are automatically added to all auth collections (including `users`):

| Field Name | Type | Description | Required | Hidden |
|------------|------|-------------|----------|--------|
| `id` | text | Unique record identifier | Yes | No |
| `email` | email | User email address | Yes* | No |
| `username` | text | Username (optional, if enabled) | No* | No |
| `password` | password | Hashed password | Yes* | Yes |
| `tokenKey` | text | Token key for auth tokens | Yes | Yes |
| `emailVisibility` | bool | Whether email is visible to others | No | No |
| `verified` | bool | Whether email is verified | No | No |
| `created` | date | Record creation timestamp | Yes | No |
| `updated` | date | Last update timestamp | Yes | No |

*Required based on authentication method configuration (password auth, username auth, etc.)

### Custom Fields (Pre-configured)

The built-in `users` collection includes these custom fields:

| Field Name | Type | Description | Required |
|------------|------|-------------|----------|
| `name` | text | User's display name | No (max: 255 characters) |
| `avatar` | file | User avatar image | No (max: 1 file, images only) |

### Default API Rules

The `users` collection comes with these default API rules:

```javascript
{
  listRule: "id = @request.auth.id",    // Users can only list themselves
  viewRule: "id = @request.auth.id",   // Users can only view themselves
  createRule: "",                       // Anyone can register (public)
  updateRule: "id = @request.auth.id", // Users can only update themselves
  deleteRule: "id = @request.auth.id"  // Users can only delete themselves
}
```

**Understanding the Rules:**

1. **`listRule: "id = @request.auth.id"`**
   - Users can only see their own record when listing
   - If not authenticated, returns empty list (not an error)
   - Superusers can see all users

2. **`viewRule: "id = @request.auth.id"`**
   - Users can only view their own record
   - If trying to view another user, returns 404
   - Superusers can view any user

3. **`createRule: ""`** (empty string)
   - **Public registration** - Anyone can create a user account
   - No authentication required
   - This enables self-registration

4. **`updateRule: "id = @request.auth.id"`**
   - Users can only update their own record
   - Prevents users from modifying other users' data
   - Superusers can update any user

5. **`deleteRule: "id = @request.auth.id"`**
   - Users can only delete their own account
   - Prevents users from deleting other users
   - Superusers can delete any user

**Note**: These rules ensure user privacy and security. Users can only access and modify their own data unless they are superusers.

---

## User Registration

### Basic Registration

Users can register by creating a record in the `users` collection. The `createRule` is set to `""` (empty string), meaning **anyone can register**.

```javascript
import BosBase from 'bosbase';

const pb = new BosBase('http://localhost:8090');

// Register a new user
const newUser = await pb.collection('users').create({
  email: 'user@example.com',
  password: 'securepassword123',
  passwordConfirm: 'securepassword123',
  name: 'John Doe',
});

console.log('User registered:', newUser.id);
console.log('Email:', newUser.email);
```

### Registration with Email Verification

```javascript
// Register user (verification email sent automatically if configured)
const newUser = await pb.collection('users').create({
  email: 'user@example.com',
  password: 'securepassword123',
  passwordConfirm: 'securepassword123',
  name: 'John Doe',
});

// User will receive verification email
// After clicking link, verified field becomes true
```

### Registration with Username

If username authentication is enabled in the collection settings:

```javascript
const newUser = await pb.collection('users').create({
  email: 'user@example.com',
  username: 'johndoe',
  password: 'securepassword123',
  passwordConfirm: 'securepassword123',
  name: 'John Doe',
});
```

### Registration with Avatar Upload

```javascript
const formData = new FormData();
formData.append('email', 'user@example.com');
formData.append('password', 'securepassword123');
formData.append('passwordConfirm', 'securepassword123');
formData.append('name', 'John Doe');
formData.append('avatar', avatarFile); // File from input

const newUser = await pb.collection('users').create(formData);
```

### Check if Email Exists

```javascript
try {
  const existing = await pb.collection('users').getFirstListItem(
    'email = "user@example.com"'
  );
  console.log('Email already exists');
} catch (err) {
  if (err.status === 404) {
    console.log('Email is available');
  }
}
```

---

## User Login/Authentication

### Password Authentication

```javascript
// Login with email and password
const authData = await pb.collection('users').authWithPassword(
  'user@example.com',
  'password123'
);

// Auth data is automatically stored
console.log(pb.authStore.isValid);  // true
console.log(pb.authStore.token);    // JWT token
console.log(pb.authStore.record);   // User record
```

### Login with Username

If username authentication is enabled:

```javascript
const authData = await pb.collection('users').authWithPassword(
  'johndoe',  // username instead of email
  'password123'
);
```

### OAuth2 Authentication

```javascript
// Login with OAuth2 (e.g., Google)
const authData = await pb.collection('users').authWithOAuth2({
  provider: 'google'
});

// If user doesn't exist, account is created automatically
console.log(pb.authStore.record);
```

### OTP Authentication

```javascript
// Step 1: Request OTP
const otpResult = await pb.collection('users').requestOTP('user@example.com');

// Step 2: Authenticate with OTP code from email
const authData = await pb.collection('users').authWithOTP(
  otpResult.otpId,
  '123456' // OTP code from email
);
```

### Check Current Authentication

```javascript
if (pb.authStore.isValid) {
  const user = pb.authStore.record;
  console.log('Logged in as:', user.email);
  console.log('User ID:', user.id);
  console.log('Name:', user.name);
} else {
  console.log('Not authenticated');
}
```

### Refresh Auth Token

```javascript
// Refresh the authentication token
await pb.collection('users').authRefresh();
```

### Logout

```javascript
pb.authStore.clear();
```

### Get Current User

```javascript
const currentUser = pb.authStore.record;
if (currentUser) {
  console.log('Current user:', currentUser.email);
  console.log('User ID:', currentUser.id);
  console.log('Name:', currentUser.name);
  console.log('Verified:', currentUser.verified);
}
```

### Accessing User Fields

```javascript
// After authentication, access user fields
const user = pb.authStore.record;

// System fields
console.log(user.id);                    // User ID
console.log(user.email);                 // Email
console.log(user.username);              // Username (if enabled)
console.log(user.verified);              // Email verification status
console.log(user.emailVisibility);       // Email visibility setting
console.log(user.created);               // Creation date
console.log(user.updated);               // Last update date

// Custom fields (from users collection)
console.log(user.name);                  // Display name
console.log(user.avatar);                // Avatar filename

// Access via data object (alternative)
console.log(user.data.email);
console.log(user.data.name);
```

---

## API Rules and Filters with Users

### Understanding @request.auth

The `@request.auth` identifier provides access to the currently authenticated user's data in API rules and filters.

**Available Properties:**
- `@request.auth.id` - User's record ID
- `@request.auth.email` - User's email
- `@request.auth.username` - User's username (if enabled)
- `@request.auth.*` - Any field from the user record

### Common API Rule Patterns

#### 1. Require Authentication

```javascript
// Only authenticated users can access
listRule: '@request.auth.id != ""'
viewRule: '@request.auth.id != ""'
createRule: '@request.auth.id != ""'
```

#### 2. Owner-Based Access

```javascript
// Users can only access their own records
viewRule: 'author = @request.auth.id'
updateRule: 'author = @request.auth.id'
deleteRule: 'author = @request.auth.id'
```

#### 3. Public with User-Specific Data

```javascript
// Public can see published, users can see their own
listRule: '@request.auth.id != "" && author = @request.auth.id || status = "published"'
viewRule: '@request.auth.id != "" && author = @request.auth.id || status = "published"'
```

#### 4. Role-Based Access (if you add a role field)

```javascript
// Assuming you add a 'role' select field to users collection
listRule: '@request.auth.id != "" && @request.auth.role = "admin"'
updateRule: '@request.auth.role = "admin" || author = @request.auth.id'
```

#### 5. Verified Users Only

```javascript
// Only verified users can create
createRule: '@request.auth.id != "" && @request.auth.verified = true'
```

### Setting API Rules for Other Collections

When creating collections that relate to users:

```javascript
// Create posts collection with user-based rules
const postsCollection = await pb.collections.create({
  name: 'posts',
  type: 'base',
  fields: [
    {
      name: 'title',
      type: 'text',
      required: true,
    },
    {
      name: 'content',
      type: 'editor',
    },
    {
      name: 'author',
      type: 'relation',
      collectionId: '_pb_users_auth_', // Reference to users collection
      maxSelect: 1,
      required: true,
    },
    {
      name: 'status',
      type: 'select',
      options: {
        values: ['draft', 'published'],
      },
    },
  ],
  // Public can see published posts, users can see their own
  listRule: '@request.auth.id != "" && author = @request.auth.id || status = "published"',
  viewRule: '@request.auth.id != "" && author = @request.auth.id || status = "published"',
  // Only authenticated users can create
  createRule: '@request.auth.id != ""',
  // Only authors can update their posts
  updateRule: 'author = @request.auth.id',
  // Only authors can delete their posts
  deleteRule: 'author = @request.auth.id',
});
```

### Using Filters with Users

```javascript
// Get posts by current user
const myPosts = await pb.collection('posts').getList(1, 20, {
  filter: 'author = @request.auth.id',
});

// Get posts by verified users only
const verifiedPosts = await pb.collection('posts').getList(1, 20, {
  filter: 'author.verified = true',
  expand: 'author',
});

// Get posts where author name contains "John"
const posts = await pb.collection('posts').getList(1, 20, {
  filter: 'author.name ~ "John"',
  expand: 'author',
});
```

---

## Using Users with Other Collections

### Creating Relations to Users

When creating collections that need to reference users:

```javascript
// Create a posts collection with author relation
const postsCollection = await pb.collections.create({
  name: 'posts',
  type: 'base',
  fields: [
    {
      name: 'title',
      type: 'text',
      required: true,
    },
    {
      name: 'author',
      type: 'relation',
      collectionId: '_pb_users_auth_', // Users collection ID
      // OR use collection name
      // collectionName: 'users',
      maxSelect: 1,
      required: true,
    },
  ],
});
```

### Creating Records with User Relations

```javascript
// Authenticate first
await pb.collection('users').authWithPassword('user@example.com', 'password');

// Create a post with current user as author
const post = await pb.collection('posts').create({
  title: 'My First Post',
  author: pb.authStore.record.id, // Current user's ID
});
```

### Querying with User Relations

```javascript
// Get posts with author information
const posts = await pb.collection('posts').getList(1, 20, {
  expand: 'author', // Expand the author relation
});

posts.items.forEach(post => {
  console.log('Post:', post.title);
  console.log('Author:', post.expand.author.name);
  console.log('Author Email:', post.expand.author.email);
});

// Filter posts by author
const userPosts = await pb.collection('posts').getList(1, 20, {
  filter: 'author = "USER_ID"',
  expand: 'author',
});
```

### Updating User Profile

```javascript
// Users can update their own profile
await pb.collection('users').update(pb.authStore.record.id, {
  name: 'Updated Name',
});

// Update with avatar
const formData = new FormData();
formData.append('name', 'New Name');
formData.append('avatar', newAvatarFile);

await pb.collection('users').update(pb.authStore.record.id, formData);
```

---

## Complete Examples

### Example 1: User Registration and Login Flow

```javascript
import BosBase from 'bosbase';

const pb = new BosBase('http://localhost:8090');

async function registerAndLogin() {
  try {
    // 1. Register new user
    const newUser = await pb.collection('users').create({
      email: 'newuser@example.com',
      password: 'securepassword123',
      passwordConfirm: 'securepassword123',
      name: 'New User',
    });
    
    console.log('Registration successful:', newUser.id);
    
    // 2. Login with credentials
    const authData = await pb.collection('users').authWithPassword(
      'newuser@example.com',
      'securepassword123'
    );
    
    console.log('Login successful');
    console.log('Token:', authData.token);
    console.log('User:', authData.record);
    
    return authData;
  } catch (err) {
    console.error('Error:', err.message);
    if (err.data) {
      console.error('Validation errors:', err.data);
    }
  }
}

registerAndLogin();
```

### Example 2: Creating User-Related Collections

```javascript
import BosBase from 'bosbase';

const pb = new BosBase('http://localhost:8090');

// Authenticate as superuser to create collections
await pb.admins.authWithPassword('admin@example.com', 'adminpassword');

async function setupUserRelatedCollections() {
  // Create posts collection linked to users
  const postsCollection = await pb.collections.create({
    name: 'posts',
    type: 'base',
    fields: [
      {
        name: 'title',
        type: 'text',
        required: true,
      },
      {
        name: 'content',
        type: 'editor',
      },
      {
        name: 'author',
        type: 'relation',
        collectionId: '_pb_users_auth_', // Link to users
        maxSelect: 1,
        required: true,
      },
      {
        name: 'status',
        type: 'select',
        options: {
          values: ['draft', 'published'],
        },
      },
    ],
    // API rules using users collection
    listRule: '@request.auth.id != "" && author = @request.auth.id || status = "published"',
    viewRule: '@request.auth.id != "" && author = @request.auth.id || status = "published"',
    createRule: '@request.auth.id != ""',
    updateRule: 'author = @request.auth.id',
    deleteRule: 'author = @request.auth.id',
  });
  
  // Create comments collection
  const commentsCollection = await pb.collections.create({
    name: 'comments',
    type: 'base',
    fields: [
      {
        name: 'content',
        type: 'text',
        required: true,
      },
      {
        name: 'post',
        type: 'relation',
        collectionId: postsCollection.id,
        maxSelect: 1,
        required: true,
      },
      {
        name: 'author',
        type: 'relation',
        collectionId: '_pb_users_auth_', // Link to users
        maxSelect: 1,
        required: true,
      },
    ],
    listRule: '@request.auth.id != ""',
    viewRule: '@request.auth.id != ""',
    createRule: '@request.auth.id != ""',
    updateRule: 'author = @request.auth.id',
    deleteRule: 'author = @request.auth.id',
  });
  
  console.log('Collections created successfully');
}

setupUserRelatedCollections();
```

### Example 3: User Creates and Manages Their Posts

```javascript
import BosBase from 'bosbase';

const pb = new BosBase('http://localhost:8090');

async function userPostManagement() {
  // 1. User logs in
  await pb.collection('users').authWithPassword('user@example.com', 'password');
  const userId = pb.authStore.record.id;
  
  // 2. User creates a post
  const post = await pb.collection('posts').create({
    title: 'My First Post',
    content: 'This is my content',
    author: userId,
    status: 'draft',
  });
  
  console.log('Post created:', post.id);
  
  // 3. User lists their own posts
  const myPosts = await pb.collection('posts').getList(1, 20, {
    filter: `author = "${userId}"`,
    sort: '-created',
  });
  
  console.log('My posts:', myPosts.items.length);
  
  // 4. User updates their post
  await pb.collection('posts').update(post.id, {
    title: 'Updated Title',
    status: 'published',
  });
  
  // 5. User views their post with author info
  const updatedPost = await pb.collection('posts').getOne(post.id, {
    expand: 'author',
  });
  
  console.log('Post author:', updatedPost.expand.author.name);
  
  // 6. User deletes their post
  await pb.collection('posts').delete(post.id);
  
  console.log('Post deleted');
}

userPostManagement();
```

### Example 4: Public Posts with User Information

```javascript
import BosBase from 'bosbase';

const pb = new BosBase('http://localhost:8090');

async function viewPublicPosts() {
  // No authentication required for public posts
  
  // Get published posts with author information
  const posts = await pb.collection('posts').getList(1, 20, {
    filter: 'status = "published"',
    expand: 'author',
    sort: '-created',
  });
  
  posts.items.forEach(post => {
    console.log('Title:', post.title);
    console.log('Author:', post.expand.author.name);
    // Email visibility depends on author's emailVisibility setting
    if (post.expand.author.emailVisibility) {
      console.log('Author Email:', post.expand.author.email);
    }
  });
}

viewPublicPosts();
```

### Example 5: Email Verification Flow

```javascript
import BosBase from 'bosbase';

const pb = new BosBase('http://localhost:8090');

async function emailVerificationFlow() {
  // 1. User registers
  const newUser = await pb.collection('users').create({
    email: 'user@example.com',
    password: 'password123',
    passwordConfirm: 'password123',
    name: 'User Name',
  });
  
  console.log('User registered, verification email sent');
  console.log('Verified status:', newUser.verified); // false
  
  // 2. User clicks verification link in email
  // (This is handled by the backend automatically)
  
  // 3. Check verification status
  const user = await pb.collection('users').getOne(newUser.id);
  console.log('Verified:', user.verified);
  
  // 4. Request new verification email if needed
  await pb.collection('users').requestVerification('user@example.com');
}

emailVerificationFlow();
```

### Example 6: Password Reset Flow

```javascript
import BosBase from 'bosbase';

const pb = new BosBase('http://localhost:8090');

async function passwordResetFlow() {
  // 1. User requests password reset
  await pb.collection('users').requestPasswordReset('user@example.com');
  console.log('Password reset email sent');
  
  // 2. User clicks link in email and gets reset token
  // (Token is in the URL query parameter)
  
  // 3. User confirms password reset with token
  await pb.collection('users').confirmPasswordReset(
    'RESET_TOKEN_FROM_EMAIL',
    'newpassword123',
    'newpassword123' // passwordConfirm
  );
  
  console.log('Password reset successful');
  
  // 4. User can now login with new password
  await pb.collection('users').authWithPassword(
    'user@example.com',
    'newpassword123'
  );
}

passwordResetFlow();
```

### Example 7: Using Users in API Rules for Other Collections

```javascript
import BosBase from 'bosbase';

const pb = new BosBase('http://localhost:8090');

// Authenticate as superuser
await pb.admins.authWithPassword('admin@example.com', 'adminpassword');

// Create a blog system with user-based access control
async function createBlogSystem() {
  // Create posts collection
  const posts = await pb.collections.create({
    name: 'posts',
    type: 'base',
    fields: [
      { name: 'title', type: 'text', required: true },
      { name: 'content', type: 'editor' },
      { name: 'author', type: 'relation', collectionId: '_pb_users_auth_', maxSelect: 1, required: true },
      { name: 'status', type: 'select', options: { values: ['draft', 'published'] } },
    ],
    // Public can see published, authors can see their own
    listRule: 'status = "published" || author = @request.auth.id',
    viewRule: 'status = "published" || author = @request.auth.id',
    createRule: '@request.auth.id != ""',
    updateRule: 'author = @request.auth.id',
    deleteRule: 'author = @request.auth.id',
  });
  
  // Create comments collection
  const comments = await pb.collections.create({
    name: 'comments',
    type: 'base',
    fields: [
      { name: 'content', type: 'text', required: true },
      { name: 'post', type: 'relation', collectionId: posts.id, maxSelect: 1, required: true },
      { name: 'author', type: 'relation', collectionId: '_pb_users_auth_', maxSelect: 1, required: true },
    ],
    // Anyone can see comments on published posts, authors can see their own
    listRule: 'post.status = "published" || author = @request.auth.id',
    viewRule: 'post.status = "published" || author = @request.auth.id',
    createRule: '@request.auth.id != "" && post.status = "published"',
    updateRule: 'author = @request.auth.id',
    deleteRule: 'author = @request.auth.id',
  });
  
  console.log('Blog system created with user-based access control');
}

createBlogSystem();
```

---

## Best Practices

1. **Always use the built-in `users` collection** - Don't create a new one
2. **Use `_pb_users_auth_` as collectionId** when creating relations
3. **Check authentication** before user-specific operations
4. **Use `@request.auth.id`** in API rules for user-based access control
5. **Expand user relations** when you need user information
6. **Respect emailVisibility** - Don't expose emails unless user allows it
7. **Handle verification** - Check `verified` field for email verification status
8. **Use proper error handling** for registration/login failures

---

## Common Patterns

### Pattern 1: Owner-Only Access

```javascript
// Users can only access their own records
updateRule: 'author = @request.auth.id'
deleteRule: 'author = @request.auth.id'
```

### Pattern 2: Public Read, Authenticated Write

```javascript
listRule: 'status = "published" || author = @request.auth.id'
viewRule: 'status = "published" || author = @request.auth.id'
createRule: '@request.auth.id != ""'
```

### Pattern 3: Verified Users Only

```javascript
createRule: '@request.auth.id != "" && @request.auth.verified = true'
```

### Pattern 4: Filter by Current User

```javascript
const myRecords = await pb.collection('posts').getList(1, 20, {
  filter: `author = "${pb.authStore.record.id}"`,
});
```

---

This guide covers all essential operations with the built-in `users` collection. Remember: **always use the existing `users` collection, never create a new one manually.**

