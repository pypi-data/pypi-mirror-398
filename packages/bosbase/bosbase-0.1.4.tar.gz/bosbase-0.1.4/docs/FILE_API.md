# File API - Python SDK

In addition to uploading files through record mutations, BosBase exposes a dedicated File API for generating signed URLs and serving files.

## Download URLs

```python
files = pb.files
record = pb.collection("documents").get_one("doc123")

public_url = files.get_url(record, "manual.pdf")
```

`get_url` automatically encodes the collection name, record ID, and filename.

### Thumbnails

Add a `thumb` parameter to request dynamic thumbnails:

```python
thumb_url = files.get_url(record, "cover.png", thumb="300x300")
```

### Forced Download

```python
download = files.get_url(record, "backup.zip", download=True)
```

## File Tokens

Protected files require a temporary token tied to the authenticated record.

```python
token = files.get_token()
secure_url = files.get_url(record, "invoice.pdf", token=token)
```

Tokens follow the configuration under *Auth Collection → File tokens*. They expire automatically; request new tokens when needed.

## Serving Files from Backups

When generating download links inside automation scripts:

```python
token = files.get_token()
backups = pb.backups.get_full_list()

links = [
    pb.backups.get_download_url(token, backup["key"])
    for backup in backups
]
```

## Tips

1. Generate the token on the server and forward the URL to clients if you do not want clients to know about the API base URL.
2. Combine `token` + `thumb` for secure preview images.
3. The URLs can be safely cached because they include the token and filename; once the token expires the link stops working.
4. Use HTTPS when exposing URLs to the public internet—BosBase does not add TLS itself.

## Complete Examples

### Example 1: Image Gallery

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def display_image_gallery(record_id: str):
    """Display image gallery with thumbnails."""
    record = pb.collection("posts").get_one(record_id)
    
    # Handle both single image and multiple images
    images = record.get("images", [])
    if not isinstance(images, list):
        images = [record.get("image")] if record.get("image") else []
    
    gallery_items = []
    
    for filename in images:
        # Thumbnail for gallery
        thumb_url = pb.files.get_url(record, filename, thumb="200x200")
        
        # Full image URL
        full_url = pb.files.get_url(record, filename)
        
        gallery_items.append({
            "filename": filename,
            "thumbnail": thumb_url,
            "full": full_url
        })
    
    return gallery_items

# Usage
gallery = display_image_gallery("post_id_123")
for item in gallery:
    print(f"{item['filename']}: {item['thumbnail']}")
```

### Example 2: File Download Handler

```python
from bosbase import BosBase
import webbrowser

pb = BosBase("http://127.0.0.1:8090")

def download_file(record_id: str, filename: str):
    """Download a file from a record."""
    record = pb.collection("documents").get_one(record_id)
    
    # Get download URL
    download_url = pb.files.get_url(record, filename, download=True)
    
    # In a web application, you would return this URL or redirect to it
    # For CLI, you might use requests to download
    print(f"Download URL: {download_url}")
    
    # Optionally open in browser
    # webbrowser.open(download_url)
    
    return download_url

# Usage
url = download_file("doc_id_123", "manual.pdf")
```

### Example 3: Protected File Viewer

```python
from bosbase import BosBase
from bosbase.exceptions import ClientResponseError

pb = BosBase("http://127.0.0.1:8090")

def view_protected_file(record_id: str):
    """View a protected file with authentication."""
    # Authenticate
    if not pb.auth_store.is_valid():
        pb.collection("users").auth_with_password("user@example.com", "password")
    
    # Get record
    record = pb.collection("private_docs").get_one(record_id)
    
    # Get token
    try:
        token = pb.files.get_token()
    except Exception as error:
        print(f"Failed to get file token: {error}")
        return None
    
    # Get file URL
    filename = record.get("file")
    file_url = pb.files.get_url(record, filename, token=token)
    
    # Display based on file type
    ext = filename.split(".")[-1].lower() if filename else ""
    
    file_info = {
        "url": file_url,
        "type": "unknown"
    }
    
    if ext in ["jpg", "jpeg", "png", "gif", "webp"]:
        file_info["type"] = "image"
    elif ext == "pdf":
        file_info["type"] = "pdf"
    else:
        file_info["type"] = "download"
    
    return file_info

# Usage
file_info = view_protected_file("doc_id_123")
if file_info:
    print(f"File URL: {file_info['url']}")
    print(f"File type: {file_info['type']}")
