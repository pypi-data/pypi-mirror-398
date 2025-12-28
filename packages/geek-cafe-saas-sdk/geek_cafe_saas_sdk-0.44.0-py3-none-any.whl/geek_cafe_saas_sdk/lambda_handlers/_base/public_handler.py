"""
Lambda handler for public endpoints.

Public handler with no authentication required.
Useful for public APIs, health checks, and configuration endpoints.
"""

from typing import Dict, Any, Optional
from .base_handler import BaseLambdaHandler


class PublicLambdaHandler(BaseLambdaHandler):
    """
    Lambda handler for public endpoints (no authentication).
    
    Does not require any authentication or API keys.
    Use for truly public endpoints like health checks or public configuration.
    
    Example:
        handler = PublicLambdaHandler(
            require_body=False,
            convert_request_case=False
        )
        
        def lambda_handler(event, context):
            return handler.execute(event, context, get_config)
        
        def get_config(event, service, user_context):
            return {
                "version": "1.0",
                "environment": os.getenv("ENVIRONMENT")
            }
    """
    
    def __init__(self, **kwargs):
        """
        Initialize public handler.
        
        Args:
            **kwargs: Arguments passed to BaseLambdaHandler
        """
        # Public handlers don't require JWT auth
        kwargs.setdefault('require_auth', False)
        super().__init__(**kwargs)
    
    def _validate_security(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Public endpoints have no security validation.
        
        Returns:
            None (always valid)
        """
        return None
