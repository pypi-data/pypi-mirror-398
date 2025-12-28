"""
Lambda handler for updating addons.

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
    Update an addon.
    
    Path parameters:
    - addonId: Addon ID
    
    Body contains fields to update
    
    Returns 200 with updated addon
    """
    return handler_wrapper.execute(event, context, update_addon, injected_service)


def update_addon(event: LambdaEvent, service: SubscriptionManagerService) -> ServiceResult:
    """
    Business logic for updating an addon.
    """
    path_params = event.get("pathParameters") or {}
    addon_id = path_params.get("addon_id")
    
    if not addon_id:
        raise ValueError("addon_id is required in path")
    
    payload = event.body()
    
    result = service.update_addon(
        addon_id=addon_id,
        updates=payload
    )
    
    return result
