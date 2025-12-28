# Collection API - Python SDK

The Collection API exposes the same admin endpoints that power the dashboard. Use it for migrations, seed scripts, or CI pipelines.

## Listing Collections

```python
collections = pb.collections.get_list(page=1, per_page=50)
for item in collections["items"]:
    print(item["name"], item["type"])
```

`get_full_list()` fetches all collections in batches, which is useful for snapshots.

## Creating Collections

### Manual Definition

```python
collection = pb.collections.create(
    body={
        "name": "projects",
        "type": "base",
        "schema": [
            {"name": "title", "type": "text", "required": True},
            {"name": "owner", "type": "relation", "collectionId": "users"},
        ],
        "options": {},
    },
)
```

### Using Scaffolds

```python
pb.collections.create_base("articles")
pb.collections.create_auth("customers")
pb.collections.create_view("recent_posts", view_query="SELECT * FROM posts")
```

## Updating Collections

```python
pb.collections.update(
    "articles",
    body={
        "listRule": 'status = "published" || @request.auth.role = "editor"',
        "schema": [
            {"name": "status", "type": "select", "options": {"values": ["draft", "published"]}},
        ],
    },
)
```

Partial updates merge with the existing schema. For field-level helpers see `COLLECTIONS.md`.

## Managing Indexes

Indexes are stored as SQL strings on the collection definition. The Python SDK includes helpers so you can add, remove, or inspect indexes without editing raw SQL manually.

```python
# Unique slug index with a custom name
pb.collections.add_index(
    "posts",
    columns=["slug"],
    unique=True,
    index_name="idx_posts_slug_unique",
)

# Composite non-unique index (name auto-generated)
pb.collections.add_index("posts", columns=["status", "published"])

# Remove any index that references the slug column
pb.collections.remove_index("posts", columns=["slug"])

# Inspect current indexes
for idx in pb.collections.get_indexes("posts"):
    print(idx)
```

- `columns` must reference existing fields (system fields like `id` are always allowed).
- `unique=True` emits `CREATE UNIQUE INDEX` while the default emits `CREATE INDEX`.
- Omit `index_name` to let the SDK generate `idx_{collection}_{column1}_{column2}`.
- `remove_index()` deletes indexes that contain all provided columns, so it works for both single and multi-column indexes.

## Delete & Truncate

```python
pb.collections.delete_collection("unused")
pb.collections.truncate("logs")  # delete records, keep schema
```

## Register Existing SQL Tables

Map existing SQL tables to BosBase collections (superuser-only):

```python
pb.collections.register_sql_tables(["projects", "accounts"])

pb.collections.import_sql_tables(
    [
        {"name": "reports"},
        {
            "name": "legacy_orders",
            "sql": "CREATE TABLE IF NOT EXISTS legacy_orders (id TEXT PRIMARY KEY);",
        },
    ]
)
```

`register_sql_tables()` registers existing tables.  
`import_sql_tables()` optionally runs SQL before registering and returns `{"created": [...], "skipped": [...]}`.

## Import / Export

```python
snapshot = pb.collections.get_full_list()

pb.collections.import_collections(
    collections=snapshot,
    delete_missing=True,
)
```

- `delete_missing=True` removes collections not present in the import payload.
- Use this inside migrations to sync environments.
- `export_collections()` strips timestamps and OAuth providers to match the admin UI export.
- `normalize_for_import()` deduplicates collections/fields and removes timestamps before calling `import_collections()`.

## Settings and Metadata

`get_scaffolds()` returns the default JSON definitions for base/auth/view collections. You can inspect them to understand required fields.

`get_schema(name)` returns the light-weight schema info for a single collection.

## Tips

1. Keep versioned snapshots of the schema for diffing between environments.
2. Use `truncate()` inside tests to reset state quickly.
3. The API requires superuser credentials. Authenticate with `_superusers` before invoking collection management calls.
4. When migrating production data, use `import_collections(..., delete_missing=False)` to avoid unintentional drops.

