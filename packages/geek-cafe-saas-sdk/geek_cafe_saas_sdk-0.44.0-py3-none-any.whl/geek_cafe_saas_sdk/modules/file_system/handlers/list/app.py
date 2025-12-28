"""
Lambda handler for listing files.

Ultra-thin handler - validation happens in service layer.

Requires authentication (secure mode).
"""
import os
from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.file_system.services import FileSystemService

DEFAULT_LIMIT = os.getenv("DEFAULT_LIMIT", 250)

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileSystemService,
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


def list_files(
    event: LambdaEvent,
    service: FileSystemService
) -> Any:
    """
    Ultra-thin business logic - extract parameters and call service.
    
    Service handles:
    - Field validation
    - Access control (from service.request_context)
    - DynamoDB queries
    - Result filtering
    """
    directory_id = event.query("directoryId")    
    limit = event.query_int("limit", default=DEFAULT_LIMIT)
    category = event.query("category")
    status = event.query("status")
    ascending = event.query_bool("ascending", default=False)
    
    # Service has RequestContext - just pass filter parameters
    if directory_id:
        return service.list_files_by_directory(
            directory_id=directory_id,
            limit=limit,
            ascending=ascending
        )
    else:
        kwargs = {
            "limit": limit,
            "category": category,
            "status": status,
            "ascending": ascending
        }

        return service.list_files_by_owner(**kwargs)
