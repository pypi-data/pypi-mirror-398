"""
Lambda handler for updating chat channels.

Supports multiple operations:
- Update channel properties
- Add/remove members
- Archive/unarchive
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.messaging.services import ChatChannelService

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ChatChannelService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Update a chat channel.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ChatChannelService for testing
    
    Path parameters:
        id: Chat channel ID
    
    Expected body (camelCase from frontend):
    {
        "action": "update" | "add_member" | "remove_member" | "archive" | "unarchive",
        
        // For action="update":
        "name": "Updated Name",
        "description": "Updated description",
        "topic": "New topic",
        "isAnnouncement": true,
        
        // For action="add_member":
        "memberId": "user_456",
        
        // For action="remove_member":
        "memberId": "user_456"
    }
    
    Returns 200 with updated chat channel
    """
    return handler_wrapper.execute(event, context, update_chat_channel, injected_service)


def update_chat_channel(event: LambdaEvent, service: ChatChannelService) -> ServiceResult:
    """
    Business logic for updating chat channels.
    
    Routes to different service methods based on action parameter.
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
    
    payload = event.body()
    action = payload.get("action", "update")
    
    user_id = user_context.get("user_id")
    tenant_id = user_context.get("tenant_id")
    
    # Route to appropriate service method based on action
    
    if action == "add_member":
        # Add a member to the channel
        member_id = payload.get("member_id")
        if not member_id:
            from geek_cafe_saas_sdk.core.service_result import ServiceResult
            from geek_cafe_saas_sdk.core.service_errors import ValidationError
            return ServiceResult.exception_result(
                ValidationError("member_id is required for add_member action")
            )
        
        return service.add_member(
            channel_id=channel_id,
            tenant_id=tenant_id,
            user_id=user_id,
            member_to_add=member_id
        )
    
    elif action == "remove_member":
        # Remove a member from the channel
        member_id = payload.get("member_id")
        if not member_id:
            from geek_cafe_saas_sdk.core.service_result import ServiceResult
            from geek_cafe_saas_sdk.core.service_errors import ValidationError
            return ServiceResult.exception_result(
                ValidationError("member_id is required for remove_member action")
            )
        
        return service.remove_member(
            channel_id=channel_id,
            tenant_id=tenant_id,
            user_id=user_id,
            member_to_remove=member_id
        )
    
    elif action == "archive":
        # Archive the channel
        return service.archive(
            channel_id=channel_id,
            tenant_id=tenant_id,
            user_id=user_id
        )
    
    elif action == "unarchive":
        # Unarchive the channel
        return service.unarchive(
            channel_id=channel_id,
            tenant_id=tenant_id,
            user_id=user_id
        )
    
    else:
        # General update (update channel properties)
        updates = {}
        allowed_fields = ['name', 'description', 'topic', 'icon', 'is_announcement', 'is_default']
        
        for field in allowed_fields:
            if field in payload:
                updates[field] = payload[field]
        
        return service.update(
            channel_id=channel_id,
            tenant_id=tenant_id,
            user_id=user_id,
            updates=updates
        )
