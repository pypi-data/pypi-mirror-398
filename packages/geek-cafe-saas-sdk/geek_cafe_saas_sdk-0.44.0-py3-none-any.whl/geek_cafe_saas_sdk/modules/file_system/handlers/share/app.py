"""
Lambda handler for sharing files.

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
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Share a file with another user.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileShareService for testing
    
    Expected body (camelCase from frontend):
    {
        "fileId": "file-123",
        "sharedWithUserId": "user-456",
        "permission": "view",  // Optional: view, download, edit
        "expiresAt": 1234567890,  // Optional: Unix timestamp
        "message": "Check this out!"  // Optional
    }
    
    Returns 201 with share details
    """
    return handler_wrapper.execute(event, context, share_file_logic, injected_service)


def share_file_logic(
    event: LambdaEvent,
    service: FileShareService
) -> ServiceResult:
    """Business logic for sharing files."""
    payload = event.body()
    
    # Service now uses request_context internally, so no tenant_id/user_id needed
    result = service.create(
        file_id=payload["file_id"],
        shared_with_user_id=payload["shared_with_user_id"],
        permission=payload.get("permission", "view"),
        expires_at=payload.get("expires_at"),
        message=payload.get("message")
    )
    
    return result
