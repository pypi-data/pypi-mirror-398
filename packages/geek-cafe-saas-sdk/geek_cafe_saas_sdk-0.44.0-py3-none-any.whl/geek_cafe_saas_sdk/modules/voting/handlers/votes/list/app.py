"""
Lambda handler for listing votes with optional filters.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.services import VoteService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=VoteService,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for listing votes with optional filters.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional VoteService for testing
    """
    return handler_wrapper.execute(event, context, list_votes, injected_service)


def list_votes(event: LambdaEvent, service: VoteService) -> ServiceResult:
    """
    Business logic for listing votes.
    
    Service already has request_context with tenant_id and user_id.
    """
    target_id = event.query("target_id", "targetId")
    
    if target_id:
        return service.list_by_target(target_id=target_id)
    else:
        # Default to listing by authenticated user
        user_id = service.request_context.authenticated_user_id
        return service.list_by_user(user_id=user_id)
