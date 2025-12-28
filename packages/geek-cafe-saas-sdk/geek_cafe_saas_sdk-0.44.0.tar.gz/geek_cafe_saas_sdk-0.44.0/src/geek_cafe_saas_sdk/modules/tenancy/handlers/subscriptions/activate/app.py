"""
Lambda handler for activating a subscription (upgrade/downgrade).

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.services import SubscriptionService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=SubscriptionService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for activating a subscription (upgrade/downgrade).
    
    This creates a new subscription and sets it as the tenant's active subscription.
    Updates the tenant's plan_tier automatically.
    
    Expected body:
    {
        "plan_code": "pro_monthly",
        "plan_name": "Pro Plan",
        "price_cents": 2999,
        "seat_count": 10,
        "current_period_start_utc_ts": 1729123200.0,
        "current_period_end_utc_ts": 1731801600.0
    }
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional SubscriptionService for testing
    """
    return handler_wrapper.execute(event, context, activate_subscription, injected_service)


def activate_subscription(event: LambdaEvent, service: SubscriptionService) -> ServiceResult:
    """
    Business logic for activating a subscription.
    
    Service already has request_context with tenant_id and user_id.
    """
    return service.activate_subscription(payload=event.body)
