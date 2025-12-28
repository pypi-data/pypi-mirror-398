"""
Lambda handler for retrieving a subscription by ID.

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
    Lambda handler for retrieving a subscription by ID.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional SubscriptionService for testing
    """
    return handler_wrapper.execute(event, context, get_subscription, injected_service)


def get_subscription(event: LambdaEvent, service: SubscriptionService) -> ServiceResult:
    """
    Business logic for getting a subscription by ID.
    
    Service already has request_context with tenant_id and user_id.
    """
    subscription_id = event.path("id", "subscriptionId")
    
    if not subscription_id:
        raise ValueError("Subscription ID is required in the path")
    
    return service.get_by_id(subscription_id=subscription_id)
