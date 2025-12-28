"""
Lambda handler for updating file metadata.

Ultra-thin handler - validation happens in service layer.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.file_system.services import FileSystemService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileSystemService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Update file metadata.
    
    Ultra-thin handler - service handles validation and access control.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Path parameters:
        fileId: File ID
    
    Body (camelCase → auto-converted to snake_case):
    {
        "description": "Updated description",
        "tags": ["updated", "tags"],
        "directoryId": "new-dir-id",
        "category": "updated-category"
    }
    
    Returns:
        200 with updated file metadata or error response
    """
    return handler_wrapper.execute(event, context, update_file, injected_service)


def update_file(
    event: LambdaEvent,
    service: FileSystemService
) -> Any:
    """
    Ultra-thin business logic - extract ID and payload, call service.
    
    Service handles:
    - Field validation
    - Access control (from service.request_context)
    - Update logic
    """
    file_id = event.path("file-id", "fileId")
    payload = event.body()
    
    return service.update(file_id=file_id,
        **payload  # Spread all update fields
    )