## Complete Examples

### Example 1: Setup Blog Collections

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")
pb.collection("_superusers").auth_with_password("admin@example.com", "password")

def setup_blog():
    """Create blog collections with posts and categories."""
    # Create posts collection
    posts = pb.collections.create(
        body={
            "name": "posts",
            "type": "base",
            "fields": [
                {
                    "name": "title",
                    "type": "text",
                    "required": True,
                    "min": 10,
                    "max": 255
                },
                {
                    "name": "slug",
                    "type": "text",
                    "required": True,
                    "options": {
                        "pattern": "^[a-z0-9-]+$"
                    }
                },
                {
                    "name": "content",
                    "type": "editor",
                    "required": True
                },
                {
                    "name": "featured_image",
                    "type": "file",
                    "maxSelect": 1,
                    "maxSize": 5242880,  # 5MB
                    "mimeTypes": ["image/jpeg", "image/png"]
                },
                {
                    "name": "published",
                    "type": "bool",
                    "required": False
                },
                {
                    "name": "author",
                    "type": "relation",
                    "collectionId": "_pbc_users_auth_",
                    "maxSelect": 1
                },
                {
                    "name": "categories",
                    "type": "relation",
                    "collectionId": "categories",
                    "maxSelect": 5
                }
            ],
            "listRule": '@request.auth.id != "" || published = true',
            "viewRule": '@request.auth.id != "" || published = true',
            "createRule": '@request.auth.id != ""',
            "updateRule": "author = @request.auth.id",
            "deleteRule": "author = @request.auth.id"
        }
    )
    
    # Create categories collection
    categories = pb.collections.create(
        body={
            "name": "categories",
            "type": "base",
            "fields": [
                {
                    "name": "name",
                    "type": "text",
                    "required": True,
                    "unique": True
                },
                {
                    "name": "slug",
                    "type": "text",
                    "required": True
                },
                {
                    "name": "description",
                    "type": "text",
                    "required": False
                }
            ],
            "listRule": '@request.auth.id != ""',
            "viewRule": '@request.auth.id != ""'
        }
    )
    
    # Access collection IDs immediately after creation
    print(f"Posts collection ID: {posts['id']}")
    print(f"Categories collection ID: {categories['id']}")
    
    # Update posts collection to use the categories collection ID
    posts_updated = pb.collections.get_one(posts["id"])
    category_field = next((f for f in posts_updated["fields"] if f["name"] == "categories"), None)
    if category_field:
        category_field["collectionId"] = categories["id"]
        pb.collections.update(posts["id"], body=posts_updated)
    
    print("Blog setup complete!")
    return {
        "posts_id": posts["id"],
        "categories_id": categories["id"]
    }

# Usage
result = setup_blog()
```

### Example 2: Migrate Collections

```python
from bosbase import BosBase
import json

pb = BosBase("http://127.0.0.1:8090")
pb.collection("_superusers").auth_with_password("admin@example.com", "password")

def migrate_collections():
    """Migrate collections by adding new fields and updating rules."""
    # Export existing collections
    existing_collections = pb.collections.get_full_list()
    
    # Modify collections
    modified_collections = []
    for collection in existing_collections:
        if collection["name"] == "posts":
            # Add new field
            collection["fields"].append({
                "name": "views",
                "type": "number",
                "required": False,
                "options": {
                    "min": 0
                }
            })
            
            # Update rules
            collection["updateRule"] = '@request.auth.id != "" || published = true'
        
        modified_collections.append(collection)
    
    # Import modified collections
    pb.collections.import_collections(
        collections=modified_collections,
        delete_missing=False
    )
    
    print("Collections migrated successfully")

