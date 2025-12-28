"""
Core Lambda lambda_handler decorators for common cross-cutting concerns.

These decorators handle:
- Error handling and standardized error responses
- CORS headers
- Request body parsing and case conversion
- Service injection with pooling
- Path parameter validation
- User context extraction
- Execution logging
"""

import json
import time
import functools
from typing import Callable, Any, Dict, Optional, Type, List
from aws_lambda_powertools import Logger

from geek_cafe_saas_sdk.utilities.response import error_response, success_response
from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility
from geek_cafe_saas_sdk.middleware.auth import extract_user_context
from geek_cafe_saas_sdk.lambda_handlers._base.service_pool import ServicePool

logger = Logger()


def handle_errors(lambda_handler: Callable) -> Callable:
    """
    Catch exceptions and return standardized error responses.
    
    Converts Python exceptions into API Gateway-compatible error responses
    with appropriate status codes and error messages.
    
    Usage:
        @handle_errors
        def lambda_handler(event, context):
            # Any exception becomes a 500 response
            raise ValueError("Something went wrong")
    
    Returns:
        Decorated lambda_handler that catches exceptions
    """
    @functools.wraps(lambda_handler)
    def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
        try:
            return lambda_handler(event, context, *args, **kwargs)
        except ValueError as e:
            # Validation errors -> 400
            logger.warning(f"Validation error: {e}")
            return error_response(str(e), "VALIDATION_ERROR", 400)
        except PermissionError as e:
            # Permission errors -> 403
            logger.warning(f"Permission error: {e}")
            return error_response(str(e), "PERMISSION_DENIED", 403)
        except KeyError as e:
            # Missing required field -> 400
            logger.warning(f"Missing field: {e}")
            return error_response(f"Missing required field: {str(e)}", "MISSING_FIELD", 400)
        except Exception as e:
            # Unexpected errors -> 500
            logger.exception(f"Unexpected error in lambda_handler: {e}")
            return error_response(
                "An unexpected error occurred",
                "INTERNAL_ERROR",
                500
            )
    return wrapper


def add_cors(
    allow_origin: str = "*",
    allow_methods: str = "GET,POST,PUT,DELETE,OPTIONS",
    allow_headers: str = "Content-Type,Authorization,X-Api-Key"
) -> Callable:
    """
    Add CORS headers to response.
    
    Args:
        allow_origin: Allowed origins (default: "*")
        allow_methods: Allowed HTTP methods
        allow_headers: Allowed headers
    
    Usage:
        @add_cors()
        def lambda_handler(event, context):
            return {'statusCode': 200, 'body': '{}'}
        
        # Custom CORS
        @add_cors(allow_origin="https://example.com")
        def lambda_handler(event, context):
            return {'statusCode': 200, 'body': '{}'}
    
    Returns:
        Decorated lambda_handler with CORS headers
    """
    def decorator(lambda_handler: Callable) -> Callable:
        @functools.wraps(lambda_handler)
        def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
            response = lambda_handler(event, context, *args, **kwargs)
            
            # Ensure headers dict exists
            if 'headers' not in response:
                response['headers'] = {}
            
            # Add CORS headers
            response['headers']['Access-Control-Allow-Origin'] = allow_origin
            response['headers']['Access-Control-Allow-Methods'] = allow_methods
            response['headers']['Access-Control-Allow-Headers'] = allow_headers
            
            return response
        return wrapper
    return decorator


def parse_request_body(
    required: bool = False,
    convert_to_snake_case: bool = True
) -> Callable:
    """
    Parse request body from JSON and optionally convert case.
    
    Parses event['body'] as JSON and adds it to event['parsed_body'].
    Optionally converts camelCase to snake_case for backend processing.
    
    Args:
        required: If True, returns 400 error if body is missing
        convert_to_snake_case: If True, converts camelCase keys to snake_case (default: True)
    
    Usage:
        @parse_request_body(required=True)
        def lambda_handler(event, context):
            payload = event['parsed_body']
            return {'statusCode': 200, 'body': json.dumps(payload)}
    
    Returns:
        Decorated lambda_handler with parsed body in event['parsed_body']
    """
    def decorator(lambda_handler: Callable) -> Callable:
        @functools.wraps(lambda_handler)
        def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
            # Check if body is required
            if required and not event.get('body'):
                return error_response(
                    "Request body is required",
                    "MISSING_BODY",
                    400
                )
            
            # Parse body if present
            if event.get('body'):
                try:
                    body = LambdaEventUtility.get_body_from_event(event, raise_on_error=required)
                    
                    # Convert camelCase → snake_case for Python backend
                    if body and convert_to_snake_case:
                        body = LambdaEventUtility.to_snake_case_for_backend(body)
                    
                    if body:
                        event['parsed_body'] = body
                        
                except (ValueError, json.JSONDecodeError) as e:
                    logger.warning(f"Failed to parse request body: {e}")
                    return error_response(
                        "Invalid JSON in request body",
                        "INVALID_JSON",
                        400
                    )
            
            return lambda_handler(event, context, *args, **kwargs)
        return wrapper
    return decorator


