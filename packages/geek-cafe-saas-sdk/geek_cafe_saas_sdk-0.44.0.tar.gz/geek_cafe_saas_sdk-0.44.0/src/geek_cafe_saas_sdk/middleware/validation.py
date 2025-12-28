"""
Request validation middleware for Lambda handlers.
"""

import json
import functools
from ..core.service_errors import ValidationError
from typing import Any, Callable, Dict, List, Optional


def validate_request_body(
    required_fields: Optional[List[str]] = None,
    optional_fields: Optional[List[str]] = None
) -> Callable:
    """
    Decorator that validates request body JSON and required fields.

    Args:
        required_fields: List of required field names in the request body
        optional_fields: List of optional field names (for documentation/validation)

    Returns:
        Decorated function that validates request body before calling handler
    """

    def decorator(handler: Callable) -> Callable:
        @functools.wraps(handler)
        def wrapper(
            event: Dict[str, Any], context: Any, *args, **kwargs
        ) -> Dict[str, Any]:
            
            def _create_error_response(error: str, error_code: str, message: str) -> Dict[str, Any]:
                """Helper to create consistent error responses."""
                return {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                    },
                    "body": json.dumps({
                        "error": error,
                        "error_code": error_code,
                        "message": message,
                    }),
                }

            # Get and parse request body
            body = event.get("body", "{}")
            
            try:
                parsed_body = json.loads(body) if isinstance(body, str) else body
                if parsed_body is None:
                    raise json.JSONDecodeError("Body is None", "", 0)
            except json.JSONDecodeError:
                return _create_error_response(
                    "Invalid JSON", 
                    "INVALID_JSON", 
                    "Request body must be valid JSON"
                )

            # Validate required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in parsed_body]
                if missing_fields:
                    field = missing_fields[0]  # Return first missing field
                    return _create_error_response(
                        f"Missing required field: {field}",
                        "MISSING_REQUIRED_FIELD",
                        f'The field "{field}" is required'
                    )

            # Add parsed body to event for handler use
            event["parsed_body"] = parsed_body

            # Call the original handler
            return handler(event, context, *args, **kwargs)

        return wrapper

    return decorator
