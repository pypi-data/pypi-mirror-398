"""
Lambda handler for deleting files.

Ultra-thin handler - validation happens in service layer.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.file_system.services import FileSystemService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileSystemService,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Delete file (soft or hard delete).
    
    Ultra-thin handler - service handles validation and access control.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Path parameters:
        fileId: File ID
    
    Query parameters:
        hardDelete: "true" or "false" (default: false)
    
    Returns:
        200 with success message or error response
    """
    return handler_wrapper.execute(event, context, delete_file, injected_service)


def delete_file(
    event: LambdaEvent,
    service: FileSystemService
) -> Any:
    """
    Ultra-thin business logic - extract parameters and call service.
    
    Service handles:
    - File existence check
    - Access control (from service.request_context)
    - Soft/hard delete logic
    - S3 cleanup (if hard delete)
    """
    file_id = event.path("fileId", "id")
    hard_delete = event.query_bool("hardDelete")
    
    return service.delete(file_id=file_id,
        hard_delete=hard_delete
    )
