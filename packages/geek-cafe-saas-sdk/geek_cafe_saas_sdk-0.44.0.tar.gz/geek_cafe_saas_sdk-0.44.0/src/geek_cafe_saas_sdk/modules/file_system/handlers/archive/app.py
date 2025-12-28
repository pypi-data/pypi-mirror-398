"""
Lambda handler for getting file metadata.

Ultra-thin handler - validation happens in service layer.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.file_system.services import FileSystemService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileSystemService,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Archive a file by ID.
    
    Ultra-thin handler - service handles validation and access control.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Path parameters:
        fileId: File ID
    
    Returns:
        200 with file metadata or error response
    """
    return handler_wrapper.execute(event, context, archive_file, injected_service)


def archive_file(
    event: LambdaEvent,
    service: FileSystemService
) -> Any:
    """
    Ultra-thin business logic - extract ID and call service.
    
    Service handles:
    - Field validation
    - File existence check
    - Access control (from service.request_context)
    - Data retrieval
    
    Args:
        event: Lambda event wrapper
        service: FileSystemService with RequestContext
    
    Returns:
        ServiceResult from service.archive()
    """
    file_id = event.path("file-id") or event.body("file_id")
    if not file_id:
        return ServiceResult.error_result("Missing file ID. Add the file id to the path or body.")
    return service.archive(file_id=file_id)
