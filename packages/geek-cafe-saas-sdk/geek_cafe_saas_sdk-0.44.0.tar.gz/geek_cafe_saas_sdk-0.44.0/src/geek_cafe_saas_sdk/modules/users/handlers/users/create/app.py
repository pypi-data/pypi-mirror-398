# src/geek_cafe_saas_sdk/lambda_handlers/users/create/app.py

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
    Lambda handler for creating a new user.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional UserService for testing
    
    Returns 201 with created user
    """
    return handler_wrapper.execute(event, context, create_user_logic, injected_service)

def create_user_logic(
    event: LambdaEvent,
    service: UserService
) -> ServiceResult:
    """Business logic for creating a user."""
    # Get all body parameters
    body = event.body()
    
    # Service now uses request_context internally
    result = service.create(**body)
    
    return result
