"""
Lambda handler for updating an existing vote.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.services import VoteService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=VoteService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for updating an existing vote.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional VoteService for testing
    """
    return handler_wrapper.execute(event, context, update_vote, injected_service)


def update_vote(event: LambdaEvent, service: VoteService) -> ServiceResult:
    """
    Business logic for updating a vote.
    
    Service already has request_context with tenant_id and user_id.
    """
    vote_id = event.path("id", "voteId")
    
    if not vote_id:
        raise ValueError("Vote ID is required in the path")
    
    return service.update(vote_id=vote_id, updates=event.body)