```

### Example 4: Responsive Image URLs

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def get_responsive_image_urls(record_id: str, field_name: str):
    """Get responsive image URLs for different screen sizes."""
    record = pb.collection("posts").get_one(record_id)
    
    if not record or not record.get(field_name):
        return None
    
    filename = record[field_name]
    
    # Generate URLs for different sizes
    urls = {
        "base": pb.files.get_url(record, filename),
        "small": pb.files.get_url(record, filename, thumb="300x300"),
        "medium": pb.files.get_url(record, filename, thumb="400x400"),
        "large": pb.files.get_url(record, filename, thumb="800x800")
    }
    
    return urls

# Usage
urls = get_responsive_image_urls("post_id_123", "cover")
if urls:
    print(f"Small: {urls['small']}")
    print(f"Medium: {urls['medium']}")
    print(f"Large: {urls['large']}")
```

### Example 5: Multiple Files with Thumbnails

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def display_file_list(record_id: str):
    """Display a list of files with thumbnails for images."""
    record = pb.collection("attachments").get_one(record_id)
    
    files = record.get("files", [])
    if not isinstance(files, list):
        files = [files] if files else []
    
    file_items = []
    
    for filename in files:
        ext = filename.split(".")[-1].lower() if filename else ""
        is_image = ext in ["jpg", "jpeg", "png", "gif", "webp"]
        
        file_item = {
            "filename": filename,
            "is_image": is_image,
            "download_url": pb.files.get_url(record, filename, download=True)
        }
        
        if is_image:
            # Show thumbnail
            file_item["thumbnail"] = pb.files.get_url(record, filename, thumb="100x100")
        else:
            file_item["thumbnail"] = None
        
        file_items.append(file_item)
    
    return file_items

# Usage
files = display_file_list("attachment_id_123")
for file_item in files:
    print(f"{file_item['filename']}: {file_item['download_url']}")
    if file_item.get("thumbnail"):
        print(f"  Thumbnail: {file_item['thumbnail']}")
```

### Example 6: Image Upload Preview with Thumbnail

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def preview_uploaded_image(record: dict, filename: str):
    """Get preview URL for an uploaded image."""
    # Get thumbnail for preview
    preview_url = pb.files.get_url(
        record,
        filename,
        thumb="200x200f"  # Fit to 200x200 without cropping
    )
    
    # Full URL for viewing
    full_url = pb.files.get_url(record, filename)
    
    return {
        "preview": preview_url,
        "full": full_url,
        "filename": filename
    }

# Usage (after uploading an image)
record = pb.collection("posts").create(
    body={"title": "My Post"},
    files={"image": ("image.jpg", open("image.jpg", "rb"), "image/jpeg")}
)

preview = preview_uploaded_image(record, record["image"])
print(f"Preview URL: {preview['preview']}")
print(f"Full URL: {preview['full']}")
```

## Error Handling

```python
from bosbase import BosBase
from bosbase.exceptions import ClientResponseError
import requests

pb = BosBase("http://127.0.0.1:8090")

def get_file_url_safely(record: dict, filename: str):
    """Safely get file URL with error handling."""
    try:
        file_url = pb.files.get_url(record, filename)
        
        # Verify URL is valid
        if not file_url:
            raise ValueError("Invalid file URL")
        
        # Optionally verify the file exists
        response = requests.head(file_url, timeout=5)
        if response.status_code != 200:
            raise ValueError(f"File not accessible: {response.status_code}")
        
        return file_url
        
    except Exception as error:
        print(f"File access error: {error}")
        return None

# Usage
record = pb.collection("posts").get_one("post_id_123")
url = get_file_url_safely(record, record.get("image"))
if url:
    print(f"File URL: {url}")
```

### Protected File Token Error Handling

```python
from bosbase import BosBase
from bosbase.exceptions import ClientResponseError

pb = BosBase("http://127.0.0.1:8090")

def get_protected_file_url(record: dict, filename: str):
    """Get protected file URL with error handling."""
    try:
        # Get token
        token = pb.files.get_token()
        
        # Get file URL
        return pb.files.get_url(record, filename, token=token)
        
    except ClientResponseError as error:
        if error.status == 401:
            print("Not authenticated")
            # Redirect to login
        elif error.status == 403:
            print("No permission to access file")
        else:
            print(f"Failed to get file token: {error}")
        return None
    except Exception as error:
        print(f"Unexpected error: {error}")
        return None

# Usage
record = pb.collection("private_docs").get_one("doc_id_123")
url = get_protected_file_url(record, record.get("file"))
if url:
    print(f"Protected file URL: {url}")
```

## Best Practices

1. **Use Thumbnails for Lists**: Use thumbnails when displaying images in lists/grids to reduce bandwidth
2. **Lazy Loading**: Consider lazy loading for images below the fold in web applications
3. **Cache Tokens**: Store file tokens and reuse them until they expire
4. **Error Handling**: Always handle file loading errors gracefully
5. **Content-Type**: Let the server handle content-type detection automatically
6. **Range Requests**: The API supports Range requests for efficient video/audio streaming
7. **Caching**: Files are cached with a 30-day cache-control header
8. **Security**: Always use tokens for protected files, never expose them in client-side code
