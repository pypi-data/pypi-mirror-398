# Relations - Python SDK

Relations connect records across collections. The SDK lets you expand relations inline, filter across relations, and react to back-relations in realtime.

## Expanding Relations

```python
posts = pb.collection("posts").get_list(
    page=1,
    per_page=20,
    query={"expand": "author,comments.author"},
)

for record in posts["items"]:
    author = record["expand"]["author"]
    comments = record["expand"].get("comments") or []
```

- Use comma-separated paths for nested expands.
- Expand paths follow relation field names (`comments.author`).

## Filtering by Relations

```python
expr = pb.filter("author = {:author} && comments.id ?= {:comment}", {
    "author": pb.auth_store.record["id"],
    "comment": "comment123",
})

records = pb.collection("posts").get_list(query={"filter": expr})
```

`?=` checks whether the relation contains the provided value.

## Managing Relation Fields

### Setting Single Relations

```python
pb.collection("posts").update(
    "POST_ID",
    body={"author": "USER_ID"},
)
```

### Managing Many-to-Many Relations

Provide lists of record IDs:

```python
pb.collection("posts").update(
    "POST_ID",
    body={"tags": ["tag1", "tag2"]},
)
```

When using the `$append`/`$remove` modifiers:

```python
pb.collection("posts").update(
    "POST_ID",
    body={
        "tags+": ["tag3"],
        "tags-": ["tag1"],
    },
)
```

## Back-Relations

The backend automatically exposes back-relations so you can expand them without storing redundant fields. For example, if comments have a `post` relation, you can expand `comments_via_post` from the `posts` collection (depending on your schema naming).

Use the Admin UI “API preview” to confirm the generated back-relation name and then use it in `expand`.

## Realtime and Relations

Subscriptions use `<collection>/<topic>` syntax, so you can monitor relation changes:

```python
def on_comment(event):
    print(event["action"], event["record"]["content"])

pb.collection("comments").subscribe("*", on_comment, query={"expand": "post"})
```

When a relation is expanded in the subscription and the related record changes, the backend automatically emits an update event with the refreshed relation data.

## Tips

1. Use `fields` to limit relation payloads (`"fields": "id,title,author.name"`).
2. When building filters that involve large relation lists, prefer `@collection` lookups inside rules to keep the filter lean.
3. Reuse relation names consistently (e.g. `user`, not `userId`) for clean expand syntax.
4. Enable cascading deletes only when the domain model requires strong ownership; otherwise handle clean-up with triggers or cron jobs.

## Complete Examples

### Example 1: Blog Post with Author and Tags

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

# Create a blog post with relations
post = pb.collection("posts").create(
    body={
        "title": "Getting Started with BosBase",
        "content": "Lorem ipsum...",
        "author": "AUTHOR_ID",  # Single relation
        "tags": ["tag1", "tag2", "tag3"]  # Multiple relation
    }
)

# Retrieve with all relations expanded
full_post = pb.collection("posts").get_one(
    post["id"],
    query={"expand": "author,tags"}
)

print(full_post["title"])
print(f"Author: {full_post['expand']['author']['name']}")
print("Tags:")
for tag in full_post["expand"]["tags"]:
    print(f"  - {tag['name']}")
```

### Example 2: Comment System with Nested Relations

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

# Create a comment on a post
comment = pb.collection("comments").create(
    body={
        "message": "Great article!",
        "post": "POST_ID",
        "user": "USER_ID"
    }
)

# Get post with all comments and their authors
post = pb.collection("posts").get_one(
    "POST_ID",
    query={"expand": "author,comments_via_post.user"}
)

print(f"Post: {post['title']}")
print(f"Author: {post['expand']['author']['name']}")
comments = post["expand"].get("comments_via_post", [])
print(f"Comments ({len(comments)}):")
for comment in comments:
    print(f"  {comment['expand']['user']['name']}: {comment['message']}")
```

### Example 3: Dynamic Tag Management

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

