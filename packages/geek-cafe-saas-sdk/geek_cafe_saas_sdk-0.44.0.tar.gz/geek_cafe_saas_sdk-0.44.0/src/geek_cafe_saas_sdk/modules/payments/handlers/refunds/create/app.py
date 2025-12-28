"""
Lambda handler for creating refunds.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.payments.services import PaymentService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=PaymentService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Create a refund for a payment.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional PaymentService for testing
    
    Expected body (camelCase from frontend):
    {
        "paymentId": "payment-123",
        "amountCents": 5000,  // Amount to refund (must not exceed remaining)
        "reason": "requested_by_customer",  // "duplicate", "fraudulent", "requested_by_customer"
        "description": "Customer requested refund",
        "pspRefundId": "re_xxx",  // Optional - PSP refund ID if already created
        "disputeId": "dp_xxx"  // Optional - if related to dispute
    }
    
    Returns 201 with created refund
    """
    return handler_wrapper.execute(event, context, create_refund, injected_service)


def create_refund(event: LambdaEvent, service: PaymentService) -> ServiceResult:
    """
    Business logic for creating refunds.
    """
    payload = event.body()
    tenant_id = user_context.get("tenant_id")
    user_id = user_context.get("user_id")
    
    # Extract required fields
    payment_id = payload.get("payment_id")
    amount_cents = payload.get("amount_cents")
    
    if not payment_id:
        raise ValueError("payment_id is required")
    if amount_cents is None or amount_cents <= 0:
        raise ValueError("amount_cents must be greater than 0")
    
    # Extract optional fields
    reason = payload.get("reason")
    
    # Build kwargs for optional fields
    kwargs = {}
    optional_fields = [
        "description", "psp_refund_id", "psp_balance_transaction_id",
        "dispute_id", "notes"
    ]
    
    for field in optional_fields:
        if field in payload:
            kwargs[field] = payload[field]
    
    # Create refund
    result = service.create_refund(
        tenant_id=tenant_id,
        payment_id=payment_id,
        amount_cents=amount_cents,
        reason=reason,
        initiated_by_id=user_id,
        **kwargs
    )
    
    return result
