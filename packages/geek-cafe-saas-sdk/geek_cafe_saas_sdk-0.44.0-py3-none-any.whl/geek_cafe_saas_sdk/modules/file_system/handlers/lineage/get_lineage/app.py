"""
Lambda handler for getting file lineage.

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
    Get complete lineage for a file.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Path parameters:
        fileId: File ID
    
    Returns 200 with lineage information:
    {
        "selected": {file object},
        "main": {file object or null},
        "original": {file object or null},
        "allDerived": [{file objects}]  # If viewing main file
    }
    """
    return handler_wrapper.execute(event, context, get_file_lineage, injected_service)


def get_file_lineage(event: LambdaEvent, service: FileSystemService) -> ServiceResult:
    """
    Business logic for getting file lineage.
    
    Service already has request_context with tenant_id and user_id,
    so we just need to extract the file_id and call the service.
    """
    # Get file ID from path parameters
    file_id = event.path("file-id", "fileId", "id")
    
    if not file_id:
        raise ValueError("fileId path parameter is required")
    
    query_type = event.query("type")

    if query_type == "parent":    
        result = service.list_lineage(parent_id=file_id)
    else:
        result = service.list_lineage(root_id=file_id)
    
    return result
