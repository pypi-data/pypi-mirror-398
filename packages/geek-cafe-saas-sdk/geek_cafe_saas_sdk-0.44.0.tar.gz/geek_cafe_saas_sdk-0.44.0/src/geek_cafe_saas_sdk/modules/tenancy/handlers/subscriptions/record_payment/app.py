"""
Lambda handler for recording a payment on a subscription.

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
    Lambda handler for recording a payment on a subscription.
    
    This updates the subscription with payment details and can change status from past_due to active.
    
    Expected body:
    {
        "amount_cents": 2999
    }
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional SubscriptionService for testing
    """
    return handler_wrapper.execute(event, context, record_payment, injected_service)


def record_payment(event: LambdaEvent, service: SubscriptionService) -> ServiceResult:
    """
    Business logic for recording a payment.
    
    Service already has request_context with tenant_id and user_id.
    """
    subscription_id = event.path("id", "subscriptionId")
    
    if not subscription_id:
        raise ValueError("Subscription ID is required in the path")
    
    amount_cents = event.body.get('amount_cents')
    if amount_cents is None:
        raise ValueError("Payment amount_cents is required")
    
    return service.record_payment(
        subscription_id=subscription_id,
        amount_cents=amount_cents
    )
