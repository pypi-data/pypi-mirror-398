"""
Generic Lambda handler for generating presigned upload URLs.

Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.

Configuration:
    Consumers can inject configuration values (like bucket names) when invoking:
    
    Example:
        from geek_cafe_saas_sdk.lambda_handlers import create_handler
        
        # Create handler with config
        handler = create_handler(
            service_class=S3FileService,
            require_body=True,
            config={
                "upload_bucket": "my-custom-uploads-bucket",
                "download_bucket": "my-downloads-bucket"
            }
        )
        
        # Or update existing handler
        handler_wrapper.config["upload_bucket"] = "new-bucket"
        
        # In handler logic, access via event:
        bucket = event.config("upload_bucket", default="fallback-bucket")
"""

from typing import Dict, Any, Optional
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.file_system.services.file_system_service import FileSystemService, File
from geek_cafe_saas_sdk.modules.file_system.services.s3_path_service import S3PathService
from geek_cafe_saas_sdk.utilities.response import error_response, success_response
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
import uuid
import os


# Create handler wrapper (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileSystemService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Generate presigned URL for file upload.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional S3FileService for testing
    
    Expected body (camelCase from frontend):
    {
        "fileName": "data.xlsx",
        "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  // Optional
        "expiresIn": 300  // Optional, defaults to 300 seconds
    }
    
    Returns 200 with presigned URL details
    """
    return handler_wrapper.execute(event, context, generate_upload_url_logic, injected_service)


def generate_upload_url_logic(
    event: LambdaEvent,
    service: FileSystemService
) -> ServiceResult:
    """Business logic for generating presigned upload URLs."""

    payload = event.body()
    return service.generate_presigned_upload_url(
        file_name=payload.get("file_name"),
        content_type=payload.get("content_type"),
        expires_in=payload.get("expires_in"),
        bucket_name=payload.get("bucket_name") or event.config("upload_bucket"),
        category=payload.get("category")
    )
    
