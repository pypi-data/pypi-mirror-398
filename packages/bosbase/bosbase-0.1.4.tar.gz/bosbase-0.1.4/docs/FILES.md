# Files - Python SDK

File handling is unified across all BosBase services. You use multipart/form-data to upload files and the File API to create secure download links.

## Uploading Files with Records

Pass a `files` dict to `create` or `update`.

```python
with open("avatar.jpg", "rb") as fh:
    pb.collection("users").update(
        "RECORD_ID",
        body={"name": "Jane"},
        files={"avatar": ("avatar.jpg", fh, "image/jpeg")},
    )
```

Multiple files can be uploaded in one request by including several entries in the dict or by sharing the same field name with a list of tuples.

## Direct File Uploads

Use the Files API when you only need to update the file content:

```python
files_service = pb.files

record = pb.collection("documents").get_one("doc123")

with open("updated.pdf", "rb") as fh:
    files_service.get_url(record, "attachment.pdf")  # builds download URL
```

## Building File URLs

```python
url = pb.files.get_url(
    record,
    "cover.png",
    thumb="300x300",
    query={"token": "optionalTemporaryToken"},
)
```

- `thumb` accepts thumbnail presets or raw resizing strings (`600x400`).
- `download=True` forces a download response.
- `token` attaches a private file token (see below).

## Private File Tokens

Generate time-limited tokens tied to the current auth record:

```python
token = pb.files.get_token()

secure_url = pb.files.get_url(
    record,
    "invoice.pdf",
    token=token,
)
```

Tokens expire according to the auth collection settings.

## Handling Protected Files in Batches

When building URLs for exported data, reuse the `get_url` helper:

```python
orders = pb.collection("orders").get_full_list(query={"expand": "customer"})
token = pb.files.get_token()

download_links = [
    pb.files.get_url(order, "receipt.pdf", token=token)
    for order in orders
    if order.get("receipt")
]
```

## Tips

- Always send files as binary mode (`"rb"`).
- When uploading large files wrap the file object with `io.BufferedReader` to benefit from streaming.
- Use thumbnails for previews rather than storing separate preview fields.
- Generate download URLs server-side if you need to sign them with a privileged token; otherwise `get_url` can be called by the client directly.

## Complete Examples

### Example 1: Image Upload with Thumbnails

```python
from bosbase import BosBase

pb = BosBase("http://localhost:8090")
pb.collection("_superusers").auth_with_password("admin@example.com", "password")

# Create collection with image field and thumbnails
collection = pb.collections.create_base(
    "products",
    overrides={
        "fields": [
            {"name": "name", "type": "text", "required": True},
            {
                "name": "image",
                "type": "file",
                "maxSelect": 1,
                "mimeTypes": ["image/jpeg", "image/png"],
                "thumbs": ["100x100", "300x300", "800x600f"]  # Thumbnail sizes
            }
        ]
    }
)

# Upload product with image
with open("product.jpg", "rb") as image_file:
    product = pb.collection("products").create(
        body={"name": "My Product"},
        files={"image": ("product.jpg", image_file, "image/jpeg")}
    )

# Display thumbnail in UI
thumbnail_url = pb.files.get_url(
    product,
    product["image"],
    thumb="300x300"
)

print(f"Thumbnail URL: {thumbnail_url}")
```

### Example 2: Multiple File Upload with Progress

```python
from bosbase import BosBase
from tqdm import tqdm  # Optional: for progress bar

pb = BosBase("http://127.0.0.1:8090")

def upload_multiple_files(file_paths: list, title: str = "Document Set"):
    """Upload multiple files with progress tracking."""
    files_dict = {}
    
    for idx, file_path in enumerate(file_paths):
        with open(file_path, "rb") as fh:
            filename = file_path.split("/")[-1]
            content_type = "application/octet-stream"  # Adjust as needed
            
            # For multiple files, use a list or append to the same field
            if "documents" not in files_dict:
                files_dict["documents"] = []
            files_dict["documents"].append((filename, fh.read(), content_type))
    
    try:
        # Note: For actual progress tracking, you'd need to use requests with streaming
        # or implement a custom upload handler
        record = pb.collection("example").create(
            body={"title": title},
            files=files_dict
        )
        
        print(f"Uploaded files: {record.get('documents', [])}")
        return record
    except Exception as err:
        print(f"Upload failed: {err}")
        raise

# Usage
file_paths = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
upload_multiple_files(file_paths, "Document Set")
```

