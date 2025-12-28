"""
Lambda handler for getting billing account by ID.

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
    Get billing account by ID.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional PaymentService for testing
    
    Path parameters:
    - accountId: Billing account ID
    
    Returns 200 with billing account data
    """
    return handler_wrapper.execute(event, context, get_billing_account, injected_service)


def get_billing_account(event: LambdaEvent, service: PaymentService) -> ServiceResult:
    """
    Business logic for getting billing account.
    """
    tenant_id = user_context.get("tenant_id")
    
    # Extract account ID from path parameters
    path_params = event.get("pathParameters", {})
    account_id = path_params.get("accountId")
    
    if not account_id:
        raise ValueError("accountId path parameter is required")
    
    # Get billing account
    result = service.get_billing_account(
        account_id=account_id,
        tenant_id=tenant_id
    )
    
    return result
