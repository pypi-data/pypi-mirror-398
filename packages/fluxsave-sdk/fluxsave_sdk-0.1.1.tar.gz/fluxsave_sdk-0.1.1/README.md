# fluxsave-sdk

Python SDK for FluxSave. API key + secret authentication with file upload and management helpers.

## Install

```bash
pip install fluxsave-sdk
```

## Usage

```python
from fluxsave_sdk import FluxsaveClient

client = FluxsaveClient(
    base_url="https://fluxsaveapi.lutheralien.com",
    api_key="fs_xxx",
    api_secret="sk_xxx",
)

response = client.upload_file("./photo.png", name="marketing-hero", transform=True)
print(response)
```

## API

- `upload_file(path, name=None, transform=None)`
- `upload_files(paths, name=None, transform=None)`
- `list_files()`
- `get_file_metadata(file_id)`
- `update_file(file_id, path, name=None, transform=None)`
- `delete_file(file_id)`
- `get_metrics()`
- `build_file_url(file_id, **options)`

## Docs

https://fluxsave-sdk-docs.vercel.app/
