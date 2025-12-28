"""
Lambda handler for deleting (soft delete) chat channels.

Requires authentication and channel creator permissions.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.messaging.services import ChatChannelService

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ChatChannelService,
    require_body=False
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Delete (soft delete) a chat channel.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ChatChannelService for testing
    
    Path parameters:
        id: Chat channel ID
    
    Returns 200 with success boolean
    """
    return handler_wrapper.execute(event, context, delete_chat_channel, injected_service)


def delete_chat_channel(event: LambdaEvent, service: ChatChannelService) -> ServiceResult:
    """
    Business logic for deleting a chat channel.
    
    Performs soft delete (sets deleted timestamp).
    Only channel creator can delete.
    """
    # Extract path parameter
    path_params = event.get("pathParameters") or {}
    channel_id = path_params.get("id")
    
    if not channel_id:
        from geek_cafe_saas_sdk.core.service_result import ServiceResult
        from geek_cafe_saas_sdk.core.service_errors import ValidationError
        return ServiceResult.exception_result(
            ValidationError("Channel ID is required in path")
        )
    
    user_id = user_context.get("user_id")
    tenant_id = user_context.get("tenant_id")
    
    # Delete the chat channel
    return service.delete(
        channel_id=channel_id,
        tenant_id=tenant_id,
        user_id=user_id
    )
