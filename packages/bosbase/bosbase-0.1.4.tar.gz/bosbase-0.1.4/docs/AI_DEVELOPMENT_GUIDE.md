# AI Development Guide - JavaScript SDK

This guide provides a comprehensive, fast reference for AI systems to quickly develop applications using the BosBase JavaScript SDK. All examples are production-ready and follow best practices.

## Table of Contents

1. [Authentication](#authentication)
2. [Initialize Collections](#initialize-collections)
3. [Define Collection Fields](#define-collection-fields)
4. [Add Data to Collections](#add-data-to-collections)
5. [Modify Collection Data](#modify-collection-data)
6. [Delete Data from Collections](#delete-data-from-collections)
7. [Query Collection Contents](#query-collection-contents)
8. [Add and Delete Fields from Collections](#add-and-delete-fields-from-collections)
9. [Query Collection Field Information](#query-collection-field-information)
10. [Upload Files](#upload-files)
11. [Query Logs](#query-logs)
12. [Send Emails](#send-emails)

---

## Authentication

### Initialize Client

```javascript
import BosBase from 'bosbase';

const pb = new BosBase('http://localhost:8090');
```

### Password Authentication

```javascript
// Authenticate with email/username and password
const authData = await pb.collection('users').authWithPassword(
  'user@example.com',
  'password123'
);

// Auth data is automatically stored
console.log(pb.authStore.isValid);  // true
console.log(pb.authStore.token);    // JWT token
console.log(pb.authStore.record);   // User record
```

### OAuth2 Authentication

```javascript
// Get OAuth2 providers
const methods = await pb.collection('users').listAuthMethods();
console.log(methods.oauth2.providers); // Available providers

// Authenticate with OAuth2
const authData = await pb.collection('users').authWithOAuth2({
  provider: 'google',
  urlCallback: (url) => {
    // Open OAuth2 URL in browser
    window.open(url);
  },
});
```

### OTP Authentication

```javascript
// Request OTP
const otpResponse = await pb.collection('users').requestVerification('user@example.com');

// Authenticate with OTP
const authData = await pb.collection('users').authWithOTP(
  otpResponse.otpId,
  '123456' // OTP code
);
```

### Check Authentication Status

```javascript
if (pb.authStore.isValid) {
  console.log('Authenticated as:', pb.authStore.record.email);
} else {
  console.log('Not authenticated');
}
```

### Logout

```javascript
pb.authStore.clear();
```

---

## Initialize Collections

### Create Base Collection

```javascript
const collection = await pb.collections.create({
  name: 'posts',
  type: 'base',
  fields: [
    {
      name: 'title',
      type: 'text',
      required: true,
    },
  ],
});

console.log('Collection ID:', collection.id);
```

### Create Auth Collection

```javascript
const authCollection = await pb.collections.create({
  name: 'users',
  type: 'auth',
  fields: [
    {
      name: 'name',
      type: 'text',
      required: false,
    },
  ],
  passwordAuth: {
    enabled: true,
    identityFields: ['email', 'username'],
  },
});
```

### Create View Collection

```javascript
const viewCollection = await pb.collections.create({
  name: 'published_posts',
  type: 'view',
  viewQuery: 'SELECT * FROM posts WHERE published = true',
});
```

### Get Collection by ID or Name

```javascript
const collection = await pb.collections.getOne('posts');
// or by ID
const collection = await pb.collections.getOne('_pbc_2287844090');
```

---

## Define Collection Fields

### Add Field to Collection

```javascript
const updatedCollection = await pb.collections.addField('posts', {
  name: 'content',
  type: 'editor',
  required: false,
});
```

### Common Field Types

```javascript
// Text field
{
  name: 'title',
  type: 'text',
  required: true,
  min: 10,
  max: 255,
}

// Number field
{
  name: 'views',
  type: 'number',
  required: false,
  min: 0,
}

// Boolean field
{
  name: 'published',
  type: 'bool',
  required: false,
}

// Date field
{
  name: 'published_at',
  type: 'date',
  required: false,
}

// File field
{
  name: 'avatar',
  type: 'file',
  required: false,
  maxSelect: 1,
  maxSize: 2097152, // 2MB
  mimeTypes: ['image/jpeg', 'image/png'],
}

// Relation field
{
  name: 'author',
  type: 'relation',
  required: true,
  collectionId: '_pbc_users_auth_',
  maxSelect: 1,
}

// Select field
{
  name: 'status',
  type: 'select',
  required: true,
  options: {
    values: ['draft', 'published', 'archived'],
  },
}
```

### Update Field

```javascript
const updatedCollection = await pb.collections.updateField('posts', 'title', {
  max: 500,
  required: true,
});
```

### Remove Field

```javascript
const updatedCollection = await pb.collections.removeField('posts', 'old_field');
```

---

## Add Data to Collections

### Create Single Record

```javascript
const record = await pb.collection('posts').create({
  title: 'My First Post',
  content: 'This is the content',
  published: true,
});

console.log('Created record ID:', record.id);
```

### Create Record with File Upload

```javascript
const formData = new FormData();
formData.append('title', 'Post with Image');
formData.append('image', fileInput.files[0]); // File from input

const record = await pb.collection('posts').create(formData);
```

### Create Record with Relations

```javascript
const record = await pb.collection('posts').create({
  title: 'My Post',
  author: 'user_record_id', // Related record ID
  categories: ['cat1_id', 'cat2_id'], // Multiple relations
});
```

### Batch Create Records

```javascript
const records = await pb.batch([
  {
    method: 'POST',
    url: '/api/collections/posts/records',
    body: { title: 'Post 1' },
  },
  {
    method: 'POST',
    url: '/api/collections/posts/records',
    body: { title: 'Post 2' },
  },
]);
```

---

## Modify Collection Data

### Update Single Record

```javascript
const updated = await pb.collection('posts').update('record_id', {
  title: 'Updated Title',
  content: 'Updated content',
});
```

### Update Record with File

```javascript
const formData = new FormData();
formData.append('title', 'Updated Title');
formData.append('image', newFile);

const updated = await pb.collection('posts').update('record_id', formData);
```

### Partial Update

```javascript
// Only update specific fields
const updated = await pb.collection('posts').update('record_id', {
  views: 100, // Only update views
});
```

---

## Delete Data from Collections

### Delete Single Record

```javascript
await pb.collection('posts').delete('record_id');
```

### Delete Multiple Records

```javascript
// Using batch
await pb.batch([
  {
    method: 'DELETE',
    url: '/api/collections/posts/records/record_id_1',
  },
  {
    method: 'DELETE',
    url: '/api/collections/posts/records/record_id_2',
  },
]);
```

### Delete All Records (Truncate)

```javascript
await pb.collections.truncate('posts');
```

---

## Query Collection Contents

### List Records with Pagination

```javascript
const result = await pb.collection('posts').getList(1, 50);

console.log(result.page);        // 1
console.log(result.perPage);     // 50
console.log(result.totalItems);  // Total count
console.log(result.items);       // Array of records
```

### Filter Records

```javascript
const result = await pb.collection('posts').getList(1, 50, {
  filter: 'published = true && views > 100',
  sort: '-created',
});
```

### Filter Operators

```javascript
// Equality
filter: 'status = "published"'

// Comparison
filter: 'views > 100'
filter: 'created >= "2023-01-01"'

// Text search
filter: 'title ~ "javascript"'

// Multiple conditions
filter: 'status = "published" && views > 100'
filter: 'status = "draft" || status = "pending"'

// Relation filter
filter: 'author.id = "user_id"'
```

### Sort Records

```javascript
// Single field
sort: '-created'  // DESC
sort: 'title'     // ASC

// Multiple fields
sort: '-created,title'  // DESC by created, then ASC by title
```

### Expand Relations

```javascript
const result = await pb.collection('posts').getList(1, 50, {
  expand: 'author,categories',
});

// Access expanded data
result.items.forEach(post => {
  console.log(post.expand.author.name);
  console.log(post.expand.categories);
});
```

### Get Single Record

```javascript
const record = await pb.collection('posts').getOne('record_id', {
  expand: 'author',
});
```

### Get First Matching Record

```javascript
const record = await pb.collection('posts').getFirstListItem(
  'slug = "my-post-slug"',
  {
    expand: 'author',
  }
);
```

### Get All Records

```javascript
const allRecords = await pb.collection('posts').getFullList({
  filter: 'published = true',
  sort: '-created',
});
```

---

## Add and Delete Fields from Collections

### Add Field

```javascript
const collection = await pb.collections.addField('posts', {
  name: 'tags',
  type: 'select',
  options: {
    values: ['tech', 'science', 'art'],
  },
});
```

### Update Field

```javascript
const collection = await pb.collections.updateField('posts', 'tags', {
  options: {
    values: ['tech', 'science', 'art', 'music'],
  },
});
```

### Remove Field

```javascript
const collection = await pb.collections.removeField('posts', 'old_field');
```

### Get Field Information

```javascript
const field = await pb.collections.getField('posts', 'title');
console.log(field.type, field.required, field.options);
```

---

## Query Collection Field Information

### Get All Fields for a Collection

```javascript
const collection = await pb.collections.getOne('posts');
collection.fields.forEach(field => {
  console.log(field.name, field.type, field.required);
});
```

### Get Collection Schema (Simplified)

```javascript
const schema = await pb.collections.getSchema('posts');
console.log(schema.fields); // Array of field info
```

### Get All Collection Schemas

```javascript
const schemas = await pb.collections.getAllSchemas();
schemas.collections.forEach(collection => {
  console.log(collection.name, collection.fields);
});
```

### Query Field Information for Single Collection

```javascript
// Method 1: Get full collection
const collection = await pb.collections.getOne('posts');
const titleField = collection.fields.find(f => f.name === 'title');

// Method 2: Get specific field
const field = await pb.collections.getField('posts', 'title');

// Method 3: Get schema
const schema = await pb.collections.getSchema('posts');
const titleFieldInfo = schema.fields.find(f => f.name === 'title');
```

---

## Upload Files

### Upload File with Record Creation

```javascript
const formData = new FormData();
formData.append('title', 'Post Title');
formData.append('image', fileInput.files[0]);

const record = await pb.collection('posts').create(formData);
```

### Upload File with Record Update

```javascript
const formData = new FormData();
formData.append('image', newFile);

const updated = await pb.collection('posts').update('record_id', formData);
```

### Get File URL

```javascript
const record = await pb.collection('posts').getOne('record_id');
const fileUrl = pb.files.getURL(record, record.image);
```

### Get File URL with Options

```javascript
const fileUrl = pb.files.getURL(record, record.image, {
  thumb: '100x100',  // Thumbnail
  download: true,    // Force download
});
```

### Get Private File Token

```javascript
// For accessing private files
const token = await pb.files.getToken();
// Use token in file URL query params
```

---

## Query Logs

### List Logs

```javascript
const logs = await pb.logs.getList(1, 50);
console.log(logs.items); // Array of log entries
```

### Filter Logs

```javascript
const logs = await pb.logs.getList(1, 50, {
  filter: 'level >= 400', // Error level and above
  sort: '-created',
});
```

### Get Single Log

```javascript
const log = await pb.logs.getOne('log_id');
console.log(log.message, log.data);
```

### Get Log Statistics

```javascript
const stats = await pb.logs.getStats({
  filter: 'level >= 400',
});

stats.forEach(stat => {
  console.log(stat.date, stat.total);
});
```

### Log Levels

- `0` - Debug
- `1` - Info
- `2` - Warning
- `3` - Error
- `4` - Fatal

---

## Send Emails

**Note**: Email sending is typically handled server-side via hooks or backend code. The SDK doesn't provide direct email sending methods, but you can trigger email-related operations.

### Trigger Email Verification

```javascript
// Request verification email
await pb.collection('users').requestVerification('user@example.com');
```

### Trigger Password Reset Email

```javascript
// Request password reset email
await pb.collection('users').requestPasswordReset('user@example.com');
```

### Email Change Request

```javascript
// Request email change
await pb.collection('users').requestEmailChange('newemail@example.com');
```

### Server-Side Email Sending

Email sending is configured in the backend settings and triggered automatically by:
- User registration (verification email)
- Password reset requests
- Email change requests
- Custom hooks

To send custom emails, you would typically:
1. Create a backend hook that uses `app.NewMailClient()`
2. Or use the admin API to configure email templates
3. Or trigger email-related record operations that automatically send emails

---

## Complete Example: Full Application Flow

```javascript
import BosBase from 'bosbase';

const pb = new BosBase('http://localhost:8090');

async function setupApplication() {
  // 1. Authenticate
  await pb.collection('users').authWithPassword('admin@example.com', 'password');
  
  // 2. Create collection
  const collection = await pb.collections.create({
    name: 'posts',
    type: 'base',
    fields: [
      { name: 'title', type: 'text', required: true },
      { name: 'content', type: 'editor' },
      { name: 'published', type: 'bool' },
    ],
  });
  
  // 3. Add more fields
  await pb.collections.addField('posts', {
    name: 'views',
    type: 'number',
    min: 0,
  });
  
  // 4. Create records
  const post = await pb.collection('posts').create({
    title: 'Hello World',
    content: 'My first post',
    published: true,
    views: 0,
  });
  
  // 5. Query records
  const posts = await pb.collection('posts').getList(1, 10, {
    filter: 'published = true',
    sort: '-created',
  });
  
  // 6. Update record
  await pb.collection('posts').update(post.id, {
    views: 100,
  });
  
  // 7. Query logs
  const logs = await pb.logs.getList(1, 20, {
    filter: 'level >= 400',
  });
  
  console.log('Application setup complete!');
}

setupApplication().catch(console.error);
```

---

## Quick Reference

### Common Patterns

```javascript
// Check if authenticated
if (pb.authStore.isValid) { /* ... */ }

// Get current user
const user = pb.authStore.record;

// Refresh auth token
await pb.collection('users').authRefresh();

// Error handling
try {
  await pb.collection('posts').create({ title: 'Test' });
} catch (err) {
  if (err.status === 400) {
    console.error('Validation error:', err.data);
  } else if (err.status === 401) {
    console.error('Not authenticated');
  }
}
```

### Field Types Reference

- `text` - Text input
- `number` - Numeric value
- `bool` - Boolean
- `email` - Email address
- `url` - URL
- `date` - Date
- `select` - Single select
- `json` - JSON data
- `file` - File upload
- `relation` - Relation to another collection
- `editor` - Rich text editor

---

## Best Practices

1. **Always handle errors**: Wrap API calls in try-catch
2. **Check authentication**: Verify `pb.authStore.isValid` before operations
3. **Use pagination**: Don't fetch all records at once for large collections
4. **Validate data**: Ensure required fields are provided
5. **Use filters**: Filter data on the server, not client-side
6. **Expand relations wisely**: Only expand what you need
7. **Handle file uploads**: Use FormData for file fields
8. **Refresh tokens**: Use `authRefresh()` to maintain sessions

---

## LangChaingo Recipes

### Quick Completion

```javascript
const result = await pb.langchaingo.completions({
  model: { provider: "openai", model: "gpt-4o-mini" },
  messages: [
    { role: "system", content: "Answer with one concise line." },
    { role: "user", content: "Give me a fun fact about Mars." }
  ],
  temperature: 0.4
});

console.log(result.content);
```

### Retrieval-Augmented Answering

```javascript
const rag = await pb.langchaingo.rag({
  collection: "knowledge-base",
  question: "Why is the sky blue?",
  topK: 3,
  returnSources: true
});

console.log(rag.answer);
console.log(rag.sources);
```

---

This guide provides all essential operations for building applications with the BosBase JavaScript SDK. For more detailed information, refer to the specific API documentation files.
