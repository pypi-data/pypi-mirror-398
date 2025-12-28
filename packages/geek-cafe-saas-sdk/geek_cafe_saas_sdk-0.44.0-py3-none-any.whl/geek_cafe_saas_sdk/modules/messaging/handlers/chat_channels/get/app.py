"""
Lambda handler for getting a chat channel by ID.

Requires authentication.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.messaging.services import ChatChannelService

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ChatChannelService,
    require_body=False
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Get a chat channel by ID.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ChatChannelService for testing
    
    Path parameters:
        id: Chat channel ID
    
    Returns 200 with chat channel details
    """
    return handler_wrapper.execute(event, context, get_chat_channel, injected_service)


def get_chat_channel(event: LambdaEvent, service: ChatChannelService) -> ServiceResult:
    """
    Business logic for getting a chat channel.
    
    Access control: public channels visible to all, private channels only to members.
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
    
    # Get the chat channel with access control
    return service.get_by_id(channel_id=channel_id)
