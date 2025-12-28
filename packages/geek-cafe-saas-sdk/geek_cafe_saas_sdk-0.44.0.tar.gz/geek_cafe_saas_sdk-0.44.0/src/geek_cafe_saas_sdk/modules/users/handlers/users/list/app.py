# src/geek_cafe_saas_sdk/lambda_handlers/users/list/app.py

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
    Lambda handler for listing users in the tenant.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional UserService for testing
    
    Returns 200 with list of users
    """
    return handler_wrapper.execute(event, context, list_users_logic, injected_service)

def list_users_logic(
    event: LambdaEvent,
    service: UserService
) -> ServiceResult:
    """Business logic for listing users."""
    limit = event.query_int("limit", default=50)
    
    # Service now uses request_context internally
    result = service.get_users_by_tenant(limit=limit)
    
    return result
