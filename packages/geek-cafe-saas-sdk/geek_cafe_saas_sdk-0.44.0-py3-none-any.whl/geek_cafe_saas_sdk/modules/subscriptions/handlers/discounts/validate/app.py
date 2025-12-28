"""
Lambda handler for validating discount codes.

Public endpoint - no authentication required.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.subscriptions.services import SubscriptionManagerService


handler_wrapper = create_handler(
    service_class=SubscriptionManagerService,
    require_auth=False,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Validate a discount code.
    
    Expected body:
    {
        "discountCode": "SUMMER25",
        "planCode": "pro",  // optional
        "amountCents": 2999,  // optional
        "isFirstPurchase": false  // optional
    }
    
    Returns 200 with discount details if valid
    """
    return handler_wrapper.execute(event, context, validate_discount, injected_service)


def validate_discount(event: LambdaEvent, service: SubscriptionManagerService) -> ServiceResult:
    """
    Business logic for validating a discount.
    """
    payload = event.body()
    
    discount_code = payload.get("discount_code")
    if not discount_code:
        raise ValueError("discount_code is required")
    
    plan_code = payload.get("plan_code")
    amount_cents = payload.get("amount_cents")
    is_first_purchase = payload.get("is_first_purchase", False)
    
    result = service.validate_discount(
        discount_code=discount_code,
        plan_code=plan_code,
        amount_cents=amount_cents,
        is_first_purchase=is_first_purchase
    )
    
    return result
