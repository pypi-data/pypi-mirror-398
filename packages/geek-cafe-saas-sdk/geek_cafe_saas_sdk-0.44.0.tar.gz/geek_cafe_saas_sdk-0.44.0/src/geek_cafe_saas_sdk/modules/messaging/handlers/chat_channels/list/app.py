"""
Lambda handler for listing chat channels.

Supports multiple query patterns:
- List by channel type (public, private, direct)
- List user's channels
- List default channels
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
    List chat channels based on query parameters.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ChatChannelService for testing
    
    Query parameters:
        channel_type: Filter by type (public, private, direct)
        user_channels: "true" to get only user's channels
        default: "true" to get only default channels
        include_archived: "true" to include archived channels
        limit: Maximum number of results (default 50)
    
    Examples:
        GET /chat-channels?channel_type=public
        GET /chat-channels?user_channels=true
        GET /chat-channels?default=true
    
    Returns 200 with list of chat channels
    """
    return handler_wrapper.execute(event, context, list_chat_channels, injected_service)


def list_chat_channels(event: LambdaEvent, service: ChatChannelService) -> ServiceResult:
    """
    Business logic for listing chat channels.
    
    Routes to different service methods based on query parameters.
    """
    query_params = event.get("queryStringParameters") or {}
    
    limit = int(query_params.get("limit", "100"))
    
    # Route to appropriate service method
    
    # Pattern 1: List default channels
    if query_params.get("default") == "true":
        return service.list_default_channels(limit=limit)
    
    # Pattern 2: List user's channels
    if query_params.get("user_channels") == "true":
        include_archived = query_params.get("include_archived") == "true"
        return service.list_user_channels(
            include_archived=include_archived,
            limit=limit
        )
    
    # Pattern 3: List by channel type
    if "channel_type" in query_params:
        channel_type = query_params.get("channel_type")
        return service.list_by_type(
            channel_type=channel_type,
            limit=limit
        )
    
    # Pattern 4: List all accessible channels (default)
    return service.list_all(limit=limit)
