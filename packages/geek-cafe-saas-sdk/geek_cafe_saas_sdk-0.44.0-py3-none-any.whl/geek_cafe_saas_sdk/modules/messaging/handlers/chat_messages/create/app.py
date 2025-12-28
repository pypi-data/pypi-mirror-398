"""
Lambda handler for creating chat messages.

Requires authentication.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.messaging.services import ChatMessageService

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ChatMessageService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Create a new chat message.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ChatMessageService for testing
    
    Expected body (camelCase from frontend):
    {
        "channelId": "channel_123",
        "content": "Hello world!",
        "senderName": "User Name",
        "parentMessageId": "msg_parent_123" (optional for threaded replies),
        "mentions": ["user_456", "user_789"],
        "attachments": [
            {"type": "image", "url": "https://..."}
        ]
    }
    
    Returns 201 with created chat message
    """
    return handler_wrapper.execute(event, context, create_chat_message, injected_service)


def create_chat_message(
    event: LambdaEvent,
    service: ChatMessageService
) -> ServiceResult:
    """
    Business logic for creating chat messages.
    
    Validates channel membership before creating message.
    """
    payload = event.body()
    
    # Service now uses request_context internally
    result = service.create(payload=payload)
    
    return result
