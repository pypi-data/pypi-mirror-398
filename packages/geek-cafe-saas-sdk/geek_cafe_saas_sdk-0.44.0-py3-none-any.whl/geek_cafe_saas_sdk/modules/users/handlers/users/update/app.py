# src/geek_cafe_saas_sdk/lambda_handlers/users/update/app.py

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.users.services.user_service import UserService
from geek_cafe_saas_sdk.core.service_result import ServiceResult

# Create handler wrapper (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=UserService,
    convert_request_case=True
)

def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for updating an existing user.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional UserService for testing
    
    Returns 200 with updated user
    """
    return handler_wrapper.execute(event, context, update_user_logic, injected_service)

def update_user_logic(
    event: LambdaEvent,
    service: UserService
) -> ServiceResult:
    """Business logic for updating a user."""
    user_id = event.path("user-id")
    updates = event.body()
    
    # Service now uses request_context internally
    result = service.update(user_id=user_id, updates=updates)
    
    return result
