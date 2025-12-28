# src/geek_cafe_saas_sdk/lambda_handlers/communities/get/app.py

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.communities.services.community_service import CommunityService
from geek_cafe_saas_sdk.core.service_result import ServiceResult

# Create handler wrapper
handler_wrapper = create_handler(
    service_class=CommunityService,
    convert_request_case=True
)

def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Lambda handler for getting a community by ID.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional CommunityService for testing
    
    Returns 200 with community data
    """
    return handler_wrapper.execute(event, context, get_community_logic, injected_service)

def get_community_logic(
    event: LambdaEvent,
    service: CommunityService
) -> ServiceResult:
    """Business logic for getting a community."""
    community_id = event.path("id")
    
    # Service now uses request_context internally
    result = service.get_by_id(community_id=community_id)
    
    return result
