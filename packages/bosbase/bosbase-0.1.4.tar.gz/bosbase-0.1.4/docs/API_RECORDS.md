# Records API - Python SDK

The Records API provides CRUD access to collection data. Every record operation hangs off a `RecordService` returned by `pb.collection("<name>")`.

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")
pb.collection("_superusers").auth_with_password("admin@example.com", "password")

posts = pb.collection("posts")
```

## Listing Records

```python
result = posts.get_list(page=1, per_page=20, query={"sort": "-created"})
for record in result["items"]:
    print(record["title"])
```

- `get_full_list()` fetches everything in batches (client-side pagination).
- `get_first_list_item(filter=...)` returns the first match or raises a 404 error.

## Filtering and Sorting

```python
expr = pb.filter(
    '(status = {:status} && published >= {:start}) || tags @> {:highlight}',
    {"status": "published", "start": "2024-01-01 00:00:00", "highlight": "launch"},
)

records = posts.get_list(
    page=1,
    per_page=5,
    query={"filter": expr, "sort": "-published", "expand": "author"},
)
```

## Retrieving Records

```python
record = posts.get_one("RECORD_ID", query={"expand": "author,comments"})
count = posts.get_count(filter="status = 'published'")
```

## Creating Records

```python
article = posts.create(
    body={
        "title": "Hello from Python",
        "status": "draft",
    },
)
```

### File Uploads

Provide a dict of file tuples (`(filename, fileobj, content_type)`):

```python
with open("cover.png", "rb") as fh:
    posts.create(
        body={"title": "With cover"},
        files={"cover": ("cover.png", fh, "image/png")},
    )
```

## Updating & Deleting

```python
posts.update("RECORD_ID", body={"status": "published"})
posts.delete("RECORD_ID")
```

When you update/delete the authenticated record, the auth store is automatically kept in sync.

## Auth Collections

`RecordService` contains all auth-specific helpers when the collection is auth-enabled:

```python
users = pb.collection("users")

auth_data = users.auth_with_password("demo@example.com", "secret")

users.request_password_reset("demo@example.com")
users.confirm_password_reset(token, "newPass", "newPass")

otp = users.request_otp("demo@example.com")
auth_data = users.auth_with_otp(otp["otpId"], "123456")

auth_data = users.auth_refresh()
users.request_verification("demo@example.com")
users.confirm_verification(token)

impersonated = users.impersonate("TARGET_ID", duration=300)
print(impersonated.auth_store.token)
```

OAuth2 helper:

```python
def open_browser(url: str) -> None:
    print("Open in browser:", url)

auth_data = users.auth_with_oauth2(
    "google",
    url_callback=open_browser,
    scopes=["profile", "email"],
)
```

## Batch Operations

Use `pb.create_batch()` for transactional multi-collection writes:

```python
batch = pb.create_batch()

batch.collection("posts").create(body={"title": "from batch"})
batch.collection("posts").update("abc123", body={"title": "edited"})
batch.collection("comments").delete("comment123")

results = batch.send()
for res in results:
    print(res["status"])
```

## Tips

- Always request only needed relations via `expand` to minimize payloads.
- Reuse filters and sort orders between SDK and dashboard for consistency.
- Combine `get_list(skip_total=True)` for cheap infinite scrolling.
- Use `query={"fields": "id,title"}` when building search indexes to limit data transfer.

## Complete Examples

### Example 1: Blog Post Search with Filters

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")
posts = pb.collection("posts")

def search_posts(query: str, category_id: str = None, min_views: int = None):
    """Search posts with optional filters."""
    filter_parts = [f'title ~ "{query}" || content ~ "{query}"']
    
    if category_id:
        filter_parts.append(f'categories.id ?= "{category_id}"')
    
    if min_views:
        filter_parts.append(f"views >= {min_views}")
    
    filter_expr = " && ".join(filter_parts)
    
    result = posts.get_list(
        page=1,
        per_page=20,
        query={
            "filter": filter_expr,
            "sort": "-created",
            "expand": "author,categories"
        }
    )
    
    return result["items"]

# Usage
results = search_posts("python", category_id="tech", min_views=100)
for post in results:
    print(post["title"])
```

### Example 2: User Dashboard with Related Content

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def get_user_dashboard(user_id: str):
    """Get user dashboard with posts and comments."""
    # Get user's posts
    posts_result = pb.collection("posts").get_list(
        page=1,
        per_page=10,
        query={
            "filter": f'author = "{user_id}"',
            "sort": "-created",
            "expand": "categories"
        }
    )
    
    # Get user's comments
    comments_result = pb.collection("comments").get_list(
        page=1,
        per_page=10,
        query={
            "filter": f'user = "{user_id}"',
            "sort": "-created",
            "expand": "post"
        }
    )
    
    return {
        "posts": posts_result["items"],
        "comments": comments_result["items"]
    }

# Usage
dashboard = get_user_dashboard("user_id_123")
print(f"User has {len(dashboard['posts'])} posts and {len(dashboard['comments'])} comments")
```

### Example 3: Advanced Filtering

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

# Complex filter example
result = pb.collection("posts").get_list(
    page=1,
    per_page=50,
    query={
        "filter": """
            (status = "published" || featured = true) &&
            created >= "2023-01-01" &&
            (tags.id ?= "important" || categories.id = "news") &&
            views > 100 &&
            author.email != ""
        """,
        "sort": "-views,created",
        "expand": "author.profile,tags,categories",
        "fields": "*,content:excerpt(300),author.name,author.email"
    }
)

for post in result["items"]:
    print(f"{post['title']} - {post.get('views', 0)} views")
```