# Usage
migrate_collections()
```

### Example 3: Clone Collection

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")
pb.collection("_superusers").auth_with_password("admin@example.com", "password")

def clone_collection(source_name: str, target_name: str):
    """Clone a collection with a new name."""
    # Get source collection
    source = pb.collections.get_one(source_name)
    
    # Create new collection based on source
    clone = dict(source)
    clone.pop("id", None)  # Let it auto-generate
    clone["name"] = target_name
    clone.pop("created", None)
    clone.pop("updated", None)
    clone["system"] = False
    
    # Remove system fields
    clone["fields"] = [f for f in clone.get("fields", []) if not f.get("system", False)]
    
    # Create cloned collection
    return pb.collections.create(body=clone)

# Usage
cloned = clone_collection("posts", "posts_backup")
print(f"Cloned collection ID: {cloned['id']}")
```

### Example 4: Backup and Restore

```python
from bosbase import BosBase
import json

pb = BosBase("http://127.0.0.1:8090")
pb.collection("_superusers").auth_with_password("admin@example.com", "password")

def backup_collections(filename: str = "collections_backup.json"):
    """Backup all collections to a JSON file."""
    # Get all collections
    collections = pb.collections.get_full_list()
    
    # Save to file
    with open(filename, "w") as f:
        json.dump(collections, f, indent=2)
    
    print(f"Backed up {len(collections)} collections to {filename}")

def restore_collections(filename: str = "collections_backup.json"):
    """Restore collections from a JSON file."""
    # Load from file
    with open(filename, "r") as f:
        collections = json.load(f)
    
    # Restore
    pb.collections.import_collections(
        collections=collections,
        delete_missing=False
    )
    
    print(f"Restored {len(collections)} collections from {filename}")

# Usage
backup_collections()
# restore_collections()
```

### Example 5: Validate Collection Configuration

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")
pb.collection("_superusers").auth_with_password("admin@example.com", "password")

def validate_collection(name: str):
    """Validate collection configuration."""
    try:
        collection = pb.collections.get_one(name)
        
        warnings = []
        
        # Check required fields
        has_required_fields = any(f.get("required", False) for f in collection.get("fields", []))
        if not has_required_fields:
            warnings.append("Collection has no required fields")
        
        # Check API rules
        if collection.get("type") == "base" and not collection.get("listRule"):
            warnings.append("Base collection has no listRule (superuser only)")
        
        # Check indexes
        if len(collection.get("indexes", [])) == 0:
            warnings.append("Collection has no indexes")
        
        if warnings:
            print(f"Validation warnings for {name}:")
            for warning in warnings:
                print(f"  - {warning}")
        else:
            print(f"Collection {name} is valid")
        
        return len(warnings) == 0
        
    except Exception as error:
        print(f"Validation failed: {error}")
        return False

# Usage
is_valid = validate_collection("posts")
```

## Error Handling

```python
from bosbase import BosBase
from bosbase.exceptions import ClientResponseError

pb = BosBase("http://127.0.0.1:8090")
pb.collection("_superusers").auth_with_password("admin@example.com", "password")

try:
    pb.collections.create(
        body={
            "name": "test",
            "type": "base",
            "fields": []
        }
    )
except ClientResponseError as error:
    if error.status == 401:
        print("Not authenticated")
    elif error.status == 403:
        print("Not a superuser")
    elif error.status == 400:
        print(f"Validation error: {error.response}")
    else:
        print(f"Unexpected error: {error}")
except Exception as error:
    print(f"Unexpected error: {error}")
```

## Best Practices

1. **Always Authenticate**: Ensure you're authenticated as a superuser before making requests
2. **Backup Before Import**: Always backup existing collections before using `import_collections` with `delete_missing=True`
3. **Validate Schema**: Validate collection schemas before creating/updating
4. **Use Scaffolds**: Use scaffolds as starting points for consistency
5. **Test Rules**: Test API rules thoroughly before deploying to production
6. **Index Important Fields**: Add indexes for frequently queried fields
7. **Document Schemas**: Keep documentation of your collection schemas
8. **Version Control**: Store collection schemas in version control for migration tracking
