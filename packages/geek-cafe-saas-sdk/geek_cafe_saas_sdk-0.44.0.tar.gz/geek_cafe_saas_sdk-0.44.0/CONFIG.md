# Configuration Injection Pattern

The SDK supports runtime configuration injection through the `handler_wrapper.config` dictionary. This allows consumers to override default behaviors without modifying environment variables.

## How It Works

### 1. Consumer Sets Config (e.g., Aplos layer)
```python
from geek_cafe_saas_sdk.modules.file_system.handlers.generate_upload_url.app import handler_wrapper
import os

# Inject custom config before invoking handler
handler_wrapper.config["upload_bucket"] = os.getenv("UPLOAD_BUCKET")
handler_wrapper.config["download_bucket"] = os.getenv("DOWNLOAD_BUCKET")
```

### 2. Handler Accesses Config
```python
def generate_upload_url(event: LambdaEvent, service: S3FileService) -> ServiceResult:
    # Read config from event (which wraps handler_wrapper.config)
    bucket_name = event.config("upload_bucket")
    
    # Pass to service
    result = service.generate_presigned_upload_url(
        key=key,
        bucket=bucket_name  # Uses injected config
    )
```

### 3. Service Fallback Chain
```python
# Services follow this resolution order:
bucket_name = (
    explicit_param        # Function argument takes precedence
    or self.default_bucket   # Service instance default
    or os.getenv("S3_UPLOAD_BUCKET_NAME")  # SDK env var
    or os.getenv("UPLOAD_BUCKET")  # Consumer env var fallback
)
```

## Available Configuration Parameters

### S3FileService

#### `upload_bucket`
**Used by**: `generate_presigned_upload_url()`  
**Purpose**: S3 bucket for file uploads  
**Fallback chain**:
1. `bucket` parameter in method call
2. `handler_wrapper.config["upload_bucket"]`
3. `S3FileService.default_bucket`
4. `S3_UPLOAD_BUCKET_NAME` env var
5. `UPLOAD_BUCKET` env var

**Example**:
```python
handler_wrapper.config["upload_bucket"] = "my-uploads-bucket"
```

#### `download_bucket`
**Used by**: 
- `generate_presigned_download_url()`
- `get_object_versions()`

**Purpose**: S3 bucket for file downloads/retrieval  
**Fallback chain**:
1. `bucket` parameter in method call
2. `handler_wrapper.config["download_bucket"]`
3. `S3FileService.default_bucket`
4. `S3_DOWNLOAD_BUCKET_NAME` env var
5. `DOWNLOAD_BUCKET` env var

**Example**:
```python
handler_wrapper.config["download_bucket"] = "my-downloads-bucket"
```

#### `copy_source_bucket`
**Used by**: `copy_object()`  
**Purpose**: Source bucket for S3 object copy operations  
**Fallback chain**:
1. `source_bucket` parameter
2. `handler_wrapper.config["copy_source_bucket"]`
3. `S3FileService.default_bucket`
4. `COPY_SOURCE_BUCKET` env var

**Example**:
```python
handler_wrapper.config["copy_source_bucket"] = "archive-bucket"
```

#### `copy_dest_bucket`
**Used by**: `copy_object()`  
**Purpose**: Destination bucket for S3 object copy operations  
**Fallback chain**:
1. `dest_bucket` parameter
2. `handler_wrapper.config["copy_dest_bucket"]`
3. `S3FileService.default_bucket`
4. `COPY_DEST_BUCKET` env var

**Example**:
```python
handler_wrapper.config["copy_dest_bucket"] = "processed-bucket"
```

### FileSystemService

#### `table_name`
**Used by**: All DynamoDB operations  
**Purpose**: DynamoDB table for file metadata  
**Fallback chain**:
1. `FileSystemService(table_name=...)`
2. `DYNAMODB_TABLE_NAME` env var

**Example**:
```python
# Usually set during service initialization
service = FileSystemService(table_name="my-files-table")
```

#### `default_bucket`
**Used by**: All S3 operations (inherited from S3FileService)  
**Purpose**: Default bucket when specific upload/download bucket not specified  
**Example**:
```python
service = FileSystemService(default_bucket="my-default-bucket")
```

## Usage Patterns

### Pattern 1: Per-Handler Configuration
Each Aplos handler sets its own config:

```python
# aplos_saas_file_system/handlers/files/generate_upload_url/app.py
from geek_cafe_saas_sdk.modules.file_system.handlers.generate_upload_url.app import (
    lambda_handler as geek_cafe_upload_url, 
    handler_wrapper
)
import os

@with_aplos_claims
def lambda_handler(event, context):
    # Map Aplos env vars to SDK config
    handler_wrapper.config["upload_bucket"] = os.getenv("UPLOAD_BUCKET")
    return geek_cafe_upload_url(event, context)
```

### Pattern 2: Centralized Configuration
Create a config module:

```python
# aplos_saas_file_system/config/sdk_config.py
import os

def configure_sdk_handlers():
    """Configure all SDK handlers with Aplos environment variables."""
    from geek_cafe_saas_sdk.modules.file_system.handlers.generate_upload_url.app import (
        handler_wrapper as upload_wrapper
    )
    from geek_cafe_saas_sdk.modules.file_system.handlers.generate_download_url.app import (
        handler_wrapper as download_wrapper
    )
    
    # Upload configuration
    upload_wrapper.config.update({
        "upload_bucket": os.getenv("UPLOAD_BUCKET"),
    })
    
    # Download configuration
    download_wrapper.config.update({
        "download_bucket": os.getenv("DOWNLOAD_BUCKET"),
    })

# Call once at module import
configure_sdk_handlers()
```

### Pattern 3: Dynamic Configuration
Change config per request:

```python
def lambda_handler(event, context):
    # Could vary by tenant, region, etc.
    tenant_id = event.path("tenant-id")
    handler_wrapper.config["upload_bucket"] = f"uploads-{tenant_id}"
    
    return geek_cafe_upload_url(event, context)
```

## Testing

Config injection works seamlessly with `injected_service`:

```python
def test_with_custom_bucket(service_injection_helper):
    # Set config for test
    handler_wrapper.config["upload_bucket"] = "test-upload-bucket"
    
    event = create_event(...)
    service = service_injection_helper.create_file_system_service()
    
    response = lambda_handler(event, None, injected_service=service)
    assert response["statusCode"] == 200
```

## Benefits

✅ **Decouples environment variables** - Consumers use their own naming conventions  
✅ **No SDK changes needed** - Works with existing handlers  
✅ **Runtime flexibility** - Config can vary per request/tenant  
✅ **Clear ownership** - Consumer layer handles consumer config  
✅ **Testing friendly** - Easy to override in tests  
✅ **Backwards compatible** - Falls back to env vars if config not set

## Adding New Config Parameters

To add a new config parameter:

1. **Document it** in this file
2. **Handler**: Access via `event.config("param_name")`
3. **Service**: Add to fallback chain: `param or event_config or env_var`
4. **Update tests** if needed

Example:
```python
# Handler
encryption_key = event.config("s3_encryption_key")

# Service
def some_method(self, encryption_key=None):
    key = encryption_key or os.getenv("S3_ENCRYPTION_KEY")
```