### Example 4: Batch Create Posts

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def create_multiple_posts(posts_data: list):
    """Create multiple posts in a batch operation."""
    batch = pb.create_batch()
    
    for post_data in posts_data:
        batch.collection("posts").create(body=post_data)
    
    results = batch.send()
    
    # Check for failures
    failures = [
        {"index": idx, "result": res}
        for idx, res in enumerate(results)
        if res.get("status", 0) >= 400
    ]
    
    if failures:
        print(f"Some posts failed to create: {failures}")
    
    return [r.get("body") for r in results]

# Usage
posts_to_create = [
    {"title": "Post 1", "content": "Content 1", "status": "draft"},
    {"title": "Post 2", "content": "Content 2", "status": "draft"},
    {"title": "Post 3", "content": "Content 3", "status": "published"},
]

created_posts = create_multiple_posts(posts_to_create)
print(f"Created {len(created_posts)} posts")
```

### Example 5: Pagination Helper

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def get_all_records_paginated(collection_name: str, options: dict = None):
    """Fetch all records using pagination."""
    if options is None:
        options = {}
    
    all_records = []
    page = 1
    has_more = True
    
    while has_more:
        query = dict(options)
        query["skip_total"] = True  # Skip count for performance
        
        result = pb.collection(collection_name).get_list(
            page=page,
            per_page=500,
            query=query
        )
        
        all_records.extend(result["items"])
        
        has_more = len(result["items"]) == 500
        page += 1
    
    return all_records

# Usage
all_posts = get_all_records_paginated(
    "posts",
    options={"filter": 'status = "published"', "sort": "-created"}
)
print(f"Found {len(all_posts)} published posts")
```

### Example 6: OAuth2 Authentication Flow

```python
from bosbase import BosBase
from bosbase.exceptions import ClientResponseError

pb = BosBase("https://your-domain.com")

# In a real application, you would use a session store
# For this example, we'll use a simple dictionary
oauth2_state = {}

def handle_oauth2_login(provider_name: str):
    """Initiate OAuth2 login flow."""
    # Get OAuth2 methods
    methods = pb.collection("users").list_auth_methods()
    providers = methods.get("oauth2", {}).get("providers", [])
    provider = next((p for p in providers if p["name"] == provider_name), None)
    
    if not provider:
        raise ValueError(f"Provider {provider_name} not available")
    
    # Store code verifier for later (in a real app, use session storage)
    oauth2_state["code_verifier"] = provider["codeVerifier"]
    oauth2_state["provider"] = provider_name
    
    # In a real application, redirect to provider.authURL
    print(f"Redirect to: {provider['authURL']}")
    return provider["authURL"]

def handle_oauth2_callback(code: str, redirect_url: str):
    """Handle OAuth2 callback after redirect."""
    provider = oauth2_state.get("provider")
    code_verifier = oauth2_state.get("code_verifier")
    
    if not provider or not code_verifier:
        raise ValueError("OAuth2 state not found")
    
    try:
        auth_data = pb.collection("users").auth_with_oauth2_code(
            provider,
            code,
            code_verifier,
            redirect_url,
            body={
                # Optional: data for new account creation
                "name": "User"
            }
        )
        
        # Success! User is now authenticated
        print("OAuth2 authentication successful")
        return auth_data
    except ClientResponseError as error:
        print(f"OAuth2 authentication failed: {error}")
        raise

# Usage example (in a web framework)
# @app.route('/oauth2/login/<provider>')
# def oauth2_login(provider):
#     auth_url = handle_oauth2_login(provider)
#     return redirect(auth_url)
#
# @app.route('/oauth2/callback')
# def oauth2_callback():
#     code = request.args.get('code')
#     redirect_url = request.url_root + 'oauth2/callback'
#     auth_data = handle_oauth2_callback(code, redirect_url)
#     return redirect('/dashboard')
```

## Error Handling

```python
from bosbase import BosBase
from bosbase.exceptions import ClientResponseError

pb = BosBase("http://127.0.0.1:8090")

try:
    record = pb.collection("posts").create(
        body={"title": "My Post"}
    )
except ClientResponseError as error:
    if error.status == 400:
        # Validation error
        print(f"Validation errors: {error.response}")
    elif error.status == 403:
        # Permission denied
        print("Access denied")
    elif error.status == 404:
        # Not found
        print("Collection or record not found")
    else:
        print(f"Unexpected error: {error}")
```

## Best Practices

1. **Use Pagination**: Always use pagination for large datasets
2. **Skip Total When Possible**: Use `skip_total=True` in query for better performance when you don't need counts
3. **Batch Operations**: Use batch for multiple operations to reduce round trips
4. **Field Selection**: Only request fields you need to reduce payload size
5. **Expand Wisely**: Only expand relations you actually use
6. **Filter Before Sort**: Apply filters before sorting for better performance
7. **Cache Auth Tokens**: Auth tokens are automatically stored in `auth_store`, no need to manually cache
8. **Handle Errors**: Always handle authentication and permission errors gracefully
