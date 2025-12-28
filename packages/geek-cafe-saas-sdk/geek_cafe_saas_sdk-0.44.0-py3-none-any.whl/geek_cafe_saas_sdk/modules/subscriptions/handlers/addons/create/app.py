"""
Lambda handler for creating addons.

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
    Create a new addon.
    
    Expected body:
    {
        "addonCode": "chat",
        "addonName": "Chat Module",
        "pricingModel": "fixed",
        "priceMonthly Cents": 1500,
        "description": "Real-time chat for your app",
        "category": "communication"
    }
    
    Returns 201 with created addon
    """
    return handler_wrapper.execute(event, context, create_addon, injected_service)


def create_addon(event: LambdaEvent, service: SubscriptionManagerService) -> ServiceResult:
    """
    Business logic for creating an addon.
    """
    payload = event.body()
    
    # Extract required fields
    addon_code = payload.get("addon_code")
    if not addon_code:
        raise ValueError("addon_code is required")
    
    addon_name = payload.get("addon_name")
    if not addon_name:
        raise ValueError("addon_name is required")
    
    pricing_model = payload.get("pricing_model", "fixed")
    
    # Build kwargs for optional fields
    kwargs = {}
    optional_fields = [
        "description", "category", "status", "is_public", "sort_order",
        "price_monthly_cents", "price_annual_cents", "currency",
        "price_per_unit_cents", "unit_name", "included_units", "min_units", "max_units",
        "pricing_tiers", "trial_days", "features", "limits",
        "compatible_plan_codes", "incompatible_addon_codes", "feature_list",
        "icon", "color", "is_metered", "meter_event_name", "billing_scheme"
    ]
    
    for field in optional_fields:
        if field in payload:
            kwargs[field] = payload[field]
    
    result = service.create_addon(
        addon_code=addon_code,
        addon_name=addon_name,
        pricing_model=pricing_model,
        **kwargs
    )
    
    return result
