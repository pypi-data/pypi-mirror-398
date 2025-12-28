"""
Lambda handler for aggregating usage.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.subscriptions.services import SubscriptionManagerService


handler_wrapper = create_handler(
    service_class=SubscriptionManagerService,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Get aggregated usage for a billing period.
    
    Query parameters:
    - subscriptionId: Subscription ID (required)
    - addonCode: Addon code (required)
    - periodStart: Period start timestamp (required)
    - periodEnd: Period end timestamp (required)
    
    Returns 200 with aggregated usage total
    """
    return handler_wrapper.execute(event, context, aggregate_usage, injected_service)


def aggregate_usage(event: LambdaEvent, service: SubscriptionManagerService) -> ServiceResult:
    """
    Business logic for aggregating usage.
    """
    params = event.get("queryStringParameters") or {}
    
    tenant_id = user_context.get("tenant_id")
    
    subscription_id = params.get("subscription_id")
    if not subscription_id:
        raise ValueError("subscription_id is required")
    
    addon_code = params.get("addon_code")
    if not addon_code:
        raise ValueError("addon_code is required")
    
    period_start = params.get("period_start")
    if not period_start:
        raise ValueError("period_start is required")
    period_start = float(period_start)
    
    period_end = params.get("period_end")
    if not period_end:
        raise ValueError("period_end is required")
    period_end = float(period_end)
    
    result = service.aggregate_usage(
        tenant_id=tenant_id,
        subscription_id=subscription_id,
        addon_code=addon_code,
        period_start=period_start,
        period_end=period_end
    )
    
    return result
