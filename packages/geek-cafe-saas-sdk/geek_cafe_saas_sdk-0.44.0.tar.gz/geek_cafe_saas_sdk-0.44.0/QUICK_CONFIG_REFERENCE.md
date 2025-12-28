# Quick Config Reference

## TL;DR
```python
# In your Aplos handler:
from geek_cafe_saas_sdk.modules.file_system.handlers.generate_upload_url.app import handler_wrapper
import os

handler_wrapper.config["upload_bucket"] = os.getenv("UPLOAD_BUCKET")
```

## Available Config Keys

| Config Key | Used By | Purpose |
|------------|---------|---------|
| `upload_bucket` | `generate_presigned_upload_url()` | S3 bucket for uploads |
| `download_bucket` | `generate_presigned_download_url()`, `get_object_versions()` | S3 bucket for downloads |
| `copy_source_bucket` | `copy_object()` | Source bucket for copies |
| `copy_dest_bucket` | `copy_object()` | Destination bucket for copies |

## Resolution Order (Priority)

1. ⭐ **Method parameter** - `service.method(bucket="my-bucket")`
2. 🔧 **Handler config** - `handler_wrapper.config["upload_bucket"]`
3. 🏠 **Service default** - `S3FileService(default_bucket="...")`
4. 🌍 **Environment vars** - `S3_UPLOAD_BUCKET_NAME`, `UPLOAD_BUCKET`, etc.

## Common Patterns

### Pattern: Single Handler Config
```python
# aplos_saas_file_system/handlers/files/generate_upload_url/app.py
from geek_cafe_saas_sdk.modules.file_system.handlers.generate_upload_url.app import (
    lambda_handler as geek_cafe_upload_url,
    handler_wrapper
)
import os

def lambda_handler(event, context):
    handler_wrapper.config["upload_bucket"] = os.getenv("UPLOAD_BUCKET")
    return geek_cafe_upload_url(event, context)
```

### Pattern: Multi-Bucket Setup
```python
def lambda_handler(event, context):
    # Different buckets for different operations
    handler_wrapper.config["upload_bucket"] = "uploads-prod"
    handler_wrapper.config["download_bucket"] = "downloads-cdn"
    handler_wrapper.config["copy_source_bucket"] = "archive"
    handler_wrapper.config["copy_dest_bucket"] = "processed"
    
    return geek_cafe_handler(event, context)
```

### Pattern: Dynamic Per-Tenant Buckets
```python
def lambda_handler(event, context):
    tenant_id = event.path("tenant-id")
    region = event.query("region", default="us-east-1")
    
    # Tenant-specific buckets
    handler_wrapper.config["upload_bucket"] = f"uploads-{tenant_id}-{region}"
    handler_wrapper.config["download_bucket"] = f"downloads-{tenant_id}-{region}"
    
    return geek_cafe_handler(event, context)
```

## Testing
Config works with `injected_service`:

```python
def test_custom_bucket():
    handler_wrapper.config["upload_bucket"] = "test-bucket"
    
    event = create_event(...)
    service = service_injection_helper.create_file_system_service()
    
    response = lambda_handler(event, None, injected_service=service)
    # Service will use "test-bucket"
```

## Full Documentation
See [CONFIG.md](./CONFIG.md) for complete documentation.