def inject_service(
    service_class: Type,
    param_name: str = "service",
    use_pooling: bool = True,
    **service_kwargs
) -> Callable:
    """
    Inject service instance into lambda_handler.
    
    Creates and injects a service instance, optionally using connection pooling.
    The service is passed as a keyword argument to the lambda_handler.
    
    Args:
        service_class: Service class to instantiate
        param_name: Parameter name to inject (default: "service")
        use_pooling: Use connection pooling (default: True)
        **service_kwargs: Additional arguments for service constructor
    
    Usage:
        @inject_service(MessageService)
        def lambda_handler(event, context, service):
            return service.get_by_id(message_id)
        
        # Custom parameter name
        @inject_service(MessageService, param_name="msg_service")
        def lambda_handler(event, context, msg_service):
            return msg_service.get_by_id(message_id)
    
    Returns:
        Decorated lambda_handler with service injected
    """
    # Initialize service pool if using pooling
    if use_pooling:
        service_pool = ServicePool(service_class, **service_kwargs)
    
    def decorator(lambda_handler: Callable) -> Callable:
        @functools.wraps(lambda_handler)
        def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
            # Get service from pool or create new instance
            if use_pooling:
                service = service_pool.get()
            else:
                service = service_class(**service_kwargs)
            
            # Inject service as keyword argument
            kwargs[param_name] = service
            
            return lambda_handler(event, context, *args, **kwargs)
        return wrapper
    return decorator


def log_execution(
    log_request: bool = True,
    log_response: bool = False,
    log_duration: bool = True
) -> Callable:
    """
    Log lambda_handler execution details.
    
    Logs request/response details and execution duration for monitoring
    and debugging purposes.
    
    Args:
        log_request: Log incoming request details
        log_response: Log response details (be careful with sensitive data)
        log_duration: Log execution duration
    
    Usage:
        @log_execution(log_response=True)
        def lambda_handler(event, context):
            return {'statusCode': 200, 'body': '{}'}
    
    Returns:
        Decorated lambda_handler with execution logging
    """
    def decorator(lambda_handler: Callable) -> Callable:
        @functools.wraps(lambda_handler)
        def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
            start_time = time.time()
            
            if log_request:
                logger.info(
                    "Handler execution started",
                    extra={
                        'function_name': context.function_name if context else 'unknown',
                        'http_method': event.get('httpMethod'),
                        'path': event.get('path'),
                        'request_id': context.aws_request_id if context else 'unknown'
                    }
                )
            
            # Execute lambda_handler
            response = lambda_handler(event, context, *args, **kwargs)
            
            duration = time.time() - start_time
            
            if log_duration:
                logger.info(
                    "Handler execution completed",
                    extra={
                        'duration_ms': round(duration * 1000, 2),
                        'status_code': response.get('statusCode')
                    }
                )
            
            if log_response:
                logger.debug(
                    "Response details",
                    extra={
                        'status_code': response.get('statusCode'),
                        'has_body': 'body' in response
                    }
                )
            
            return response
        return wrapper
    return decorator


def validate_path_params(required_params: List[str]) -> Callable:
    """
    Validate that required path parameters are present.
    
    Args:
        required_params: List of required path parameter names
    
    Usage:
        @validate_path_params(['tenant_id', 'user_id', 'message_id'])
        def lambda_handler(event, context):
            # All required params guaranteed to exist
            message_id = event['pathParameters']['message_id']
            return {'statusCode': 200}
    
    Returns:
        Decorated lambda_handler with validated path parameters
    """
    def decorator(lambda_handler: Callable) -> Callable:
        @functools.wraps(lambda_handler)
        def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
            path_params = event.get('pathParameters', {})
            
            # Check for missing parameters
            missing_params = [
                param for param in required_params
                if not path_params.get(param)
            ]
            
            if missing_params:
                return error_response(
                    f"Missing required path parameters: {', '.join(missing_params)}",
                    "MISSING_PATH_PARAMS",
                    400
                )
            
            return lambda_handler(event, context, *args, **kwargs)
        return wrapper
    return decorator


def extract_user_context_decorator(lambda_handler: Callable) -> Callable:
    """
    Extract user context from JWT and add to event.
    
    Extracts user context from API Gateway authorizer and adds it to
    event['user_context'] for easy access in lambda_handler.
    
    Usage:
        @extract_user_context_decorator
        def lambda_handler(event, context):
            user_id = event['user_context']['user_id']
            tenant_id = event['user_context']['tenant_id']
            return {'statusCode': 200}
    
    Returns:
        Decorated lambda_handler with user_context in event
    """
    @functools.wraps(lambda_handler)
    def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
        # Extract user context from authorizer
        user_context = extract_user_context(event)
        event['user_context'] = user_context
        
        return lambda_handler(event, context, *args, **kwargs)
    return wrapper
