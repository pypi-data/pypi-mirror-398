"""
Base Lambda handler with common functionality.

Provides a foundation for creating Lambda handlers with standardized
request/response handling, error management, and service injection.
"""

import json
import os
import time
from tracemalloc import start
from typing import Dict, Any, Callable, Optional, Set, Type, TypeVar, TYPE_CHECKING
from aws_lambda_powertools import Logger

from geek_cafe_saas_sdk.utilities.response import (
    error_response,
    service_result_to_response,
)
from geek_cafe_saas_sdk.utilities.case_conversion import CaseFormat, CaseConverter
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility
from geek_cafe_saas_sdk.utilities.logging_utility import LoggingUtility
from geek_cafe_saas_sdk.utilities.environment_variables import EnvironmentVariables
from geek_cafe_saas_sdk.middleware.auth import extract_user_context
from geek_cafe_saas_sdk.core.services.feature_flag_service import get_feature_flag_service
from .service_pool import ServicePool

if TYPE_CHECKING:
    from geek_cafe_saas_sdk.core.services_container import ServicesContainer

logger = Logger()

T = TypeVar('T')  # Service type


class BaseLambdaHandler:
    """
    Base class for Lambda handlers with common functionality.
    
    Handles:
    - Request body parsing and case conversion
    - Service initialization and pooling
    - User context extraction
    - Response formatting
    - Event unwrapping (SQS, SNS, etc.)
    
    """
    
    def __init__(
        self,
        service_class: Optional[Type[T]] = None,
        require_auth: bool = True,
        service_kwargs: Optional[Dict[str, Any]] = None,
        services_container: Optional['ServicesContainer'] = None,
        require_body: bool = False,
        require_request_context: bool = True,
        convert_request_case: bool = True,
        convert_response_case: bool | None = None,
        unwrap_message: bool = True,
        apply_cors: bool = True,
        apply_error_handling: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize handler with configuration.
        
        Args:
            service_class: Service class to instantiate
            require_auth: Require authentication
            service_kwargs: Additional kwargs for service instantiation
            services_container: ServicesContainer for dependency injection
            require_body: Require request body
            require_request_context: Require requestContext in event (default: True).
                Set to False for S3, SQS, SNS, EventBridge triggers that don't have requestContext.
            convert_request_case: Convert request camelCase → snake_case (default: True)
            convert_response_case: Convert response snake_case → camelCase (default: None, uses env var or True)
            unwrap_message: Unwrap SQS/SNS messages
            apply_cors: Apply CORS headers
            apply_error_handling: Apply automatic error handling
            config: Optional configuration dict passed to LambdaEvent (e.g., bucket names, feature flags)
        """
        self.service_class = service_class
        self.service_kwargs = service_kwargs or {}
        self.services_container = services_container
        self.require_body = require_body
        self.require_request_context = require_request_context
        self.convert_request_case = convert_request_case
        self.convert_response_case = convert_response_case
        self.unwrap_message = unwrap_message
        self.apply_cors = apply_cors
        self.apply_error_handling = apply_error_handling
        self.require_auth = require_auth
        self.config = config or {}

        # Initialize service pool if a class is provided
        self._service_pool = ServicePool(service_class, **self.service_kwargs) if service_class else None

    def _get_service(self, injected_service: Optional[T], request_context: Optional[Any] = None) -> Optional[T]:
        """
        Get service instance (injected or from pool) with FRESH request_context.
        
        Args:
            injected_service: Injected service for testing
            request_context: Fresh RequestContext for this invocation
            
        Returns:
            Service instance with refreshed security context
        """
        if injected_service:
            # Testing: Refresh context on injected service too
            if request_context is not None and hasattr(injected_service, '_request_context'):
                injected_service._request_context = request_context
            return injected_service
        
        if self._service_pool:
            # Production: Get from pool with fresh context
            return self._service_pool.get(request_context)
        
        # Fallback for direct instantiation if pooling is not used (rare)
        if self.service_class:
            kwargs = {**self.service_kwargs}
            if request_context is not None:
                kwargs['request_context'] = request_context
            return self.service_class(**kwargs)

        return None

    def _should_generate_provenance(self, user_context: Dict[str, Any]) -> bool:
        """
        Check if provenance should be generated for this request.
        
        Args:
            user_context: User context containing tenant_id, user_id, etc.
            
        Returns:
            True if provenance generation is enabled
        """
        try:
            feature_flag_service = get_feature_flag_service()
            tenant_id = user_context.get('tenant_id')
            user_id = user_context.get('user_id')
            
            # Only generate provenance if file_system_v2 is enabled
            return feature_flag_service.is_enabled(
                'file_system_v2',
                tenant_id=tenant_id,
                user_id=user_id,
                default=False  # Default to False for v1 behavior
            )
        except Exception as e:
            # If feature flag service fails, default to no provenance for safety
            logger.warning(f"Feature flag check failed, defaulting to no provenance: {e}")
            return False

    def _get_response_case_preference(self, event: Dict[str, Any]) -> CaseFormat:
        """
        Determine response case conversion preference from client request.
        
        Checks for client preference in this order:
        1. Query parameter: ?responseCase=camelCase or ?responseCase=snake_case
        2. Request body field: {"responseCase": "camelCase"}
        3. Handler default: self.convert_response_case
        4. Environment variable: DEFAULT_RESPONSE_CASE
        5. Default: camelCase
        
        Args:
            event: Lambda event
            
        Returns:
            CaseFormat enum indicating the desired response case format
            
        Supported formats:
            - snake, snake_case, snakecase -> snake_case
            - camel, camelCase, camelcase -> camelCase
            - pascal, PascalCase, pascalcase -> PascalCase
            - kebab, kebab-case, kebabcase -> kebab-case
            
        Examples:
            # Client requests camelCase
            GET /api/users?responseCase=camelCase
            # Returns: {"userId": "123", "firstName": "John"}
            
            # Client requests snake_case
            GET /api/users?responseCase=snake_case
            # Returns: {"user_id": "123", "first_name": "John"}
            
            # Client requests PascalCase
            GET /api/users?responseCase=pascal
            # Returns: {"UserId": "123", "FirstName": "John"}
            
            # Client requests kebab-case
            GET /api/users?responseCase=kebab
            # Returns: {"user-id": "123", "first-name": "John"}
        """
        # Check query string parameters (multiple naming conventions)
        query_params = event.get('queryStringParameters') or {}
        response_case = (
            query_params.get('responseCase') or 
            query_params.get('response_case') or 
            query_params.get('response-case')
        )
        
        if response_case:
            try:
                case_format = CaseFormat.from_string(response_case)
                logger.debug(f"Client requested {case_format.value} response via query param")
                return case_format
            except ValueError:
                logger.warning(f"Unknown response case format: {response_case}, using default")
        
        # Check parsed body (if available)
        parsed_body = event.get('parsed_body')
        if isinstance(parsed_body, dict):
            response_case = parsed_body.get('response_case') or parsed_body.get('responseCase')
            if response_case:
                try:
                    case_format = CaseFormat.from_string(response_case)
                    logger.debug(f"Client requested {case_format.value} response via body")
                    return case_format
                except ValueError:
                    logger.warning(f"Unknown response case format in body: {response_case}, using default")
        
        # No client preference - check handler setting
        if self.convert_response_case is not None:
            # Handle boolean for backwards compatibility
            if isinstance(self.convert_response_case, bool):
                return CaseFormat.CAMEL if self.convert_response_case else CaseFormat.SNAKE
            # Handle CaseFormat enum
            if isinstance(self.convert_response_case, CaseFormat):
                return self.convert_response_case
            # Handle string
            if isinstance(self.convert_response_case, str):
                try:
                    return CaseFormat.from_string(self.convert_response_case)
                except ValueError:
                    pass
        
        # Check environment variable
        env_value = os.getenv('DEFAULT_RESPONSE_CASE', 'camel')
        try:
            return CaseFormat.from_string(env_value)
        except ValueError:
            # Default to camelCase for backwards compatibility
            return CaseFormat.CAMEL

    def _get_preserve_fields(self, event: Dict[str, Any]) -> Optional[Set[str]]:
        """
        Get fields to preserve from case conversion from client request.
        
        Checks for client preference in this order:
        1. Query parameter: ?preserveFields=metadata,customData
        2. Environment variable: PRESERVE_FIELDS_FROM_CASE_CONVERSION
        3. Default: None (convert all fields)
        
        Args:
            event: Lambda event
            
        Returns:
            Set of field names to preserve, or None if all fields should be converted
            
        Examples:
            # Client requests metadata field to be preserved
            GET /api/files/123/metadata?preserveFields=metadata
            # Returns: {"userId": "123", "metadata": {"column_name": "test"}}
            # Note: metadata content keeps original case (column_name not converted)
        """
        fields: Set[str] = set()
        
        # Check multiValueQueryStringParameters first (supports repeated params)
        # e.g., ?preserveFields=metadata&preserveFields=errors
        multi_params = event.get('multiValueQueryStringParameters') or {}
        for param_name in ['preserveFields', 'preserve_fields', 'preserve-fields']:
            values = multi_params.get(param_name)
            if values:
                for val in values:
                    # Also support comma-separated within each value
                    fields.update(f.strip() for f in val.split(',') if f.strip())
        
        # Fallback to queryStringParameters (single value, comma-separated)
        # e.g., ?preserveFields=metadata,errors
        if not fields:
            query_params = event.get('queryStringParameters') or {}
            preserve_fields_str = (
                query_params.get('preserveFields') or 
                query_params.get('preserve_fields') or 
                query_params.get('preserve-fields')
            )
            if preserve_fields_str:
                fields.update(f.strip() for f in preserve_fields_str.split(',') if f.strip())
        
        if fields:
            logger.debug(f"Client requested preserve_fields: {fields}")
            return fields
        
        # Check environment variable
        env_value = os.getenv('PRESERVE_FIELDS_FROM_CASE_CONVERSION', '')
        if env_value:
            fields = {f.strip() for f in env_value.split(',') if f.strip()}
            if fields:
                return fields
        
        return None

    def _generate_provenance(self, event: Dict[str, Any], user_context: Dict[str, str]) -> Dict[str, str]:
        """
        Generate provenance data for the request.
        
        This is a no-op when file_system_v2 flag is disabled.
        When enabled, it will generate correlation/causation IDs and other provenance data.
        
        Args:
            event: Lambda event dictionary
            user_context: User context information
            
        Returns:
            Dictionary with provenance headers to add to response
        """
        if not self._should_generate_provenance(user_context):
            return {}
        
        # TODO: Implement actual provenance generation when flag is enabled
        # This will include:
        # - Correlation ID generation/retrieval
        # - Causation ID tracking
        # - Event provenance dataclass
        # - Audit event emission
        
        # For now, add correlation ID header when enabled
        import uuid
        correlation_id = str(uuid.uuid4())
        
        return {
            'X-Correlation-Id': correlation_id
        }

    def execute(
        self,
        event: Dict[str, Any],
        context: Any,
        business_logic: Callable,
        injected_service: Optional[T] = None
    ) -> Dict[str, Any]:
        """
        Execute the Lambda handler with the given business logic.
        
        NEW: Automatically loads security from services_container if provided.
        Handles authentication errors and returns proper error responses.
        
        Args:
            event: Lambda event dictionary
            context: Lambda context object
            business_logic: Callable(event, service, container) or Callable(event, service, user_context)
            injected_service: Optional service instance for testing
            
        Returns:
            Lambda response dictionary
        """
        service = None  # Track service for cleanup
        start_time = time.time()  # Track execution time for telemetry
        try:
            # Log event payload if enabled (sanitized for security)
            if EnvironmentVariables.should_log_lambda_events():
                sanitized_event = LoggingUtility.sanitize_event_for_logging(event)
                logger.info({
                    "message": "Lambda event received. The event has been sanitized for logging.",
                    "event": sanitized_event,
                    "context": context,
                    "triggered_by": "LOG_LAMBDA_EVENTS=True"
                })
            
            # Unwrap message if needed (SQS, SNS, etc.)
            if self.unwrap_message and "message" in event:
                event = event["message"]
            
            # Validate requestContext presence (Rule #4) - only if required
            # S3, SQS, SNS, EventBridge triggers don't have requestContext
            if self.require_request_context and "requestContext" not in event:
                return error_response(
                    "requestContext missing from event. For API Gateway, ensure it is properly configured. "
                    "For S3/SQS/SNS triggers, set require_request_context=False when creating the handler.",
                    "CONFIGURATION_ERROR",
                    500
                )
            
            # Load security from container if provided (NEW)
            if self.services_container:
                try:
                    self.services_container.load_security(event, context)
                    logger.debug("Security loaded from container", extra={
                        "user_id": self.services_container.current_user_id,
                        "tenant_id": self.services_container.current_tenant_id
                    })
                except Exception as e:
                    # Automatic error handling for authentication failures
                    logger.error(f"Security validation failed: {e}")
                    error_message = str(e)
                    
                    # Determine if this is auth or authz error
                    if "authentication" in error_message.lower() or "token" in error_message.lower():
                        return error_response(
                            "Authentication failed: " + error_message,
                            "AUTHENTICATION_ERROR",
                            401
                        )
                    elif "authorization" in error_message.lower() or "permission" in error_message.lower():
                        return error_response(
                            "Authorization failed: " + error_message,
                            "AUTHORIZATION_ERROR",
                            403
                        )
                    else:
                        return error_response(
                            "Security validation failed: " + error_message,
                            "SECURITY_ERROR",
                            403
                        )
            
            # Validate authentication if required (fallback for non-container handlers)
            if self.require_auth and not self.services_container:
                authorizer = event.get("requestContext", {}).get("authorizer")
                if not authorizer or not authorizer.get("claims", {}).get("custom:user_id"):
                    return error_response(
                        "Authentication required but not provided",
                        "AUTHENTICATION_REQUIRED",
                        401
                    )
            
            # Check if body is required
            if self.require_body and not event.get("body"):
                return error_response(
                    "Request body is required",
                    "VALIDATION_ERROR",
                    400
                )
            
            # Parse and validate body
            if event.get("body"):
                try:
                    body = LambdaEventUtility.get_body_from_event(event, raise_on_error=self.require_body)
                    # Convert camelCase → snake_case for Python backend (if requested)
                    if body and self.convert_request_case:
                        body = LambdaEventUtility.to_snake_case_for_backend(body)
                    if body:
                        event["parsed_body"] = body
                except (ValueError, KeyError) as e:
                    # If error handling is disabled, let the exception propagate for testing
                    if not self.apply_error_handling:
                        raise
                    return error_response(
                        str(e),
                        "VALIDATION_ERROR",
                        400
                    )
            
            # Extract user context from authorizer claims
            user_context = extract_user_context(event)
            
            # Create FRESH RequestContext for this invocation
            from geek_cafe_saas_sdk.core.request_context import RequestContext
            request_context = RequestContext(user_context)
            
            # Get service instance with FRESH request_context
            service = self._get_service(injected_service, request_context)
            
            # Determine response case conversion (can be overridden by client)
            convert_response = self._get_response_case_preference(event)
            
            # Wrap event in LambdaEvent for convenient parameter access
            from geek_cafe_saas_sdk.lambda_handlers._base.lambda_event import LambdaEvent
            lambda_event = LambdaEvent(event, config=self.config)
            
            # Execute business logic with container or user_context
            # Support both old and new signatures for backwards compatibility:
            # - New: (event: LambdaEvent, service)
            # - Old: (event: Dict, service, user_context) or (event: Dict, service, container)
            import inspect
            sig = inspect.signature(business_logic)
            param_count = len(sig.parameters)
            
            if param_count == 2:
                # New style: (event: LambdaEvent, service)
                result = business_logic(lambda_event, service)
            elif self.services_container:
                # Old style with container: (event, service, container)
                result = business_logic(lambda_event, service, self.services_container)
            else:
                # Old style with user_context: (event, service, user_context)
                result = business_logic(lambda_event, service, user_context)
            
            # Generate provenance headers if enabled
            provenance_headers = self._generate_provenance(event, user_context)
            
            # Determine appropriate HTTP status code based on HTTP method
            # ServiceResult.http_status takes precedence if set (for upserts, etc.)
            http_method = event.get('httpMethod', '').upper()
            if http_method == 'POST':
                default_success_status = 201  # Created or Updated
            elif http_method == 'DELETE':
                default_success_status = 204  # No Content
            else:
                default_success_status = 200  # OK (GET, PUT, PATCH, etc.)
            
            # Get fields to preserve from case conversion (e.g., metadata)
            preserve_fields = self._get_preserve_fields(event)
            
            # Format response - handle both ServiceResult and plain dict
            if hasattr(result, 'success'):
                # It's a ServiceResult object
                # Use result.http_status if set, otherwise use default based on HTTP method
                success_status = getattr(result, 'http_status', None) or default_success_status
                response = service_result_to_response(
                    result, 
                    success_status=success_status,
                    convert_to_camel_case=convert_response,
                    start_time=start_time,
                    preserve_fields=preserve_fields
                )
            else:
                # It's a plain dict - wrap it in a success response
                from geek_cafe_saas_sdk.utilities.response import success_response
                response = success_response(
                    result, 
                    default_success_status,
                    convert_to_camel_case=convert_response,
                    start_time=start_time,
                    preserve_fields=preserve_fields
                )
            
            # Add provenance headers to response
            if provenance_headers:
                response.setdefault('headers', {})
                response['headers'].update(provenance_headers)
            
            # Add any existing extra response headers
            extra_headers = event.get('extra_response_headers')
            if isinstance(extra_headers, dict) and extra_headers:
                response.setdefault('headers', {})
                response['headers'].update(extra_headers)

            # Note: CORS headers are already added by success_response/service_result_to_response
            # The apply_cors flag is for decorator usage, not runtime response modification
            return response
            
        except Exception as e:
            logger.exception(f"Handler execution error: {e}")
            if self.apply_error_handling:
                # Convert exception to error response (error_response is imported at top)
                return error_response(
                    str(e),
                    "INTERNAL_ERROR",
                    500
                )
            raise
        finally:
            # Track execution time for telemetry
            execution_time_ms = (time.time() - start_time) * 1000
            if self._service_pool and hasattr(self._service_pool, 'track_execution_time'):
                self._service_pool.track_execution_time(execution_time_ms)
            
            # SECURITY: Clear request_context after invocation completes
            # This ensures no lingering user credentials in warm Lambda containers
            if service and hasattr(service, '_request_context'):
                service._request_context = None
                logger.debug("Cleared request_context after invocation")
