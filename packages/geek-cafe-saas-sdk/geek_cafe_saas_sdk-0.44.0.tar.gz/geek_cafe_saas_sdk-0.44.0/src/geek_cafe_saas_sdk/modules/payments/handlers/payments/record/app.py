"""
Lambda handler for recording settled payments.

Typically called from Stripe webhooks or payment processor callbacks.
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
    Record a settled payment.
    
    Args:
        event: Lambda event from API Gateway or webhook
        context: Lambda context
        injected_service: Optional PaymentService for testing
    
    Expected body (camelCase from frontend/webhook):
    {
        "billingAccountId": "account-123",
        "paymentIntentRefId": "intent-123",  // Optional
        "grossAmountCents": 5000,  // $50.00
        "feeAmountCents": 145,  // $1.45 (Stripe fee)
        "currencyCode": "USD",
        "pspType": "stripe",
        "pspTransactionId": "txn_xxx",
        "pspChargeId": "ch_xxx",
        "pspBalanceTransactionId": "txn_balance_xxx",
        "paymentMethodId": "pm_xxx",
        "paymentMethodType": "card",
        "paymentMethodLast4": "4242",
        "paymentMethodBrand": "visa",
        "paymentMethodFunding": "credit",
        "description": "Subscription payment",
        "statementDescriptor": "ACME SUBSCRIPTION",
        "receiptEmail": "user@example.com",
        "receiptUrl": "https://stripe.com/receipt/xxx",
        "customerId": "user-123",  // Optional
        "invoiceId": "inv-123",  // Optional
        "subscriptionId": "sub-123"  // Optional
    }
    
    Returns 201 with recorded payment
    """
    return handler_wrapper.execute(event, context, record_payment, injected_service)


def record_payment(event: LambdaEvent, service: PaymentService) -> ServiceResult:
    """
    Business logic for recording payments.
    """
    payload = event.body()
    tenant_id = user_context.get("tenant_id")
    
    # Extract required fields
    billing_account_id = payload.get("billing_account_id")
    gross_amount_cents = payload.get("gross_amount_cents")
    fee_amount_cents = payload.get("fee_amount_cents")
    
    if not billing_account_id:
        raise ValueError("billing_account_id is required")
    if gross_amount_cents is None or gross_amount_cents <= 0:
        raise ValueError("gross_amount_cents must be greater than 0")
    if fee_amount_cents is None or fee_amount_cents < 0:
        raise ValueError("fee_amount_cents must be non-negative")
    
    # Extract optional fields
    payment_intent_ref_id = payload.get("payment_intent_ref_id")
    currency_code = payload.get("currency_code", "USD")
    psp_type = payload.get("psp_type", "stripe")
    
    # Build kwargs for optional fields
    kwargs = {}
    optional_fields = [
        "psp_transaction_id", "psp_charge_id", "psp_balance_transaction_id",
        "fee_details",
        "payment_method_id", "payment_method_type", "payment_method_last4",
        "payment_method_brand", "payment_method_funding",
        "settlement_date", "payout_id",
        "customer_id", "invoice_id", "subscription_id",
        "description", "statement_descriptor",
        "receipt_number", "receipt_email", "receipt_url",
        "psp_metadata", "application_fee_amount_cents"
    ]
    
    for field in optional_fields:
        if field in payload:
            kwargs[field] = payload[field]
    
    # Record payment
    result = service.record_payment(
        tenant_id=tenant_id,
        billing_account_id=billing_account_id,
        payment_intent_ref_id=payment_intent_ref_id,
        gross_amount_cents=gross_amount_cents,
        fee_amount_cents=fee_amount_cents,
        currency_code=currency_code,
        psp_type=psp_type,
        **kwargs
    )
    
    return result
