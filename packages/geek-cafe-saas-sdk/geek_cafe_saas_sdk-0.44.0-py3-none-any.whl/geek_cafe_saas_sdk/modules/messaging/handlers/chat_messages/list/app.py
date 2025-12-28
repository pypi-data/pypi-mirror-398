"""
Lambda handler for listing chat messages.

Supports multiple query patterns:
- List messages in a channel (with pagination)
- List threaded replies to a message
- List user's message history
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.messaging.services import ChatMessageService

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ChatMessageService,
    require_body=False
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    List chat messages based on query parameters.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ChatMessageService for testing
    
    Query parameters:
        channel_id: Channel ID to list messages from
        parent_message_id: Parent message ID to list thread replies
        sender_id: User ID to list message history
        limit: Maximum number of results (default 50)
        ascending: "true" for oldest first, "false" for newest first
    
    Examples:
        GET /chat-messages?channel_id=channel_123&limit=50
        GET /chat-messages?parent_message_id=msg_123
        GET /chat-messages?sender_id=user_123
    
    Returns 200 with list of chat messages
    """
    return handler_wrapper.execute(event, context, list_chat_messages, injected_service)


def list_chat_messages(event: LambdaEvent, service: ChatMessageService) -> ServiceResult:
    """
    Business logic for listing chat messages.
    
    Routes to different service methods based on query parameters.
    """
    query_params = event.get("queryStringParameters") or {}
    
    limit = int(query_params.get("limit", "50"))
    ascending = query_params.get("ascending", "true") == "true"
    
    # Route to appropriate service method
    
    # Pattern 1: List threaded replies to a parent message
    if "parent_message_id" in query_params:
        parent_message_id = query_params.get("parent_message_id")
        return service.list_thread_replies(
            parent_message_id=parent_message_id,
            limit=limit
        )
    
    # Pattern 2: List user's message history
    if "sender_id" in query_params:
        sender_id = query_params.get("sender_id")
        return service.list_by_sender(
            sender_id=sender_id,
            limit=limit
        )
    
    # Pattern 3: List messages in a channel (default, most common)
    if "channel_id" in query_params:
        channel_id = query_params.get("channel_id")
        return service.list_by_channel(
            channel_id=channel_id,
            limit=limit,
            ascending=ascending
        )
    
    # No valid query parameters
    from geek_cafe_saas_sdk.core.service_result import ServiceResult
    from geek_cafe_saas_sdk.core.service_errors import ValidationError
    return ServiceResult.exception_result(
        ValidationError("Must provide channel_id, parent_message_id, or sender_id")
    )
