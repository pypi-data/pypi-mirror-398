"""
Lambda handler for getting an addon.

Public endpoint - no authentication required.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.subscriptions.services import SubscriptionManagerService


handler_wrapper = create_handler(
    service_class=SubscriptionManagerService,
    require_auth=False,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Get an addon by ID.
    
    Path parameters:
    - addonId: Addon ID
    
    Returns 200 with addon details
    """
    return handler_wrapper.execute(event, context, get_addon, injected_service)


def get_addon(event: LambdaEvent, service: SubscriptionManagerService) -> ServiceResult:
    """
    Business logic for getting an addon.
    """
    path_params = event.get("pathParameters") or {}
    addon_id = path_params.get("addon_id")
    
    if not addon_id:
        raise ValueError("addon_id is required in path")
    
    result = service.get_addon(addon_id=addon_id)
    
    return result
