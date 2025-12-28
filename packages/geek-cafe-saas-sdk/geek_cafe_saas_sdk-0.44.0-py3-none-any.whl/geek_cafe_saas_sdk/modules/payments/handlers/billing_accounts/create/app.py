"""
Lambda handler for creating billing accounts.

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
    Create a new billing account.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional PaymentService for testing
    
    Expected body (camelCase from frontend):
    {
        "accountHolderId": "user-123",
        "accountHolderType": "user",  // "user", "organization", "property"
        "currencyCode": "USD",
        "billingEmail": "user@example.com",
        "billingName": "John Doe",
        "billingPhone": "+1234567890",
        "addressLine1": "123 Main St",
        "addressLine2": "Apt 4B",
        "addressCity": "San Francisco",
        "addressState": "CA",
        "addressPostalCode": "94105",
        "addressCountry": "US",
        "stripeCustomerId": "cus_xxx",  // Optional
        "taxId": "12-3456789",  // Optional
        "taxIdType": "us_ein",  // Optional
        "taxExempt": false  // Optional
    }
    
    Returns 201 with created billing account
    """
    return handler_wrapper.execute(event, context, create_billing_account, injected_service)


def create_billing_account(event: LambdaEvent, service: PaymentService) -> ServiceResult:
    """
    Business logic for creating billing accounts.
    """
    payload = event.body()
    
    tenant_id = user_context.get("tenant_id")
    
    # Extract required fields
    account_holder_id = payload.get("account_holder_id")
    if not account_holder_id:
        raise ValueError("account_holder_id is required")
    
    # Extract optional fields with defaults
    account_holder_type = payload.get("account_holder_type", "user")
    currency_code = payload.get("currency_code", "USD")
    billing_email = payload.get("billing_email")
    
    # Build kwargs for optional fields
    kwargs = {}
    optional_fields = [
        "billing_name", "billing_phone",
        "address_line1", "address_line2", "address_city", 
        "address_state", "address_postal_code", "address_country",
        "stripe_customer_id", "stripe_account_id",
        "country_code", "locale",
        "tax_id", "tax_id_type", "tax_exempt", "tax_metadata",
        "default_payment_method_id", "allowed_payment_methods",
        "auto_charge_enabled", "require_cvv", "send_receipts",
        "balance_cents", "credit_limit_cents",
        "notes", "external_reference"
    ]
    
    for field in optional_fields:
        if field in payload:
            kwargs[field] = payload[field]
    
    # Create billing account
    result = service.create_billing_account(
        tenant_id=tenant_id,
        account_holder_id=account_holder_id,
        account_holder_type=account_holder_type,
        currency_code=currency_code,
        billing_email=billing_email,
        **kwargs
    )
    
    return result
