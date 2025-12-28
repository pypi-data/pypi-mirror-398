"""
Lambda handler for listing payments.

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
    List payments for a tenant or billing account.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional PaymentService for testing
    
    Query parameters:
    - billingAccountId: Optional billing account ID to filter by
    - limit: Optional page size (default: 50, max: 100)
    
    Returns 200 with list of payments
    """
    return handler_wrapper.execute(event, context, list_payments, injected_service)


def list_payments(event: LambdaEvent, service: PaymentService) -> ServiceResult:
    """
    Business logic for listing payments.
    """
    tenant_id = user_context.get("tenant_id")
    
    # Extract query parameters
    query_params = event.get("queryStringParameters") or {}
    billing_account_id = query_params.get("billingAccountId")
    limit = query_params.get("limit", "50")
    
    # Validate and convert limit
    try:
        limit = int(limit)
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
    except ValueError as e:
        raise ValueError(f"Invalid limit parameter: {str(e)}")
    
    # List payments
    result = service.list_payments(
        tenant_id=tenant_id,
        billing_account_id=billing_account_id,
        limit=limit
    )
    
    return result
