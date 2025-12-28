"""
Lambda handler for updating contact threads.

Supports multiple update operations:
- Update general fields (subject, priority, tags, etc.)
- Add messages to thread
- Assign to staff member
- Update status
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.messaging.services import ContactThreadService

# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=ContactThreadService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Update a contact thread.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ContactThreadService for testing
    
    Path parameters:
        id: Contact thread ID
    
    Expected body (camelCase from frontend):
    {
        "action": "update" | "add_message" | "assign" | "update_status",
        
        // For action="update":
        "subject": "Updated subject",
        "priority": "urgent",
        "tags": ["bug", "urgent"],
        
        // For action="add_message":
        "message": {
            "content": "Reply message",
            "senderName": "Support Staff",
            "isStaffReply": true
        },
        
        // For action="assign":
        "assignedTo": "staff_user_id",
        
        // For action="update_status":
        "status": "resolved"
    }
    
    Returns 200 with updated contact thread
    """
    return handler_wrapper.execute(event, context, update_contact_thread, injected_service)


def update_contact_thread(event: LambdaEvent, service: ContactThreadService) -> ServiceResult:
    """
    Business logic for updating contact threads.
    
    Routes to different service methods based on action parameter.
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
    
    payload = event.body()
    action = payload.get("action", "update")
    
    # Route to appropriate service method based on action
    # Service uses request_context for tenant_id and user_id
    
    if action == "add_message":
        # Add a message to the thread
        message_data = payload.get("message", {})
        return service.add_message(
            thread_id=thread_id,
            message_data=message_data
        )
    
    elif action == "assign":
        # Assign thread to a staff member
        assigned_to = payload.get("assigned_to")
        if not assigned_to:
            from geek_cafe_saas_sdk.core.service_result import ServiceResult
            from geek_cafe_saas_sdk.core.service_errors import ValidationError
            return ServiceResult.exception_result(
                ValidationError("assigned_to is required for assign action")
            )
        
        return service.assign_thread(
            thread_id=thread_id,
            assigned_to=assigned_to
        )
    
    elif action == "update_status":
        # Update thread status
        status = payload.get("status")
        if not status:
            from geek_cafe_saas_sdk.core.service_result import ServiceResult
            from geek_cafe_saas_sdk.core.service_errors import ValidationError
            return ServiceResult.exception_result(
                ValidationError("status is required for update_status action")
            )
        
        return service.update_status(
            thread_id=thread_id,
            status=status
        )
    
    else:
        # General update (update multiple fields)
        # Extract allowed fields
        updates = {}
        allowed_fields = ['subject', 'status', 'priority', 'assigned_to', 'tags', 'inbox_id']
        
        for field in allowed_fields:
            if field in payload:
                updates[field] = payload[field]
        
        return service.update(
            thread_id=thread_id,
            updates=updates
        )
