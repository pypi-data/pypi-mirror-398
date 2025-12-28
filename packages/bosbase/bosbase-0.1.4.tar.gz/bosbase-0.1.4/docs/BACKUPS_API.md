# Backups API - Python SDK

Automate snapshot management with the Backups API.

## List Backups

```python
backups = pb.backups.get_full_list()
for item in backups:
    print(item["name"], item["size"], item["created"])
```

## Create a Backup

```python
pb.backups.create("nightly-2024-06-20")
```

## Upload Existing Backup Files

```python
with open("bosbase-export.pbb", "rb") as fh:
    pb.backups.upload({"file": ("bosbase-export.pbb", fh, "application/octet-stream")})
```

## Delete or Restore

```python
pb.backups.delete("nightly-2024-06-20.pbb")
pb.backups.restore("nightly-2024-06-20.pbb")
```

During restore the server reboots; wait for the API to come back online before issuing more requests.

## Download URLs

```python
token = pb.files.get_token()
download_url = pb.backups.get_download_url(token, "nightly-2024-06-20.pbb")
```

## Tips

1. Always generate a new backup before performing major schema migrations.
2. Use the upload endpoint to seed staging environments with production data.
3. Pair backups with Git-tracked schema exports for complete recoverability.
4. Guard restore endpoints with additional operational controls (e.g. runbooks, approvals) to avoid accidental overwrites.
