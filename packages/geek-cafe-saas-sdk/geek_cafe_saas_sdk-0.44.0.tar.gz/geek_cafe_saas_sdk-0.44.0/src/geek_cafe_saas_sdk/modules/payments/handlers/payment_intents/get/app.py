"""
Lambda handler for getting payment intent by ID.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.payments.services import PaymentService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=PaymentService,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Get payment intent by ID.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional PaymentService for testing
    
    Path parameters:
    - intentId: Payment intent reference ID
    
    Returns 200 with payment intent data
    """
    return handler_wrapper.execute(event, context, get_payment_intent, injected_service)


def get_payment_intent(event: LambdaEvent, service: PaymentService) -> ServiceResult:
    """
    Business logic for getting payment intent.
    """
    tenant_id = user_context.get("tenant_id")
    
    # Extract intent ID from path parameters
    path_params = event.get("pathParameters", {})
    intent_id = path_params.get("intentId")
    
    if not intent_id:
        raise ValueError("intentId path parameter is required")
    
    # Get payment intent
    result = service.get_payment_intent(
        intent_ref_id=intent_id,
        tenant_id=tenant_id
    )
    
    return result
