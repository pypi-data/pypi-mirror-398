"""
Lambda handler for updating chat messages.

Supports multiple operations:
- Edit message content
- Add/remove reactions
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.messaging.services import ChatMessageService

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ChatMessageService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Update a chat message.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ChatMessageService for testing
    
    Path parameters:
        id: Chat message ID
    
    Expected body (camelCase from frontend):
    {
        "action": "update" | "add_reaction" | "remove_reaction",
        
        // For action="update":
        "content": "Updated message content",
        
        // For action="add_reaction":
        "emoji": "👍",
        
        // For action="remove_reaction":
        "emoji": "👍"
    }
    
    Returns 200 with updated chat message
    """
    return handler_wrapper.execute(event, context, update_chat_message, injected_service)


def update_chat_message(event: LambdaEvent, service: ChatMessageService) -> ServiceResult:
    """
    Business logic for updating chat messages.
    
    Routes to different service methods based on action parameter.
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
    
    payload = event.body()
    action = payload.get("action", "update")
    
    user_id = user_context.get("user_id")
    tenant_id = user_context.get("tenant_id")
    
    # Route to appropriate service method based on action
    
    if action == "add_reaction":
        # Add a reaction to the message
        emoji = payload.get("emoji")
        if not emoji:
            from geek_cafe_saas_sdk.core.service_result import ServiceResult
            from geek_cafe_saas_sdk.core.service_errors import ValidationError
            return ServiceResult.exception_result(
                ValidationError("emoji is required for add_reaction action")
            )
        
        return service.add_reaction(
            message_id=message_id,
            tenant_id=tenant_id,
            user_id=user_id,
            emoji=emoji
        )
    
    elif action == "remove_reaction":
        # Remove a reaction from the message
        emoji = payload.get("emoji")
        if not emoji:
            from geek_cafe_saas_sdk.core.service_result import ServiceResult
            from geek_cafe_saas_sdk.core.service_errors import ValidationError
            return ServiceResult.exception_result(
                ValidationError("emoji is required for remove_reaction action")
            )
        
        return service.remove_reaction(
            message_id=message_id,
            tenant_id=tenant_id,
            user_id=user_id,
            emoji=emoji
        )
    
    else:
        # Edit message content (only sender can edit)
        updates = {}
        
        if "content" in payload:
            updates["content"] = payload["content"]
        
        return service.update(
            message_id=message_id,
            tenant_id=tenant_id,
            user_id=user_id,
            updates=updates
        )
