# Lambda Handler Reference Implementations

## Overview

This directory contains **reference Lambda handler implementations** for the file system services. These handlers are **templates** meant to be copied and customized by projects consuming this SDK.

## Important: These Are Not Deployed

**This SDK does not deploy Lambda functions to AWS.** These handlers serve as:

- ✅ **Reference implementations** showing how to use the SDK services
- ✅ **Starting templates** for your own Lambda functions  
- ✅ **Best practice examples** for structuring handlers
- ✅ **Integration patterns** with API Gateway

## How to Use

### 1. Install the SDK in Your Project

```bash
pip install geek-cafe-saas-sdk
```

### 2. Copy Handlers You Need

Copy the handler files into your project:

```bash
# Copy specific handler
cp lambda_handlers/files/upload/app.py my-project/handlers/file_upload.py

# Or copy entire categories
cp -r lambda_handlers/files my-project/handlers/
```

### 3. Customize for Your Needs

All handlers follow this pattern:

```python
from geek_cafe_saas_sdk.modules.file_system.services.file_system_service import FileSystemService

def lambda_handler(event, context):
    # 1. Extract parameters from event
    # 2. Initialize services from SDK
    # 3. Call service methods
    # 4. Return formatted response
```

Customize:
- **Authentication**: Add Cognito, JWT, or custom auth
- **Validation**: Add business-specific rules
- **Error handling**: Match your error format
- **Logging**: Integrate with your logging system
- **Metrics**: Add custom CloudWatch metrics

### 4. Deploy with Your Infrastructure

Deploy using your preferred tool:

**Serverless Framework:**
```yaml
functions:
  fileUpload:
    handler: handlers/file_upload.lambda_handler
```

**AWS CDK:**
```python
lambda_.Function(
    self, "FileUpload",
    handler="file_upload.lambda_handler",
    code=lambda_.Code.from_asset("handlers")
)
```

---

## Handler Structure

### File Operations

| Handler | Path | Purpose |
|---------|------|---------|
| `files/upload/app.py` | `POST /files` | Upload new file |
| `files/download/app.py` | `GET /files/{id}/download` | Download file |
| `files/get/app.py` | `GET /files/{id}` | Get metadata |
| `files/update/app.py` | `PUT /files/{id}` | Update metadata |
| `files/delete/app.py` | `DELETE /files/{id}` | Delete file |
| `files/list/app.py` | `GET /files` | List files |

### Directory Operations

| Handler | Path | Purpose |
|---------|------|---------|
| `directories/create/app.py` | `POST /directories` | Create directory |
| `directories/get/app.py` | `GET /directories/{id}` | Get directory |
| `directories/list/app.py` | `GET /directories` | List directories |
| `directories/move/app.py` | `PUT /directories/{id}/move` | Move directory |
| `directories/delete/app.py` | `DELETE /directories/{id}` | Delete directory |

### Sharing Operations

| Handler | Path | Purpose |
|---------|------|---------|
| `files/share/app.py` | `POST /files/share` | Share file |
| `files/shares/list/app.py` | `GET /files/shares` | List shares |
| `files/shares/revoke/app.py` | `DELETE /files/shares/{id}` | Revoke share |

---

## Common Customizations

### Add Authentication

```python
def lambda_handler(event, context):
    # Validate JWT token
    token = event['headers'].get('Authorization')
    user = validate_token(token)
    
    # Use validated user_id
    result = file_service.create(
        tenant_id=user.tenant_id,
        user_id=user.user_id,
        ...
    )
```

### Add Request Validation

```python
def lambda_handler(event, context):
    body = json.loads(event['body'])
    
    # Validate with your schema
    errors = validate_upload_request(body)
    if errors:
        return {
            'statusCode': 400,
            'body': json.dumps({'errors': errors})
        }
```

### Add Custom Error Handling

```python
def lambda_handler(event, context):
    try:
        result = file_service.create(...)
        
        if not result.success:
            # Map SDK errors to your error codes
            error_code = map_error_code(result.error_code)
            return custom_error_response(error_code, result.message)
    
    except CustomException as e:
        # Handle business exceptions
        return business_error_response(e)
```

### Add Logging and Metrics

