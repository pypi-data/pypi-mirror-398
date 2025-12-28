"""
Lambda handler for creating chat channels.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.messaging.services import ChatChannelService

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ChatChannelService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Create a new chat channel.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ChatChannelService for testing
    
    Expected body (camelCase from frontend):
    {
        "name": "general",
        "description": "General discussion",
        "channelType": "public" | "private" | "direct",
        "ownerId": "user_456",  # Optional: For admins creating channels for others
        "members": ["user_123", "user_456"],
        "topic": "Channel topic",
        "isDefault": false,
        "isAnnouncement": false
    }
    
    Note: 
    - ownerId: Who the channel belongs to (defaults to authenticated user)
    - createdBy: Always set to authenticated user (audit trail)
    
    Returns 201 with created chat channel
    """
    return handler_wrapper.execute(event, context, create_chat_channel, injected_service)


def create_chat_channel(
    event: LambdaEvent,
    service: ChatChannelService
) -> ServiceResult:
    """
    Business logic for creating chat channels.
    
    Owner is automatically added as a member.
    Supports admin scenario (Rule #1):
    - ownerId in payload: who the channel belongs to
    - createdById: authenticated admin (for audit trail - Rule #2)
    
    Owner validation (Rule #3):
    - Missing ownerId: defaults to authenticated user (self-service)
    - Present ownerId: uses specified owner (admin-on-behalf)
    - Empty ownerId: ERROR (fail fast)
    """
    payload = event.body()
    
    # Get authenticated user from request context
    authenticated_user_id = service.request_context.authenticated_user_id
    
    # Validate and resolve owner (Rule #3)
    # Will raise ValidationError if explicitly empty
    owner_user_id = service._validate_owner_field(payload, authenticated_user_id, "owner_id")
    
    # Set audit trail to authenticated user (Rule #2)
    payload["created_by_id"] = authenticated_user_id
    
    # Set the resource owner in payload
    payload["user_id"] = owner_user_id
    
    # Create the chat channel
    # Service will use request_context for authentication
    result = service.create(payload=payload)
    
    return result
