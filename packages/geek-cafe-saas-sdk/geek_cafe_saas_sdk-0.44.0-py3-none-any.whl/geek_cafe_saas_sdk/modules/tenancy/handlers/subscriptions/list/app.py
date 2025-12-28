"""
Lambda handler for listing subscription history for a tenant.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.services import SubscriptionService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=SubscriptionService,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for listing subscription history for a tenant.
    
    Returns all subscriptions (current and past) sorted by date descending.
    
    Query parameters:
    - limit: Maximum number of results (default: 50)
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional SubscriptionService for testing
    """
    return handler_wrapper.execute(event, context, list_subscriptions, injected_service)


def list_subscriptions(event: LambdaEvent, service: SubscriptionService) -> ServiceResult:
    """
    Business logic for listing subscription history.
    
    Service already has request_context with tenant_id and user_id.
    """
    limit = int(event.query("limit") or 50)
    
    return service.list_subscription_history(limit=limit)
