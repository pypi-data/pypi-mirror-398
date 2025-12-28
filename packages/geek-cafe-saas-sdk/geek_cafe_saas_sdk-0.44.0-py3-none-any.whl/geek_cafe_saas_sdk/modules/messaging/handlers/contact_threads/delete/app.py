"""
Lambda handler for deleting (soft delete) contact threads.

Requires authentication and appropriate access permissions.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.messaging.services import ContactThreadService

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ContactThreadService,
    require_body=False
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Delete (soft delete) a contact thread.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ContactThreadService for testing
    
    Path parameters:
        id: Contact thread ID
    
    Returns 200 with success boolean
    """
    return handler_wrapper.execute(event, context, delete_contact_thread, injected_service)


def delete_contact_thread(event: LambdaEvent, service: ContactThreadService) -> ServiceResult:
    """
    Business logic for deleting a contact thread.
    
    Performs soft delete (sets deleted timestamp).
    """
    # Extract path parameter
    path_params = event.get("pathParameters") or {}
    thread_id = path_params.get("id")
    
    if not thread_id:
        from geek_cafe_saas_sdk.core.service_result import ServiceResult
        from geek_cafe_saas_sdk.core.service_errors import ValidationError
        return ServiceResult.exception_result(
            ValidationError("Thread ID is required in path")
        )
    
    # Delete the contact thread
    # Service uses request_context for tenant_id and user_id
    return service.delete(thread_id=thread_id)
