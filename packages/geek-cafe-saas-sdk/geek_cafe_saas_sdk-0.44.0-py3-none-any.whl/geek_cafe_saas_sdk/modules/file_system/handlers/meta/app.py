"""
Lambda handler for file metadata.

Ultra-thin handler - validation happens in service layer.
Reuses core resource_meta handler with file-specific path parameters.

Requires authentication (secure mode).
"""
from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.handlers.resource_meta.app import get_metadata
from geek_cafe_saas_sdk.core.services.resource_meta_entry_service import ResourceMetaEntryService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ResourceMetaEntryService,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Get file metadata.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional service for testing
    
    Path parameters:
        fileId or file-id: The file ID
    
    Query parameters:
        key: Metadata key (optional)
    
    Returns 200 with file metadata
    """
    return handler_wrapper.execute(event, context, get_file_metadata, injected_service)


def get_file_metadata(
    event: LambdaEvent,
    service: ResourceMetaEntryService
) -> Any:
    """
    Get file metadata - delegates to core get_metadata with file-specific params.
    """

    resource_id = event.path("fileId") or event.path("file-id")
    key = event.query("key")
    return get_metadata(
        event=event,
        service=service,
        resource_id=resource_id,
        error_message = f"Extended Metadata key {key} for File Id of {resource_id} not found"
    )