class PostManager:
    def add_tag(self, post_id: str, tag_id: str):
        """Add a tag to a post."""
        pb.collection("posts").update(
            post_id,
            body={"tags+": [tag_id]}
        )
    
    def remove_tag(self, post_id: str, tag_id: str):
        """Remove a tag from a post."""
        pb.collection("posts").update(
            post_id,
            body={"tags-": [tag_id]}
        )
    
    def set_priority_tags(self, post_id: str, tag_ids: list):
        """Set priority tags, keeping existing tags."""
        post = pb.collection("posts").get_one(post_id)
        existing_tags = post.get("tags", [])
        
        # Set priority tags first, then append others
        pb.collection("posts").update(
            post_id,
            body={
                "tags": tag_ids + [t for t in existing_tags if t not in tag_ids]
            }
        )
    
    def get_post_with_tags(self, post_id: str):
        """Get post with tags expanded."""
        return pb.collection("posts").get_one(
            post_id,
            query={"expand": "tags"}
        )

# Usage
manager = PostManager()
manager.add_tag("POST_ID", "NEW_TAG_ID")
post = manager.get_post_with_tags("POST_ID")
print(f"Post has {len(post['expand']['tags'])} tags")
```

### Example 4: Filtering Posts by Tag

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

# Get all posts with a specific tag
posts = pb.collection("posts").get_list(
    page=1,
    per_page=50,
    query={
        "filter": 'tags.id ?= "TAG_ID"',
        "expand": "author,tags",
        "sort": "-created"
    }
)

for post in posts["items"]:
    author = post["expand"].get("author", {})
    print(f"{post['title']} by {author.get('name', 'Unknown')}")
```

### Example 5: User Dashboard with Related Content

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def get_user_dashboard(user_id: str):
    """Get user dashboard with all related content."""
    # Get user with all related content
    user = pb.collection("users").get_one(
        user_id,
        query={"expand": "posts_via_author,comments_via_user.post"}
    )
    
    print(f"Dashboard for {user.get('name', 'User')}")
    
    posts = user["expand"].get("posts_via_author", [])
    print(f"\nPosts ({len(posts)}):")
    for post in posts:
        print(f"  - {post['title']}")
    
    comments = user["expand"].get("comments_via_user", [])
    print(f"\nRecent Comments:")
    for comment in comments[:5]:
        post_title = comment["expand"].get("post", {}).get("title", "Unknown")
        print(f"  On \"{post_title}\": {comment['message']}")

# Usage
get_user_dashboard("USER_ID")
```

### Example 6: Complex Nested Expand

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

# Get a post with author, tags, comments, comment authors, and comment reactions
post = pb.collection("posts").get_one(
    "POST_ID",
    query={
        "expand": "author,tags,comments_via_post.user,comments_via_post.reactions_via_comment"
    }
)

# Access deeply nested data
comments = post["expand"].get("comments_via_post", [])
for comment in comments:
    user = comment["expand"].get("user", {})
    print(f"{user.get('name', 'Unknown')}: {comment['message']}")
    
    reactions = comment["expand"].get("reactions_via_comment")
    if reactions:
        print(f"  Reactions: {len(reactions)}")
```

## Best Practices

1. **Use Expand Wisely**: Only expand relations you actually need to reduce response size and improve performance.

2. **Handle Missing Expands**: Always check if expand data exists before accessing:

   ```python
   if record.get("expand", {}).get("user"):
       print(record["expand"]["user"]["name"])
   ```

3. **Pagination for Large Back-Relations**: If you expect more than 1000 related records, fetch them separately with pagination.

4. **Cache Expansion**: Consider caching expanded data on the client side to reduce API calls.

5. **Error Handling**: Handle cases where related records might not be accessible due to API rules.

6. **Nested Limit**: Remember that nested expands are limited to 6 levels deep.

## Performance Considerations

- **Expand Cost**: Expanding relations doesn't require additional round trips, but increases response payload size
- **Back-Relation Limit**: The 1000 record limit for back-relations prevents extremely large responses
- **Permission Checks**: Each expanded relation is checked against the collection's `viewRule`
- **Nested Depth**: Limit nested expands to avoid performance issues (max 6 levels supported)
