"""
Example: API Key Protected Lambda Handler

This example shows how to use ApiKeyLambdaHandler to eliminate boilerplate
in a Lambda function that requires API key authentication.

Compare to: dictator-watch-dog-lambdas/src/saas_app_lambdas/handlers/votes/create/app.py
Reduces ~150 lines to ~30 lines.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import ApiKeyLambdaHandler
from geek_cafe_saas_sdk.vote_service import VoteService
from geek_cafe_saas_sdk.utilities.response import error_response

# ⚡ Initialize handler at module level for Lambda warm starts
# This automatically pools the VoteService instance
handler = ApiKeyLambdaHandler(
    service_class=VoteService,
    require_body=True,        # Return 400 if no body
    convert_case=True,        # Convert camelCase → snake_case
    unwrap_message=True,      # Handle SQS/SNS events
    apply_cors=True,          # Add CORS headers
    apply_error_handling=True # Catch and format errors
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda entry point.
    
    All boilerplate is handled by the wrapper:
    - ✅ API key validation
    - ✅ Request body parsing
    - ✅ Case conversion
    - ✅ Service pooling
    - ✅ User context extraction
    - ✅ CORS headers
    - ✅ Error handling
    
    Expected request body:
    {
        "targetId": "health-meter-ui-choice",
        "choiceId": "gauge",
        "voteType": "single_choice",
        "availableChoices": ["gauge", "traffic_light"]
    }
    """
    return handler.execute(event, context, create_vote)


def create_vote(
    event: Dict[str, Any],
    service: VoteService,
    user_context: Dict[str, str]
) -> Any:
    """
    Business logic for creating a vote.
    
    All boilerplate has been handled - focus purely on business logic.
    
    Args:
        event: Enhanced event with parsed_body containing snake_case data
        service: VoteService instance (pooled for warm starts)
        user_context: Extracted user info (user_id, tenant_id, etc.)
    
    Returns:
        ServiceResult that will be formatted into Lambda response
    """
    # Get parsed and converted body
    payload = event["parsed_body"]
    
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
    
    # Get user info from context
    tenant_id = user_context.get("tenant_id", "anonymous")
    user_id = user_context.get("user_id") or payload.get("user_id", "anonymous")
    
    # Execute business logic
    if vote_type == "single_choice":
        result = service.create_single_choice_vote(
            tenant_id=tenant_id,
            user_id=user_id,
            target_id=target_id,
            choice_id=choice_id,
            available_choices=available_choices if available_choices else None,
            content=content if content else None,
        )
    else:
        return error_response(f"Unsupported vote_type: {vote_type}", 400)
    
    # Return ServiceResult - handler will format to Lambda response
    return result


# For testing with service injection
def test_example():
    """Example of testing with injected service."""
    import json
    from unittest.mock import Mock
    
    # Create mock service
    mock_service = Mock(spec=VoteService)
    mock_service.create_single_choice_vote.return_value = {
        "success": True,
        "data": {"vote_id": "test-123"}
    }
    
    # Create test event
    event = {
        "body": json.dumps({
            "targetId": "test-target",
            "choiceId": "option1",
            "voteType": "single_choice"
        }),
        "headers": {"x-api-key": "test-key"}
    }
    
    # Execute with injected service
    response = handler.execute(
        event,
        context=None,
        business_logic=create_vote,
        injected_service=mock_service
    )
    
    print(f"Response: {response}")
