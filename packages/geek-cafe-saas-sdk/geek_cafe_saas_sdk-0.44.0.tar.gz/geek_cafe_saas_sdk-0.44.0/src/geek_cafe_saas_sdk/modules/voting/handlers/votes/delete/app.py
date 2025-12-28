"""
Lambda handler for deleting a vote by its ID.

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
    Lambda handler for deleting a vote by its ID.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional VoteService for testing
    """
    return handler_wrapper.execute(event, context, delete_vote, injected_service)


def delete_vote(event: LambdaEvent, service: VoteService) -> ServiceResult:
    """
    Business logic for deleting a vote.
    
    Service already has request_context with tenant_id and user_id.
    """
    vote_id = event.path("id", "voteId")
    
    if not vote_id:
        raise ValueError("Vote ID is required in the path")
    
    return service.delete(vote_id=vote_id)
