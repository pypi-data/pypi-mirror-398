# Realtime API - Python SDK

BosBase exposes realtime change feeds over Server-Sent Events (SSE). The Python SDK manages the SSE connection in a background thread and automatically resubscribes after reconnects.

## Basic Usage

```python
def on_post_update(event):
    print(event["action"], event["record"]["title"])

unsubscribe = pb.collection("posts").subscribe("*", on_post_update)

# Later
unsubscribe()
```

- Topic `"*"` listens to all records.
- Use a record ID to watch a single record: `subscribe("RECORD_ID", callback)`.

## Subscription Options

Each subscription can include query params or headers (used by API rules):

```python
unsubscribe = pb.collection("posts").subscribe(
    "*",
    on_post_update,
    query={
        "filter": pb.filter("status = {:status}", {"status": "published"}),
        "expand": "author",
    },
    headers={"X-App-Instance": "cli"},
)
```

## PB_CONNECT Event

The SDK automatically listens for the `PB_CONNECT` event and stores the server-assigned `clientId`. If you want to react to reconnects, set `pb.realtime.on_disconnect`.

```python
def handle_disconnect(active_topics):
    if active_topics:
        print("Connection lost, waiting for auto-reconnect…")
    else:
        print("No active subscriptions; connection closed.")

pb.realtime.on_disconnect = handle_disconnect
```

## Custom Realtime Topics

 `pb.realtime` can subscribe to raw topics for custom realtime events emitted by server hooks.

```python
def on_job(event):
    print(event)

pb.realtime.subscribe("jobs/finished", on_job)
```

## Unsubscribing

- `unsubscribe(topic)` removes every listener for that topic.
- `unsubscribe_by_prefix("posts/")` removes all collection listeners.
- The returned callable from `subscribe()` removes the specific listener only.

```python
pb.collection("posts").unsubscribe("RECORD_ID")
pb.realtime.unsubscribe()  # remove every topic
```

## Threading Notes

- Callbacks execute on the SSE thread. If you mutate shared state, protect it with locks.
- The SSE loop automatically restarts unless all subscriptions are removed.

## Tips

1. Always expand required relations in the subscription query; event payloads do not re-fetch data.
2. Use `filter` query params to reduce server load and network traffic.
3. Combine realtime events with local caches to keep UI lists in sync.
4. When using OAuth2 auth flows, the SDK internally subscribes to the `@oauth2` topic and cleans it up automatically—no manual action required.

## Complete Examples

### Example 1: Real-time Chat

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def setup_chat_room(room_id: str):
    """Subscribe to messages in a chat room."""
    def on_message(event):
        # Filter for this room only
        if event["record"].get("roomId") == room_id:
            if event["action"] == "create":
                display_message(event["record"])
            elif event["action"] == "delete":
                remove_message(event["record"]["id"])
    
    unsubscribe = pb.collection("messages").subscribe(
        "*",
        on_message,
        query={"filter": f'roomId = "{room_id}"'}
    )
    
    return unsubscribe

def display_message(record):
    """Display a message in the UI."""
    print(f"New message: {record.get('content')}")

def remove_message(message_id: str):
    """Remove a message from the UI."""
    print(f"Message deleted: {message_id}")

# Usage
unsubscribe_chat = setup_chat_room("ROOM_ID")

# Cleanup
# unsubscribe_chat()
```

### Example 2: Real-time Dashboard

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def setup_dashboard():
    """Subscribe to multiple collections for dashboard updates."""
    # Posts updates
    def on_post(event):
        if event["action"] == "create":
            add_post_to_feed(event["record"])
        elif event["action"] == "update":
            update_post_in_feed(event["record"])
    
    pb.collection("posts").subscribe(
        "*",
        on_post,
        query={
            "filter": 'status = "published"',
            "expand": "author"
        }
    )
    
    # Comments updates
    def on_comment(event):
        update_comments_count(event["record"].get("postId"))
    
    pb.collection("comments").subscribe(
        "*",
        on_comment,
        query={"expand": "user"}
    )

def add_post_to_feed(record):
    """Add a new post to the feed."""
    print(f"New post: {record.get('title')}")

def update_post_in_feed(record):
    """Update a post in the feed."""
    print(f"Post updated: {record.get('title')}")

def update_comments_count(post_id: str):
    """Update comment count for a post."""
    print(f"Comments updated for post: {post_id}")

# Usage
setup_dashboard()
```

