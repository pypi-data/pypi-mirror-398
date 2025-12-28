"""
Lambda handler for tenant signup (creates tenant + primary admin user).

This is a public endpoint - no authentication required.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.services import TenantService


# Factory creates handler - signup is public (no auth required)
handler_wrapper = create_handler(
    service_class=TenantService,
    require_body=True,
    convert_request_case=True,
    auth_mode="public"  # No authentication required for signup
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for tenant signup (creates tenant + primary admin user).
    
    This is the initial signup endpoint that creates both a tenant and its first admin user.
    
    Expected body:
    {
        "user": {
            "email": "admin@company.com",
            "first_name": "John",
            "last_name": "Doe"
        },
        "tenant": {
            "name": "Company Name"
        }
    }
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional TenantService for testing
    """
    return handler_wrapper.execute(event, context, signup_tenant, injected_service)


def signup_tenant(event: LambdaEvent, service: TenantService) -> ServiceResult:
    """
    Business logic for tenant signup.
    """
    body = event.body
    
    user_payload = body.get('user', {})
    tenant_payload = body.get('tenant', {})
    
    if not user_payload:
        raise ValueError("User information is required")
    
    if not tenant_payload:
        raise ValueError("Tenant information is required")
    
    return service.create_with_user(
        user_payload=user_payload,
        tenant_payload=tenant_payload
    )
