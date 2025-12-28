"""
Lambda handler for creating payment intents.

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
    Create a payment intent.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional PaymentService for testing
    
    Expected body (camelCase from frontend):
    {
        "billingAccountId": "account-123",
        "amountCents": 5000,  // $50.00
        "currencyCode": "USD",
        "pspType": "stripe",  // "stripe", "paypal", "square"
        "description": "Subscription payment",
        "statementDescriptor": "ACME SUBSCRIPTION",
        "receiptEmail": "user@example.com",
        "setupFutureUsage": "off_session",  // Optional
        "captureMethod": "automatic",  // Optional
        "invoiceId": "inv-123",  // Optional
        "subscriptionId": "sub-123"  // Optional
    }
    
    Returns 201 with created payment intent
    """
    return handler_wrapper.execute(event, context, create_payment_intent, injected_service)


def create_payment_intent(event: LambdaEvent, service: PaymentService) -> ServiceResult:
    """
    Business logic for creating payment intents.
    """
    payload = event.body()
    tenant_id = user_context.get("tenant_id")
    
    # Extract required fields
    billing_account_id = payload.get("billing_account_id")
    amount_cents = payload.get("amount_cents")
    
    if not billing_account_id:
        raise ValueError("billing_account_id is required")
    if amount_cents is None or amount_cents <= 0:
        raise ValueError("amount_cents must be greater than 0")
    
    # Extract optional fields with defaults
    currency_code = payload.get("currency_code", "USD")
    psp_type = payload.get("psp_type", "stripe")
    
    # Build kwargs for optional fields
    kwargs = {}
    optional_fields = [
        "psp_intent_id", "psp_client_secret",
        "payment_method_id", "payment_method_type",
        "description", "statement_descriptor", "receipt_email",
        "setup_future_usage", "capture_method", "confirmation_method",
        "invoice_id", "subscription_id"
    ]
    
    for field in optional_fields:
        if field in payload:
            kwargs[field] = payload[field]
    
    # Create payment intent
    result = service.create_payment_intent(
        tenant_id=tenant_id,
        billing_account_id=billing_account_id,
        amount_cents=amount_cents,
        currency_code=currency_code,
        psp_type=psp_type,
        **kwargs
    )
    
    return result
