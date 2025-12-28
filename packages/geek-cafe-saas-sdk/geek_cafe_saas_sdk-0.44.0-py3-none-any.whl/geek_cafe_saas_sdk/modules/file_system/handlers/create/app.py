"""
Lambda handler for creating/uploading files.

Ultra-thin handler - all validation and transformation happens in the service layer.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.file_system.services import FileSystemService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileSystemService,
    require_body=True,
    convert_request_case=True  # Converts camelCase → snake_case
)

def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Create a new file (upload).
    
    Ultra-thin handler - validation, transformation, and security injection
    all happen in the FileSystemService layer.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Expected body (camelCase → auto-converted to snake_case):
    {
        "name": "document.pdf",              # Required
        "data": "base64_encoded_content",    # Required (or bytes)
        "mimeType": "application/pdf",       # Required
        "directoryId": "dir-123",            # Optional
        "description": "Q1 Report",          # Optional
        "tags": ["report", "2024"],          # Optional
        "category": "financial",             # Optional
        
        # Lineage fields (optional):
        "parentId": "file-parent",
        "lineage": {...},
        "transformationType": "convert",
        "transformationOperation": "xls_to_csv",
        "transformationMetadata": {"source": "xls", "target": "csv"}
    }
    
    Returns:
        201 with created file metadata or error response
    """
    return handler_wrapper.execute(event, context, upload_file, injected_service)


def upload_file(
    event: LambdaEvent,
    service: FileSystemService
) -> Any:
    """
    Ultra-thin business logic - pass payload to service.
    
    Service handles:
    - Field validation (unknown field detection)
    - Required field validation  
    - Base64 decoding
    - Security context injection (tenant_id, owner_id from service.request_context)
    - S3 upload
    - DynamoDB save
    
    Returns:
        ServiceResult from service.create()
    """
    return service.create(**event.body())
