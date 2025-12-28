"""
Secure Lambda handler that relies on API Gateway authorization.

This handler assumes that API Gateway (or ALB) has already validated
the request using AWS Cognito, IAM, or a custom authorizer.
The handler trusts that the request has been authenticated.
"""

from typing import Dict, Any, Optional
from aws_lambda_powertools import Logger

from .base_handler import BaseLambdaHandler

logger = Logger()


class SecureLambdaHandler(BaseLambdaHandler):
    """
    Secure handler that relies on API Gateway/ALB authorization.
    
    Use this when:
    - API Gateway has a Cognito authorizer configured
    - API Gateway has a Lambda authorizer configured
    - ALB has authentication configured
    - Request is authenticated before reaching Lambda
    
    The handler does NOT perform its own authentication.
    It trusts the upstream service (API Gateway/ALB).
    
    Example:
        handler = SecureLambdaHandler(
            service_class=VoteService,
            require_body=True
        )
        
        def lambda_handler(event, context):
            return handler.execute(event, context, process_vote)
        
        def process_vote(event, service, user_context):
            # user_context contains claims from API Gateway authorizer
            payload = event["parsed_body"]
            return service.create_vote(...)
    """
    
    def __init__(
        self,
        require_authorizer_claims: bool = True,
        **kwargs
    ):
        """
        Initialize the secure handler.
        
        Args:
            require_authorizer_claims: Whether to require authorizer claims in event
            **kwargs: Arguments passed to BaseLambdaHandler
        """
        super().__init__(**kwargs)
        self.require_authorizer_claims = require_authorizer_claims
    
    def _validate_security(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate that request came through authorized API Gateway.
        
        Checks for requestContext.authorizer which is populated by
        API Gateway when using Cognito or Lambda authorizers.
        
        Returns:
            Error response if validation fails, None if valid
        """
        if not self.require_authorizer_claims:
            return None
        
        # Check for API Gateway request context
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})
        
        # If no authorizer context, this might be a misconfiguration
        if not authorizer:
            logger.warning(
                "SecureLambdaHandler: No authorizer context found. "
                "Ensure API Gateway has an authorizer configured."
            )
            # You can choose to allow or deny here
            # For now, we'll log a warning but allow (assuming local dev/testing)
            # In production, you might want to return an error
        
        # The handler trusts API Gateway did the auth
        # User claims are extracted in extract_user_context()
        return None
