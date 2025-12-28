"""
Lambda handler for getting refund by ID.

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
    Get refund by ID.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional PaymentService for testing
    
    Path parameters:
    - refundId: Refund ID
    
    Returns 200 with refund data
    """
    return handler_wrapper.execute(event, context, get_refund, injected_service)


def get_refund(event: LambdaEvent, service: PaymentService) -> ServiceResult:
    """
    Business logic for getting refund.
    """
    tenant_id = user_context.get("tenant_id")
    
    # Extract refund ID from path parameters
    path_params = event.get("pathParameters", {})
    refund_id = path_params.get("refundId")
    
    if not refund_id:
        raise ValueError("refundId path parameter is required")
    
    # Get refund
    result = service.get_refund(
        refund_id=refund_id,
        tenant_id=tenant_id
    )
    
    return result
