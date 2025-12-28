"""
Lambda handler for retrieving a tenant by ID.

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
    Lambda handler for retrieving a tenant by ID.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional TenantService for testing
    """
    return handler_wrapper.execute(event, context, get_tenant, injected_service)


def get_tenant(event: LambdaEvent, service: TenantService) -> ServiceResult:
    """
    Business logic for getting a tenant by ID.
    
    Service already has request_context with tenant_id and user_id.
    """
    tenant_id = event.path("id", "tenantId")
    
    if not tenant_id:
        raise ValueError("Tenant ID is required in the path")
    
    return service.get_by_id(tenant_id=tenant_id)
