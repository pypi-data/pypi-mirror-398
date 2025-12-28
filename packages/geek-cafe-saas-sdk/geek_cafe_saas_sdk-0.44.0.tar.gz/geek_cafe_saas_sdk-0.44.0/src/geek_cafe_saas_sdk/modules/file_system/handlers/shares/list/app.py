"""
Lambda handler for listing file shares.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.file_system.services.file_share_service import FileShareService
from geek_cafe_saas_sdk.core.service_result import ServiceResult


# Create handler wrapper (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileShareService,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    List file shares - either for a specific file or shared with current user.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileShareService for testing
    
    Query parameters (camelCase from frontend):
    - fileId: (optional) If provided, lists shares for this file
    - limit: (optional) Maximum results, defaults to 50
    
    If fileId is provided: lists shares for that file (owner only)
    If fileId is omitted: lists files shared with current user
    
    Returns 200 with list of shares
    """
    return handler_wrapper.execute(event, context, list_shares_logic, injected_service)


def list_shares_logic(
    event: LambdaEvent,
    service: FileShareService
) -> ServiceResult:
    """Business logic for listing shares."""
    file_id = event.query("file_id")
    limit = event.query_int("limit", default=50)
    
    if file_id:
        # List shares for a specific file (owner only)
        result = service.list_shares_by_file(
            file_id=file_id,
            limit=limit
        )
    else:
        # List files shared with current user
        result = service.list_shared_with_me(
            limit=limit
        )
    
    return result