```python
import logging
from aws_lambda_powertools import Logger, Metrics

logger = Logger()
metrics = Metrics()

@logger.inject_lambda_context
@metrics.log_metrics
def lambda_handler(event, context):
    logger.info("File upload requested", extra={
        "tenant_id": tenant_id,
        "file_name": file_name
    })
    
    metrics.add_metric(name="FileUploads", unit="Count", value=1)
    
    result = file_service.create(...)
    
    if result.success:
        metrics.add_metric(name="FileUploadSuccess", unit="Count", value=1)
    else:
        metrics.add_metric(name="FileUploadFailure", unit="Count", value=1)
```

---

## Environment Variables

All handlers expect these environment variables:

```bash
DYNAMODB_TABLE_NAME=your-table-name
S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1
```

Set these in your infrastructure code (examples will vary by tool, e.g., CDK):

```python
# CDK example (Python)
lambda_.Function(
    self, "FileUpload",
    handler="file_upload.lambda_handler",
    code=lambda_.Code.from_asset("handlers"),
    environment={
        "DYNAMODB_TABLE_NAME": files_table.table_name,
        "S3_BUCKET_NAME": files_bucket.bucket_name,
    }
)
```

---

## Required Dependencies

When deploying, include:

```
geek-cafe-saas-sdk
boto3
boto3-assist
```

Use Lambda Layers for dependencies:

```bash
# Create layer
mkdir -p layer/python
pip install -t layer/python geek-cafe-saas-sdk boto3-assist
cd layer && zip -r ../dependencies.zip .
```

---

## Testing Handlers Locally

### With Python

```python
from your_handlers.file_upload import lambda_handler

event = {
    "body": {
        "tenant_id": "test",
        "user_id": "user1",
        "file_name": "test.txt",
        "file_data": "SGVsbG8="
    }
}

response = lambda_handler(event, None)
print(response)
```

---

## Example: Complete Custom Handler

Here's how to create a custom handler based on the SDK:

```python
"""
Custom file upload handler for MyApp.
"""

import json
import base64
import os
from typing import Dict, Any

from geek_cafe_saas_sdk.modules.file_system.services.file_system_service import FileSystemService
from geek_cafe_saas_sdk.modules.file_system.services.s3_file_service import S3FileService
from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.s3.s3_connection import S3Connection
from boto3_assist.s3.s3_object import S3Object
from boto3_assist.s3.s3_bucket import S3Bucket

from myapp.auth import validate_jwt
from myapp.validation import validate_file_upload
from myapp.logging import get_logger

logger = get_logger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Custom file upload handler with MyApp-specific logic."""
    
    # 1. Authenticate user
    try:
        user = validate_jwt(event['headers']['Authorization'])
    except Exception as e:
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Unauthorized'})
        }
    
    # 2. Parse and validate request
    body = json.loads(event['body'])
    errors = validate_file_upload(body, user)
    if errors:
        return {
            'statusCode': 400,
            'body': json.dumps({'errors': errors})
        }
    
    # 3. Initialize SDK services
    db = DynamoDB()
    connection = S3Connection()
    
    s3_service = S3FileService(
        s3_object=S3Object(connection=connection),
        s3_bucket=S3Bucket(connection=connection),
        default_bucket=os.environ['S3_BUCKET_NAME']
    )
    
    file_service = FileSystemService(
        dynamodb=db,
        table_name=os.environ['DYNAMODB_TABLE_NAME'],
        s3_service=s3_service,
        default_bucket=os.environ['S3_BUCKET_NAME']
    )
    
    # 4. Upload file using SDK
    try:
        result = file_service.create(
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            file_name=body['file_name'],
            file_data=base64.b64decode(body['file_data']),
            mime_type=body.get('mime_type', 'application/octet-stream'),
            directory_id=body.get('directory_id'),
            tags=body.get('tags', [])
        )
        
        if result.success:
            logger.info(f"File uploaded: {result.data.file_id}")
            
            # 5. Return MyApp-formatted response
            return {
                'statusCode': 201,
                'body': json.dumps({
                    'id': result.data.file_id,
                    'name': result.data.name,
                    'size': result.data.size,
                    'created_at': result.data.created_utc_ts
                })
            }
        else:
            logger.error(f"Upload failed: {result.message}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': result.message,
                    'code': result.error_code
                })
            }
    
    except Exception as e:
        logger.exception("Unexpected error during upload")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
```

---

## Support

- **Service Documentation**: See main SDK docs for service usage
- **Usage Examples**: See `docs/FILE_SYSTEM_USAGE.md`
- **API Reference**: See `docs/FILE_SYSTEM_API.md`
- **Integration Tests**: See `tests/test_files_integration.py` for complete workflows

---

**Remember**: These handlers are starting points. Customize them to fit your application's needs!
