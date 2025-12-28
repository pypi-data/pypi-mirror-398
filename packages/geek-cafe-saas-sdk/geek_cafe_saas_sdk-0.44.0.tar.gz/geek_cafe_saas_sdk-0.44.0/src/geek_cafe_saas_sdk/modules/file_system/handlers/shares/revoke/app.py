"""
Lambda handler for revoking file shares.

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
    Revoke a file share.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileShareService for testing
    
    Path parameters:
    - shareId: ID of share to revoke
    
    Query parameters (camelCase from frontend):
    - fileId: File ID (required for validation)
    
    Returns 200 on success
    """
    return handler_wrapper.execute(event, context, revoke_share_logic, injected_service)


def revoke_share_logic(
    event: LambdaEvent,
    service: FileShareService
) -> ServiceResult:
    """Business logic for revoking shares."""
    share_id = event.path("share_id")
    file_id = event.query("file_id")
    
    # Service now uses request_context internally
    result = service.delete(
        share_id=share_id,
        file_id=file_id
    )
    
    return result
