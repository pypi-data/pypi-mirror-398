"""
Lambda handler for getting a discount.

Admin endpoint - requires authentication.
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
    Get a discount by ID.
    
    Path parameters:
    - discountId: Discount ID
    
    Returns 200 with discount details
    """
    return handler_wrapper.execute(event, context, get_discount, injected_service)


def get_discount(event: LambdaEvent, service: SubscriptionManagerService) -> ServiceResult:
    """
    Business logic for getting a discount.
    """
    path_params = event.get("pathParameters") or {}
    discount_id = path_params.get("discount_id")
    
    if not discount_id:
        raise ValueError("discount_id is required in path")
    
    result = service.get_discount(discount_id=discount_id)
    
    return result
