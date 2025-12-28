"""
Lambda handler for updating billing accounts.

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
    Update a billing account.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional PaymentService for testing
    
    Path parameters:
    - accountId: Billing account ID
    
    Expected body (camelCase from frontend):
    {
        "billingEmail": "newemail@example.com",
        "billingName": "Jane Doe",
        "addressLine1": "456 New St",
        "stripeCustomerId": "cus_yyy",
        "defaultPaymentMethodId": "pm_xxx",
        "autoChargeEnabled": true,
        "status": "active"
        // Any updateable field from BillingAccount
    }
    
    Returns 200 with updated billing account
    """
    return handler_wrapper.execute(event, context, update_billing_account, injected_service)


def update_billing_account(event: LambdaEvent, service: PaymentService) -> ServiceResult:
    """
    Business logic for updating billing account.
    """
    payload = event.body()
    tenant_id = user_context.get("tenant_id")
    
    # Extract account ID from path parameters
    path_params = event.get("pathParameters", {})
    account_id = path_params.get("accountId")
    
    if not account_id:
        raise ValueError("accountId path parameter is required")
    
    # All payload fields are treated as updates
    updates = {}
    updatable_fields = [
        "billing_email", "billing_name", "billing_phone",
        "address_line1", "address_line2", "address_city",
        "address_state", "address_postal_code", "address_country",
        "stripe_customer_id", "stripe_account_id",
        "country_code", "locale",
        "tax_id", "tax_id_type", "tax_exempt", "tax_metadata",
        "default_payment_method_id", "allowed_payment_methods",
        "auto_charge_enabled", "require_cvv", "send_receipts",
        "balance_cents", "credit_limit_cents",
        "status", "status_reason",
        "notes", "external_reference"
    ]
    
    for field in updatable_fields:
        if field in payload:
            updates[field] = payload[field]
    
    if not updates:
        raise ValueError("No valid fields to update")
    
    # Update billing account
    result = service.update_billing_account(
        account_id=account_id,
        tenant_id=tenant_id,
        updates=updates
    )
    
    return result
