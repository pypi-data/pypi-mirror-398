"""
Lambda handler for recording usage events.

Requires authentication (secure mode).
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
    Record a usage event for metered billing.
    
    Expected body:
    {
        "subscriptionId": "sub-123",
        "addonCode": "extra_storage",
        "meterEventName": "storage_gb",
        "quantity": 50.5,
        "action": "increment",  // optional: increment, decrement, set
        "idempotencyKey": "unique-key",  // optional
        "metadata": {}  // optional
    }
    
    Returns 201 with usage record
    """
    return handler_wrapper.execute(event, context, record_usage, injected_service)


def record_usage(event: LambdaEvent, service: SubscriptionManagerService) -> ServiceResult:
    """
    Business logic for recording usage.
    """
    payload = event.body()
    
    tenant_id = user_context.get("tenant_id")
    
    # Extract required fields
    subscription_id = payload.get("subscription_id")
    if not subscription_id:
        raise ValueError("subscription_id is required")
    
    addon_code = payload.get("addon_code")
    if not addon_code:
        raise ValueError("addon_code is required")
    
    meter_event_name = payload.get("meter_event_name")
    if not meter_event_name:
        raise ValueError("meter_event_name is required")
    
    quantity = payload.get("quantity")
    if quantity is None:
        raise ValueError("quantity is required")
    
    # Build kwargs for optional fields
    kwargs = {}
    optional_fields = [
        "action", "unit_name", "idempotency_key",
        "billing_period_start_utc_ts", "billing_period_end_utc_ts",
        "metadata", "source", "description"
    ]
    
    for field in optional_fields:
        if field in payload:
            kwargs[field] = payload[field]
    
    result = service.record_usage(
        tenant_id=tenant_id,
        subscription_id=subscription_id,
        addon_code=addon_code,
        meter_event_name=meter_event_name,
        quantity=quantity,
        **kwargs
    )
    
    return result
