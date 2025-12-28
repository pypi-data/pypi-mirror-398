"""
Lambda handler for listing files.

Ultra-thin handler - validation happens in service layer.

Requires authentication (secure mode).
"""
from typing import Dict, Any, Optional
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.services.resource_meta_entry_service import ResourceMetaEntryService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ResourceMetaEntryService,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    List files.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Query parameters:
        directoryId: Filter by directory (optional)
        ownerId: Filter by owner (optional)
        limit: Max results (optional, default: 250)
    
    Returns 200 with list of files
    """
    return handler_wrapper.execute(event, context, list_files, injected_service)


def get_metadata(
    event: LambdaEvent,
    service: ResourceMetaEntryService,    
    resource_id: Optional[str] = None,
    error_message: Optional[str] = None,
) -> Any:
    """
    Ultra-thin business logic - extract parameters and call service.
    
    Args:
        event: Lambda event wrapper
        service: ResourceMetaEntryService instance
        resource_id: The resource ID to look up
        error_message: Optional error message to return if not found
    
    Service handles:
    - Field validation
    - Access control (from service.request_context)
    - DynamoDB queries
    - Result filtering
    """
    
    key = event.query("key")
    
    # Service has RequestContext - just pass filter parameters
    kwargs = {
        "resource_id": resource_id,
        "key": key,
        "error_message": error_message,
    }
    return service.get_by_id(**kwargs)
