# Management API Documentation

This document covers the management API capabilities available in the JavaScript SDK, which correspond to the features available in the backend management UI.

> **Note**: All management API operations require superuser authentication (🔐).

## Table of Contents

- [Settings Service](#settings-service)
  - [Application Configuration](#application-configuration)
  - [Mail Configuration](#mail-configuration)
  - [Storage Configuration](#storage-configuration)
  - [Backup Configuration](#backup-configuration)
  - [Log Configuration](#log-configuration)
- [Backup Service](#backup-service)
- [Log Service](#log-service)
- [Cron Service](#cron-service)
- [Health Service](#health-service)
- [Collection Service](#collection-service)

---

## Settings Service

The Settings Service provides comprehensive management of application settings, matching the capabilities available in the backend management UI.

### Application Configuration

Manage application settings including meta information, trusted proxy, rate limits, and batch configuration.

#### Get Application Settings

```js
const settings = await pb.settings.getApplicationSettings();
// Returns: { meta, trustedProxy, rateLimits, batch }
```

**Example:**
```js
const appSettings = await pb.settings.getApplicationSettings();
console.log(appSettings.meta.appName); // Application name
console.log(appSettings.rateLimits.rules); // Rate limit rules
```

#### Update Application Settings

```js
await pb.settings.updateApplicationSettings({
  meta: {
    appName: "My App",
    appURL: "https://example.com",
    hideControls: false
  },
  trustedProxy: {
    headers: ["X-Forwarded-For"],
    useLeftmostIP: true
  },
  rateLimits: {
    enabled: true,
    rules: [
      {
        label: "api/users",
        duration: 3600,
        maxRequests: 100
      }
    ]
  },
  batch: {
    enabled: true,
    maxRequests: 100,
    interval: 200
  }
});
```

#### Individual Settings Updates

**Update Meta Settings:**
```js
await pb.settings.updateMeta({
  appName: "My App",
  appURL: "https://example.com",
  senderName: "My App",
  senderAddress: "noreply@example.com",
  hideControls: false
});
```

**Update Trusted Proxy:**
```js
await pb.settings.updateTrustedProxy({
  headers: ["X-Forwarded-For", "X-Real-IP"],
  useLeftmostIP: true
});
```

**Update Rate Limits:**
```js
await pb.settings.updateRateLimits({
  enabled: true,
  rules: [
    {
      label: "api/users",
      audience: "public",
      duration: 3600,
      maxRequests: 100
    }
  ]
});
```

**Update Batch Configuration:**
```js
await pb.settings.updateBatch({
  enabled: true,
  maxRequests: 100,
  timeout: 30,
  maxBodySize: 10485760
});
```

---

### Mail Configuration

Manage SMTP email settings and sender information.

#### Get Mail Settings

```js
const mailSettings = await pb.settings.getMailSettings();
// Returns: { meta: { senderName, senderAddress }, smtp }
```

**Example:**
```js
const mail = await pb.settings.getMailSettings();
console.log(mail.meta.senderName); // Sender name
console.log(mail.smtp.host); // SMTP host
```

#### Update Mail Settings

Update both sender info and SMTP configuration in one call:

```js
await pb.settings.updateMailSettings({
  senderName: "My App",
  senderAddress: "noreply@example.com",
  smtp: {
    enabled: true,
    host: "smtp.example.com",
    port: 587,
    username: "user@example.com",
    password: "password",
    authMethod: "PLAIN",
    tls: true,
    localName: "localhost"
  }
});
```

#### Update SMTP Only

```js
await pb.settings.updateSMTP({
  enabled: true,
  host: "smtp.example.com",
  port: 587,
  username: "user@example.com",
  password: "password",
  authMethod: "PLAIN",
  tls: true,
  localName: "localhost"
});
```

#### Test Email

Send a test email to verify SMTP configuration:

```js
await pb.settings.testMail(
  "test@example.com",
  "verification", // template: verification, password-reset, email-change, otp, login-alert
  "_superusers" // collection (optional, defaults to _superusers)
);
```

**Email Templates:**
- `verification` - Email verification template
- `password-reset` - Password reset template
- `email-change` - Email change confirmation template
- `otp` - One-time password template
- `login-alert` - Login alert template

---

### Storage Configuration

Manage S3 storage configuration for file storage.

#### Get Storage S3 Configuration

```js
const s3Config = await pb.settings.getStorageS3();
// Returns: { enabled, bucket, region, endpoint, accessKey, secret, forcePathStyle }
```

#### Update Storage S3 Configuration

```js
await pb.settings.updateStorageS3({
  enabled: true,
  bucket: "my-bucket",
  region: "us-east-1",
  endpoint: "https://s3.amazonaws.com",
  accessKey: "ACCESS_KEY",
  secret: "SECRET_KEY",
  forcePathStyle: false
});
```

#### Test Storage S3 Connection

```js
await pb.settings.testStorageS3();
// Returns: true if connection succeeds
```

---

### Backup Configuration

Manage auto-backup scheduling and S3 storage for backups.

#### Get Backup Settings

```js
const backupSettings = await pb.settings.getBackupSettings();
// Returns: { cron, cronMaxKeep, s3 }
```

**Example:**
```js
const backups = await pb.settings.getBackupSettings();
console.log(backups.cron); // Cron expression (e.g., "0 0 * * *")
console.log(backups.cronMaxKeep); // Maximum backups to keep
```

#### Update Backup Settings

```js
await pb.settings.updateBackupSettings({
  cron: "0 0 * * *", // Daily at midnight (empty string to disable)
  cronMaxKeep: 10, // Keep maximum 10 backups
  s3: {
    enabled: true,
    bucket: "backup-bucket",
    region: "us-east-1",
    endpoint: "https://s3.amazonaws.com",
    accessKey: "ACCESS_KEY",
    secret: "SECRET_KEY",
    forcePathStyle: false
  }
});
```

#### Set Auto-Backup Schedule

```js
// Enable daily backups at midnight, keep 10 backups
await pb.settings.setAutoBackupSchedule("0 0 * * *", 10);

// Disable auto-backup
await pb.settings.disableAutoBackup();
```

**Common Cron Expressions:**
- `"0 0 * * *"` - Daily at midnight
- `"0 0 * * 0"` - Weekly on Sunday at midnight
- `"0 0 1 * *"` - Monthly on the 1st at midnight
- `"0 0 * * 1,3"` - Twice weekly (Monday and Wednesday)

#### Test Backups S3 Connection

```js
await pb.settings.testBackupsS3();
// Returns: true if connection succeeds
```

---

### Log Configuration

Manage log retention and logging settings.

#### Get Log Settings

```js
const logSettings = await pb.settings.getLogSettings();
// Returns: { maxDays, minLevel, logIP, logAuthId }
```

#### Update Log Settings

```js
await pb.settings.updateLogSettings({
  maxDays: 30, // Retain logs for 30 days
  minLevel: 0, // Minimum log level (negative=debug/info, 0=warning, positive=error)
  logIP: true, // Log IP addresses
  logAuthId: true // Log authentication IDs
});
```

#### Individual Log Settings

```js
// Set log retention days
await pb.settings.setLogRetentionDays(30);

// Set minimum log level
await pb.settings.setMinLogLevel(0); // -100 to 100

// Enable/disable IP logging
await pb.settings.setLogIPAddresses(true);

// Enable/disable auth ID logging
await pb.settings.setLogAuthIds(true);
```

**Log Levels:**
- Negative values: Debug/Info levels
- `0`: Default/Warning level
- Positive values: Error levels

---

## Backup Service

Manage application backups - create, list, upload, delete, and restore backups.

### List All Backups

```js
const backups = await pb.backups.getFullList();
// Returns: Array<{ key, size, modified }>
```

**Example:**
```js
const backups = await pb.backups.getFullList();
backups.forEach(backup => {
  console.log(`${backup.key}: ${backup.size} bytes, modified: ${backup.modified}`);
});
```

### Create Backup

```js
await pb.backups.create("backup-2024-01-01");
// Creates a new backup with the specified basename
```

### Upload Backup

Upload an existing backup file:

```js
const file = new File([backupData], "backup.zip", { type: "application/zip" });
await pb.backups.upload({ file });
```

Or using FormData:

```js
const formData = new FormData();
formData.append("file", fileBlob);
await pb.backups.upload(formData);
```

### Delete Backup

```js
await pb.backups.delete("backup-2024-01-01");
// Deletes the specified backup file
```

### Restore Backup

```js
await pb.backups.restore("backup-2024-01-01");
// Restores the application from the specified backup
```

**⚠️ Warning**: Restoring a backup will replace all current application data!

### Get Backup Download URL

```js
// First, get a file token
const token = await pb.files.getToken();

// Then build the download URL
const url = pb.backups.getDownloadURL(token, "backup-2024-01-01");
console.log(url); // Full URL to download the backup
```

---

## Log Service

Query and analyze application logs.

### List Logs

```js
const result = await pb.logs.getList(1, 30, {
  filter: 'level >= 0',
  sort: '-created'
});
// Returns: { page, perPage, totalItems, totalPages, items }
```

**Example with filtering:**
```js
// Get error logs from the last 24 hours
const yesterday = new Date();
yesterday.setDate(yesterday.getDate() - 1);

const errorLogs = await pb.logs.getList(1, 50, {
  filter: `level > 0 && created >= "${yesterday.toISOString()}"`,
  sort: '-created'
});

errorLogs.items.forEach(log => {
  console.log(`[${log.level}] ${log.message}`);
});
```

### Get Single Log

```js
const log = await pb.logs.getOne("log-id");
// Returns: LogModel with full log details
```

### Get Log Statistics

```js
const stats = await pb.logs.getStats({
  filter: 'level >= 0' // Optional filter
});
// Returns: Array<{ total, date }> - hourly statistics
```

**Example:**
```js
const stats = await pb.logs.getStats();
stats.forEach(stat => {
  console.log(`${stat.date}: ${stat.total} requests`);
});
```

---

## Cron Service

Manage and execute cron jobs.

### List All Cron Jobs

```js
const cronJobs = await pb.crons.getFullList();
// Returns: Array<{ id, expression }>
```

**Example:**
```js
const cronJobs = await pb.crons.getFullList();
cronJobs.forEach(job => {
  console.log(`Job ${job.id}: ${job.expression}`);
});
```

### Run Cron Job

Manually trigger a cron job:

```js
await pb.crons.run("job-id");
// Executes the specified cron job immediately
```

**Example:**
```js
const cronJobs = await pb.crons.getFullList();
const backupJob = cronJobs.find(job => job.id.includes("backup"));
if (backupJob) {
  await pb.crons.run(backupJob.id);
  console.log("Backup job executed manually");
}
```

---

## Health Service

Check the health status of the API.

### Check Health

```js
const health = await pb.health.check();
// Returns: Health status information
```

**Example:**
```js
try {
  const health = await pb.health.check();
  console.log("API is healthy:", health);
} catch (error) {
  console.error("Health check failed:", error);
}
```

---

## Collection Service

Manage collections (schemas) programmatically.

### List Collections

```js
const collections = await pb.collections.getList(1, 30);
// Returns: Paginated list of collections
```

### Get Collection

```js
const collection = await pb.collections.getOne("collection-id-or-name");
// Returns: Full collection schema
```

### Create Collection

```js
const collection = await pb.collections.create({
  name: "posts",
  type: "base",
  schema: [
    {
      name: "title",
      type: "text",
      required: true
    },
    {
      name: "content",
      type: "editor",
      required: false
    }
  ]
});
```

### Update Collection

```js
await pb.collections.update("collection-id", {
  schema: [
    // Updated schema
  ]
});
```

### Delete Collection

```js
await pb.collections.delete("collection-id");
```

### Truncate Collection

Delete all records in a collection (keeps the schema):

```js
await pb.collections.truncate("collection-id");
```

### Import Collections

```js
const collections = [
  {
    name: "collection1",
    // ... collection schema
  },
  {
    name: "collection2",
    // ... collection schema
  }
];

await pb.collections.import(collections, false); // false = don't delete missing collections
```

---

## Complete Example: Automated Backup Management

```js
import BosBase from 'bosbase';

const pb = new BosBase('http://127.0.0.1:8090');

// Authenticate as superuser
await pb.collection('_superusers').authWithPassword('admin@example.com', 'password');

// Check current backup settings
const backupSettings = await pb.settings.getBackupSettings();
console.log("Current backup schedule:", backupSettings.cron);

// List all existing backups
const backups = await pb.backups.getFullList();
console.log(`Found ${backups.length} backups`);

// Create a new backup
await pb.backups.create(`manual-backup-${new Date().toISOString().split('T')[0]}`);
console.log("Backup created successfully");

// Get updated backup list
const updatedBackups = await pb.backups.getFullList();
console.log(`Now have ${updatedBackups.length} backups`);

// Configure auto-backup (daily at 2 AM, keep 7 backups)
await pb.settings.setAutoBackupSchedule("0 2 * * *", 7);
console.log("Auto-backup configured");

// Test backup S3 connection if configured
try {
  await pb.settings.testBackupsS3();
  console.log("S3 backup storage is working");
} catch (error) {
  console.warn("S3 backup storage test failed:", error);
}
```

---

## Complete Example: Log Monitoring

```js
import BosBase from 'bosbase';

const pb = new BosBase('http://127.0.0.1:8090');

// Authenticate as superuser
await pb.collection('_superusers').authWithPassword('admin@example.com', 'password');

// Get log settings
const logSettings = await pb.settings.getLogSettings();
console.log("Log retention:", logSettings.maxDays, "days");
console.log("Minimum log level:", logSettings.minLevel);

// Get recent error logs
const errorLogs = await pb.logs.getList(1, 20, {
  filter: 'level > 0',
  sort: '-created'
});

console.log(`Found ${errorLogs.totalItems} error logs`);
errorLogs.items.forEach(log => {
  console.log(`[${log.level}] ${log.message} - ${log.created}`);
});

// Get hourly statistics for the last 24 hours
const stats = await pb.logs.getStats({
  filter: 'created >= "' + new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() + '"'
});

console.log("Hourly request statistics:");
stats.forEach(stat => {
  console.log(`${stat.date}: ${stat.total} requests`);
});

// Update log settings to retain logs for 14 days
await pb.settings.setLogRetentionDays(14);
console.log("Log retention updated to 14 days");
```

---

## Complete Example: Application Configuration Management

```js
import BosBase from 'bosbase';

const pb = new BosBase('http://127.0.0.1:8090');

// Authenticate as superuser
await pb.collection('_superusers').authWithPassword('admin@example.com', 'password');

// Get current application settings
const appSettings = await pb.settings.getApplicationSettings();
console.log("App Name:", appSettings.meta?.appName);
console.log("App URL:", appSettings.meta?.appURL);

// Update application configuration
await pb.settings.updateApplicationSettings({
  meta: {
    appName: "My Production App",
    appURL: "https://api.example.com",
    hideControls: false
  },
  rateLimits: {
    enabled: true,
    rules: [
      {
        label: "api/users",
        duration: 3600,
        maxRequests: 100
      },
      {
        label: "api/posts",
        duration: 3600,
        maxRequests: 200
      }
    ]
  },
  batch: {
    enabled: true,
    maxRequests: 100,
    interval: 200
  }
});

console.log("Application settings updated");

// Configure trusted proxy
await pb.settings.updateTrustedProxy({
  headers: ["X-Forwarded-For", "X-Real-IP"],
  useLeftmostIP: true
});

console.log("Trusted proxy configured");
```

---

## Error Handling

All management API methods can throw `ClientResponseError`. Always handle errors appropriately:

```js
try {
  await pb.backups.create("my-backup");
  console.log("Backup created successfully");
} catch (error) {
  if (error.status === 401) {
    console.error("Authentication required");
  } else if (error.status === 403) {
    console.error("Superuser access required");
  } else {
    console.error("Error:", error.message);
  }
}
```

---

## Notes

1. **Authentication**: All management API operations require superuser authentication. Use `pb.collection('_superusers').authWithPassword()` to authenticate.

2. **Rate Limiting**: Be mindful of rate limits when making multiple management API calls.

3. **Backup Safety**: Always test backup restoration in a safe environment before using in production.

4. **Log Retention**: Setting appropriate log retention helps manage storage usage.

5. **Cron Jobs**: Manual cron execution is useful for testing but should be used carefully in production.

For more information on specific services, see:
- [Settings API](./SETTINGS_API.md) - Detailed settings documentation
- [Backups API](./BACKUPS_API.md) - Detailed backup operations
- [Logs API](./LOGS_API.md) - Detailed log operations
- [Collections API](./COLLECTION_API.md) - Collection management

