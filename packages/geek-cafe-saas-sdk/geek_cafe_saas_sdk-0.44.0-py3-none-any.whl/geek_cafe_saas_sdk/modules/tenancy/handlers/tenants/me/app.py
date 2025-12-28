"""
Lambda handler for retrieving the authenticated user's tenant.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.services import TenantService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=TenantService,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for retrieving the authenticated user's tenant.
    
    This is a convenience endpoint for /tenants/me to get the current user's tenant.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional TenantService for testing
    """
    return handler_wrapper.execute(event, context, get_my_tenant, injected_service)


def get_my_tenant(event: LambdaEvent, service: TenantService) -> ServiceResult:
    """
    Business logic for getting the authenticated user's tenant.
    
    Service already has request_context with tenant_id and user_id.
    """
    # Get tenant_id from the authenticated context
    tenant_id = service.request_context.authenticated_tenant_id
    
    return service.get_by_id(tenant_id=tenant_id)
