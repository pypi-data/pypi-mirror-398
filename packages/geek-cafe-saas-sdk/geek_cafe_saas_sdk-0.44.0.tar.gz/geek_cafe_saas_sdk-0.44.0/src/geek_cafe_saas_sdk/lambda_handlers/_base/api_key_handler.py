"""
Lambda handler with API key validation.

Implements the API key validation pattern used across the application.
"""

import os
from typing import Dict, Any, Optional, Callable, TypeVar
from aws_lambda_powertools import Logger

from geek_cafe_saas_sdk.utilities.response import error_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility
from .base_handler import BaseLambdaHandler

logger = Logger()
T = TypeVar('T')


class ApiKeyLambdaHandler(BaseLambdaHandler):
    """
    Lambda handler with API key validation.
    
    Validates that requests include a valid API key in the x-api-key header.
    The expected API key is read from the API_KEY environment variable.
    
    Example:
        handler = ApiKeyLambdaHandler(
            service_class=VoteService,
            require_body=True
        )
        
        def lambda_handler(event, context):
            return handler.execute(event, context, process_vote)
        
        def process_vote(event, service, user_context):
            payload = event["parsed_body"]
            return service.create_vote(...)
    """
    
    def __init__(
        self,
        api_key_env_var: str = "API_KEY",
        api_key_header: str = "x-api-key",
        **kwargs
    ):
        """
        Initialize the API key handler.
        
        Args:
            api_key_env_var: Environment variable name for API key
            api_key_header: Header name to check for API key
            **kwargs: Arguments passed to BaseLambdaHandler
        """
        # API key handlers don't require JWT auth - API key IS the auth
        kwargs.setdefault('require_auth', False)
        super().__init__(**kwargs)
        self.api_key_env_var = api_key_env_var
        self.api_key_header = api_key_header
    
    def _validate_security(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate API key is present and correct at request time.

        This method reads the API_KEY environment variable within the request
        cycle, making it testable.

        Returns:
            Error response if validation fails, None if valid.
        """
        # 1. Get expected key from environment (at request time)
        expected_api_key = os.getenv(self.api_key_env_var)

        # 2. Check if the key is configured in the environment
        if not expected_api_key:
            logger.error(
                f"API key not configured. Set '{self.api_key_env_var}' environment variable."
            )
            # This is a server-side configuration error
            return error_response(
                "This endpoint is not configured for API key access.",
                "CONFIGURATION_ERROR",
                500,
            )

        # 3. Get provided key from request headers
        provided_api_key = LambdaEventUtility.get_value_from_header(
            event, self.api_key_header
        )

        # 4. Check if a key was provided
        if not provided_api_key:
            logger.warning(f"No API key provided in '{self.api_key_header}' header.")
            return error_response("API key is required.", "UNAUTHORIZED", 401)

        # 5. Validate the key
        if provided_api_key != expected_api_key:
            logger.warning("Invalid API key provided.")
            return error_response("Invalid API key.", "UNAUTHORIZED", 401)

        # 6. Validation passed
        logger.info("API key validation successful.")
        return None

    def execute(
        self,
        event: Dict[str, Any],
        context: Any,
        business_logic: Callable[[Dict[str, Any], Any, Dict[str, Any]], Any],
        injected_service: Optional[T] = None
    ) -> Dict[str, Any]:
        """
        Execute the Lambda handler with API key validation.
        
        Args:
            event: Lambda event dictionary
            context: Lambda context object
            business_logic: Callable that implements the business logic
            injected_service: Optional service instance for testing
            
        Returns:
            Lambda response dictionary
        """
        # Validate API key first
        validation_error = self._validate_security(event)
        if validation_error:
            return validation_error
        
        # If validation passed, execute parent's execute method
        return super().execute(event, context, business_logic, injected_service)
