"""
Lambda handler for creating discounts.

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
    Create a new discount/promo code.
    
    Expected body:
    {
        "discountCode": "SUMMER25",
        "discountName": "Summer Sale",
        "discountType": "percentage",
        "percentOff": 25.0,
        "duration": "repeating",
        "durationInMonths": 3,
        "maxRedemptions": 100
    }
    
    Returns 201 with created discount
    """
    return handler_wrapper.execute(event, context, create_discount, injected_service)


def create_discount(event: LambdaEvent, service: SubscriptionManagerService) -> ServiceResult:
    """
    Business logic for creating a discount.
    """
    payload = event.body()
    
    # Extract required fields
    discount_code = payload.get("discount_code")
    if not discount_code:
        raise ValueError("discount_code is required")
    
    discount_name = payload.get("discount_name")
    if not discount_name:
        raise ValueError("discount_name is required")
    
    discount_type = payload.get("discount_type", "percentage")
    
    # Build kwargs for optional fields
    kwargs = {}
    optional_fields = [
        "description", "amount_off_cents", "percent_off", "trial_extension_days",
        "currency", "duration", "duration_in_months",
        "valid_from_utc_ts", "valid_until_utc_ts",
        "max_redemptions", "max_redemptions_per_customer",
        "status", "minimum_amount_cents",
        "applies_to_plan_codes", "applies_to_addon_codes", "applies_to_intervals",
        "first_time_transaction", "campaign_name", "source", "notes"
    ]
    
    for field in optional_fields:
        if field in payload:
            kwargs[field] = payload[field]
    
    result = service.create_discount(
        discount_code=discount_code,
        discount_name=discount_name,
        discount_type=discount_type,
        **kwargs
    )
    
    return result
