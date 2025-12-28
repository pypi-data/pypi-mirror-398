"""
Lambda handler for getting payment by ID.

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
    Get payment by ID.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional PaymentService for testing
    
    Path parameters:
    - paymentId: Payment ID
    
    Returns 200 with payment data
    """
    return handler_wrapper.execute(event, context, get_payment, injected_service)


def get_payment(event: LambdaEvent, service: PaymentService) -> ServiceResult:
    """
    Business logic for getting payment.
    """
    tenant_id = user_context.get("tenant_id")
    
    # Extract payment ID from path parameters
    path_params = event.get("pathParameters", {})
    payment_id = path_params.get("paymentId")
    
    if not payment_id:
        raise ValueError("paymentId path parameter is required")
    
    # Get payment
    result = service.get_payment(
        payment_id=payment_id,
        tenant_id=tenant_id
    )
    
    return result
