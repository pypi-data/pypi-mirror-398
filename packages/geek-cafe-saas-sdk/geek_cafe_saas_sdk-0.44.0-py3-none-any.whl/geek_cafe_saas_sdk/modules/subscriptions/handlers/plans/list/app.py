"""
Lambda handler for listing subscription plans.

Public endpoint - no authentication required for public plans.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.subscriptions.services import SubscriptionManagerService


# Public endpoint - no auth required
handler_wrapper = create_handler(
    service_class=SubscriptionManagerService,
    require_auth=False,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    List public subscription plans.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional SubscriptionManagerService for testing
    
    Query parameters:
    - status: Filter by status (default: "active")
    - isPublic: Filter by public visibility (default: true)
    - limit: Max results (default: 50)
    
    Returns 200 with list of plans
    """
    return handler_wrapper.execute(event, context, list_plans, injected_service)


def list_plans(event: LambdaEvent, service: SubscriptionManagerService) -> ServiceResult:
    """
    Business logic for listing plans.
    """
    params = event.get("queryStringParameters") or {}
    
    status = params.get("status", "active")
    is_public = params.get("is_public")
    limit = int(params.get("limit", "50"))
    
    # Convert string to bool if provided
    if is_public is not None:
        is_public = is_public.lower() in ["true", "1", "yes"]
    else:
        is_public = True  # Default to public plans only
    
    result = service.list_plans(
        status=status,
        is_public=is_public,
        limit=limit
    )
    
    return result