### Example 3: File Management UI

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

class FileManager:
    def __init__(self, collection_id: str, record_id: str):
        self.collection_id = collection_id
        self.record_id = record_id
        self.record = None
    
    def load(self):
        """Load record with files."""
        self.record = pb.collection(self.collection_id).get_one(self.record_id)
        return self.record
    
    def get_files(self):
        """Get list of files from record."""
        files_field = self.record.get("documents")
        if isinstance(files_field, list):
            return files_field
        elif files_field:
            return [files_field]
        return []
    
    def get_file_url(self, filename: str):
        """Get download URL for a file."""
        return pb.files.get_url(self.record, filename)
    
    def delete_file(self, filename: str):
        """Delete a file from the record."""
        pb.collection(self.collection_id).update(
            self.record_id,
            body={"documents-": [filename]}
        )
        self.load()  # Reload
    
    def add_files(self, file_paths: list):
        """Add files to the record."""
        files_dict = {}
        for file_path in file_paths:
            with open(file_path, "rb") as fh:
                filename = file_path.split("/")[-1]
                content_type = "application/octet-stream"
                
                if "documents" not in files_dict:
                    files_dict["documents"] = []
                files_dict["documents"].append((filename, fh.read(), content_type))
        
        pb.collection(self.collection_id).update(
            self.record_id,
            files=files_dict
        )
        self.load()  # Reload

# Usage
manager = FileManager("example", "RECORD_ID")
manager.load()

# List files
for filename in manager.get_files():
    url = manager.get_file_url(filename)
    print(f"{filename}: {url}")

# Delete a file
# manager.delete_file("old_file.pdf")

# Add new files
# manager.add_files(["new_file1.pdf", "new_file2.pdf"])
```

### Example 4: Protected Document Viewer

```python
from bosbase import BosBase
from bosbase.exceptions import ClientResponseError

pb = BosBase("http://127.0.0.1:8090")

def view_protected_document(record_id: str, filename: str):
    """View a protected document with authentication."""
    # Authenticate if needed
    if not pb.auth_store.is_valid():
        pb.collection("users").auth_with_password("user@example.com", "pass")
    
    # Get token
    try:
        token = pb.files.get_token()
    except Exception as err:
        print(f"Failed to get file token: {err}")
        return None
    
    # Get record and file URL
    record = pb.collection("documents").get_one(record_id)
    url = pb.files.get_url(record, filename, token=token)
    
    # Return URL (in a web app, you might redirect or return this)
    print(f"Protected document URL: {url}")
    return url

# Usage
url = view_protected_document("doc_id_123", "invoice.pdf")
```

### Example 5: Image Gallery with Thumbnails

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")

def display_image_gallery(record_id: str):
    """Display image gallery with thumbnails."""
    record = pb.collection("gallery").get_one(record_id)
    images = record.get("images", [])  # Array of filenames
    
    gallery_items = []
    
    for filename in images:
        # Thumbnail for grid view
        thumb_url = pb.files.get_url(
            record,
            filename,
            thumb="200x200f"  # Fit inside 200x200
        )
        
        # Full size for lightbox
        full_url = pb.files.get_url(
            record,
            filename,
            thumb="1200x800f"  # Larger size
        )
        
        gallery_items.append({
            "filename": filename,
            "thumbnail": thumb_url,
            "full": full_url
        })
    
    return gallery_items

# Usage
gallery = display_image_gallery("gallery_id_123")
for item in gallery:
    print(f"{item['filename']}:")
    print(f"  Thumbnail: {item['thumbnail']}")
    print(f"  Full: {item['full']}")
```