### Example 3: User Activity Tracking

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def track_user_activity(user_id: str):
    """Track changes to a user's own records."""
    def on_user_post(event):
        # Only track changes to user's own posts
        if event["record"].get("author") == user_id:
            print(f"Your post {event['action']}: {event['record'].get('title')}")
            
            if event["action"] == "update":
                show_notification("Post updated")
    
    pb.collection("posts").subscribe(
        "*",
        on_user_post,
        query={"filter": f'author = "{user_id}"'}
    )

def show_notification(message: str):
    """Show a notification to the user."""
    print(f"Notification: {message}")

# Usage
pb.collection("users").auth_with_password("user@example.com", "password")
user_id = pb.auth_store.record["id"]
track_user_activity(user_id)
```

### Example 4: Real-time Collaboration

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def track_document_edits(document_id: str):
    """Track when a document is being edited."""
    def on_document_update(event):
        if event["action"] == "update":
            last_editor = event["record"].get("lastEditor")
            updated_at = event["record"].get("updated")
            
            # Show who last edited the document
            show_editor_indicator(last_editor, updated_at)
    
    pb.collection("documents").subscribe(
        document_id,
        on_document_update,
        query={"expand": "lastEditor"}
    )

def show_editor_indicator(editor_id: str, updated_at: str):
    """Show who last edited the document."""
    print(f"Document edited by {editor_id} at {updated_at}")

# Usage
track_document_edits("DOCUMENT_ID")
```

### Example 5: Connection Monitoring

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def handle_disconnect(active_topics):
    """Handle disconnection events."""
    if active_topics:
        print("Connection lost, attempting to reconnect...")
        show_connection_status("Reconnecting...")
    else:
        print("No active subscriptions; connection closed.")

# Monitor connection state
pb.realtime.on_disconnect = handle_disconnect

def on_connect(event):
    """Handle connection establishment."""
    print(f"Connected to realtime: {event.get('clientId')}")
    show_connection_status("Connected")

# Monitor connection establishment
pb.realtime.subscribe("PB_CONNECT", on_connect)

def show_connection_status(status: str):
    """Update connection status in UI."""
    print(f"Connection status: {status}")
```

### Example 6: Conditional Subscriptions

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def handler(event):
    """Handle post events."""
    print(f"Post {event['action']}: {event['record'].get('title')}")

def setup_conditional_subscriptions():
    """Subscribe conditionally based on user state."""
    if pb.auth_store.is_valid():
        # Authenticated user - subscribe to private posts
        pb.collection("posts").subscribe(
            "*",
            handler,
            query={"filter": '@request.auth.id != ""'}
        )
    else:
        # Guest user - subscribe only to public posts
        pb.collection("posts").subscribe(
            "*",
            handler,
            query={"filter": 'public = true'}
        )

# Usage
setup_conditional_subscriptions()
```

### Example 7: Cleanup on Application Exit

```python
from bosbase import BosBase
import atexit

pb = BosBase("http://127.0.0.1:8090")

class RealtimeSubscription:
    """Manage realtime subscriptions with cleanup."""
    
    def __init__(self):
        self.subscriptions = []
        atexit.register(self.cleanup)
    
    def subscribe(self, collection_name: str, topic: str, handler):
        """Subscribe to a topic and track the unsubscribe function."""
        unsubscribe = pb.collection(collection_name).subscribe(topic, handler)
        self.subscriptions.append(unsubscribe)
        return unsubscribe
    
    def cleanup(self):
        """Unsubscribe from all subscriptions."""
        for unsubscribe in self.subscriptions:
            try:
                unsubscribe()
            except Exception as e:
                print(f"Error unsubscribing: {e}")
        self.subscriptions.clear()

# Usage
rt = RealtimeSubscription()

def on_post(event):
    print(f"Post changed: {event}")

rt.subscribe("posts", "*", on_post)

# Cleanup happens automatically on exit
# Or manually: rt.cleanup()
```

## Error Handling

```python
from bosbase import BosBase
from bosbase.exceptions import ClientResponseError

pb = BosBase("http://127.0.0.1:8090")

def handler(event):
    print(f"Event: {event['action']}")

try:
    pb.collection("posts").subscribe("*", handler)
except ClientResponseError as error:
    if error.status == 403:
        print("Permission denied")
    elif error.status == 404:
        print("Collection not found")
    else:
        print(f"Subscription error: {error}")
except Exception as error:
    print(f"Unexpected error: {error}")
```
