"""
Lambda handler for creating subscription plans.

Admin endpoint - requires authentication.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.subscriptions.services import SubscriptionManagerService


handler_wrapper = create_handler(
    service_class=SubscriptionManagerService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Create a new subscription plan.
    
    Expected body:
    {
        "planCode": "pro",
        "planName": "Pro Plan",
        "priceMonthlyC ents": 2999,
        "description": "For growing teams",
        "features": {"api_access": true, "sso": false},
        "limits": {"max_projects": 100, "max_storage_gb": 500}
    }
    
    Returns 201 with created plan
    """
    return handler_wrapper.execute(event, context, create_plan, injected_service)


def create_plan(event: LambdaEvent, service: SubscriptionManagerService) -> ServiceResult:
    """
    Business logic for creating a plan.
    """
    payload = event.body()
    
    # Extract required fields
    plan_code = payload.get("plan_code")
    if not plan_code:
        raise ValueError("plan_code is required")
    
    plan_name = payload.get("plan_name")
    if not plan_name:
        raise ValueError("plan_name is required")
    
    price_monthly_cents = payload.get("price_monthly_cents", 0)
    
    # Build kwargs for optional fields
    kwargs = {}
    optional_fields = [
        "description", "tagline", "status", "is_public", "is_featured", "sort_order",
        "price_annual_cents", "price_monthly_currency", "price_annual_currency",
        "annual_discount_percentage", "trial_days", "trial_requires_payment_method",
        "min_seats", "max_seats", "price_per_additional_seat_cents",
        "features", "limits", "included_addon_ids", "compatible_addon_ids",
        "feature_list", "cta_text", "recommended",
        "allow_downgrades", "allow_upgrades"
    ]
    
    for field in optional_fields:
        if field in payload:
            kwargs[field] = payload[field]
    
    result = service.create_plan(
        plan_code=plan_code,
        plan_name=plan_name,
        price_monthly_cents=price_monthly_cents,
        **kwargs
    )
    
    return result
