"""
Lambda handler for creating votes.

REFACTORED VERSION using Factory Pattern.
Reduces code and centralizes auth strategy configuration.

The handler type is determined by environment variables:
- AUTH_TYPE=secure (default) - API Gateway authorizer
- AUTH_TYPE=api_key - x-api-key header validation
- AUTH_TYPE=public - No authentication
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.voting.services import VoteService
from geek_cafe_saas_sdk.utilities.response import error_response

# ⚡ Initialize handler at module level for Lambda warm starts
# Factory automatically selects handler based on AUTH_TYPE env var:
#   - secure (default): API Gateway authorizer (Cognito/Lambda)
#   - api_key: Validates x-api-key header
#   - public: No authentication required
#
# This automatically handles:
# - Authentication (based on AUTH_TYPE)
# - Request body parsing
# - Case conversion (camelCase → snake_case)
# - Service pooling (connection reuse)
# - User context extraction
# - CORS headers (apply_cors=True by default)
# - Error handling (apply_error_handling=True by default)
handler = create_handler(
    service_class=VoteService,
    require_body=True,
    convert_request_case=True
)

def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Create or update a vote.
    
    Args:
        event: API Gateway event
        context: Lambda context
        injected_service: Optional VoteService for testing (Moto)

    Expected request body:
    {
        "userId": "user_id",
        "targetId": "health-meter-ui-choice",
        "choiceId": "gauge" | "traffic_light",
        "voteType": "single_choice",
        "availableChoices": ["gauge", "traffic_light"],
        "content": {
            "description": "User preference for health meter display type",
            "metadata": {...}
        }
    }
    """
    return handler.execute(event, context, create_vote, injected_service)


def create_vote(event: LambdaEvent, service: VoteService) -> ServiceResult:
    """
    Business logic for creating a vote.
    
    All boilerplate has been handled by the wrapper:
    ✅ API key validation
    ✅ Body parsing and case conversion
    ✅ Service initialization
    ✅ User context extraction
    
    Focus purely on business logic here.
    
    Args:
        event: Enhanced event with parsed_body containing snake_case data
        service: VoteService instance (pooled for warm starts)
        user_context: Extracted user info (user_id, tenant_id, etc.)
    
    Returns:
        ServiceResult that will be formatted into Lambda response
    """
    # Get parsed and converted body (camelCase → snake_case already done)
    payload = event.body()
    
    # Validate required fields
    target_id = payload.get("target_id")
    if not target_id:
        return error_response("target_id is required", 400)
    
    choice_id = payload.get("choice_id")
    if not choice_id:
        return error_response("choice_id is required", 400)
    
    vote_type = payload.get("vote_type", "single_choice")
    available_choices = payload.get("available_choices", [])
    content = payload.get("content", {})
    
    # Validate choice_id is in available_choices if provided
    if available_choices and choice_id not in available_choices:
        return error_response(
            f"choice_id '{choice_id}' must be one of: {available_choices}", 400
        )
    
    # Service uses request_context internally for tenant_id/user_id
    # Create the vote based on type
    if vote_type == "single_choice":
        result = service.create_single_choice_vote(
            target_id=target_id,
            choice_id=choice_id,
            available_choices=available_choices if available_choices else None,
            content=content if content else None,
        )
    else:
        return error_response(f"Unsupported vote_type: {vote_type}", 400)
    
    # Return ServiceResult - handler will automatically format to Lambda response
    return result
