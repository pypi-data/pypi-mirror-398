"""
Lambda handler for deleting (soft delete) chat messages.

Requires authentication. Only message sender can delete.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.messaging.services import ChatMessageService

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ChatMessageService,
    require_body=False
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Delete (soft delete) a chat message.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ChatMessageService for testing
    
    Path parameters:
        id: Chat message ID
    
    Returns 200 with success boolean
    """
    return handler_wrapper.execute(event, context, delete_chat_message, injected_service)


def delete_chat_message(event: LambdaEvent, service: ChatMessageService) -> ServiceResult:
    """
    Business logic for deleting a chat message.
    
    Performs soft delete (sets deleted timestamp).
    Only message sender can delete.
    """
    # Extract path parameter
    path_params = event.get("pathParameters") or {}
    message_id = path_params.get("id")
    
    if not message_id:
        from geek_cafe_saas_sdk.core.service_result import ServiceResult
        from geek_cafe_saas_sdk.core.service_errors import ValidationError
        return ServiceResult.exception_result(
            ValidationError("Message ID is required in path")
        )
    
    user_id = user_context.get("user_id")
    tenant_id = user_context.get("tenant_id")
    
    # Delete the chat message
    return service.delete(
        message_id=message_id,
        tenant_id=tenant_id,
        user_id=user_id
    )
