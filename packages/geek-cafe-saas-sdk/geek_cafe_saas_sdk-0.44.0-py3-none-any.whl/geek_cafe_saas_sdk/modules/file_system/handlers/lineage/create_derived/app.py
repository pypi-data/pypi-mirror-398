"""
Lambda handler for creating a derived file from a parent file.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.file_system.services import FileSystemService
import base64


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileSystemService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Create a derived file from a parent file.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Expected body (camelCase from frontend):
    {
        "fileName": "data_clean_v1.csv",
        "fileData": "base64_encoded_content",
        "directoryId": "dir-789",  # Optional
        "lineage": "derived",  # Optional - defaults to "derived"
        "metadata": {}  # Optional - any custom metadata
    }
    
    Returns 201 with created derived file
    """
    return handler_wrapper.execute(event, context, create, injected_service)


def create(event: LambdaEvent, service: FileSystemService) -> ServiceResult:
    """
    Business logic for creating derived file.
    """
    payload = event.body()
    
    # Extract parent file ID from path parameters (parent-id)
    parent_id = event.path("parent-id", "parent_id", "parentId")
    if not parent_id:
        raise ValueError("parent file ID is required in path (parent-id)")
    
    # Extract required fields from body
    file_name = payload.get("file_name")
    file_data_b64 = payload.get("file_data")
    if not file_name:
        raise ValueError("file_name is required")
    if not file_data_b64:
        raise ValueError("file_data is required")
    
    # Decode base64 file data
    try:
        file_data = base64.b64decode(file_data_b64)
    except Exception as e:
        raise ValueError(f"Invalid base64 file_data: {str(e)}")
    
    # Extract optional fields
    directory_id = payload.get("directory_id")
    lineage = payload.get("lineage", "derived")
    metadata = payload.get("metadata", {})
    
    # Create derived file
    # Note: tenant_id and user_id come from service's request_context
    result = service.create(
        parent_id=parent_id,
        name=file_name,
        data=file_data,
        directory_id=directory_id,
        lineage=lineage,
        metadata=metadata
    )
    
    return result
