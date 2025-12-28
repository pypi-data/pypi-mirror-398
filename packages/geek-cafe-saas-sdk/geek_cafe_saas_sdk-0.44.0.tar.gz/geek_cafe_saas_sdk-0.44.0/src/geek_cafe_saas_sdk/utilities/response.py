"""
Utility functions for creating standardized Lambda responses.
"""

import json
import time
from typing import Any, Dict, Optional, Set, Union, List
from datetime import datetime, UTC
from boto3_assist.utilities.serialization_utility import JsonConversions
from ..core.error_codes import ErrorCode
from .case_conversion import CaseFormat, CaseConverter


def json_snake_to_camel(
    payload: Union[List[Dict[str, Any]], Dict[str, Any], None],
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convert backend data from snake_case to camelCase for UI consumption.

    Args:
        payload: The backend data in snake_case format (dict or list of dicts)

    Returns:
        The payload converted to camelCase format, maintaining the same structure

    Raises:
        ValueError: If the payload is None
    """
    if payload is None:
        raise ValueError("Payload cannot be None")
    if not payload:
        return payload  # Return empty dict/list as-is

    return JsonConversions.json_snake_to_camel(payload)


def _resolve_case_format(
    convert_option: Union[bool, CaseFormat, str, None]
) -> Optional[CaseFormat]:
    """
    Resolve a case conversion option to a CaseFormat enum.
    
    Args:
        convert_option: Case conversion option. Can be:
            - True: Convert to camelCase
            - False: No conversion (keep as-is)
            - None: No conversion
            - CaseFormat enum: Use directly
            - str: Parse as case format name
            
    Returns:
        CaseFormat enum or None if no conversion should be applied
    """
    if convert_option is None or convert_option is False:
        return None
    
    if convert_option is True:
        return CaseFormat.CAMEL
    
    if isinstance(convert_option, CaseFormat):
        return convert_option
    
    if isinstance(convert_option, str):
        try:
            return CaseFormat.from_string(convert_option)
        except ValueError:
            # Unknown format, default to camelCase for backwards compatibility
            return CaseFormat.CAMEL
    
    # Default to camelCase
    return CaseFormat.CAMEL


def success_response(
    data: Any,
    status_code: int = 200,
    message: Optional[str] = None,
    convert_to_camel_case: Union[bool, CaseFormat, str] = True,
    start_time: Optional[float] = None,
    preserve_fields: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Create a successful API Gateway response with optional case conversion.

    Args:
        data: Response data to include in body
        status_code: HTTP status code (default: 200)
        message: Optional success message
        convert_to_camel_case: Case conversion option. Can be:
            - True: Convert to camelCase (default, backwards compatible)
            - False: Keep snake_case
            - CaseFormat enum: Convert to specified format
            - str: Case format name ("camel", "snake", "pascal", "kebab")
        start_time: Optional start time for diagnostics
        preserve_fields: Set of field names whose nested content should NOT have
            case conversion applied. The field name itself IS converted, but the
            nested content is preserved as-is. Useful for user-defined metadata.
            Example: preserve_fields={"metadata"} keeps metadata content unchanged.

    Returns:
        API Gateway response dictionary

    Example:
        # Default: Converts to camelCase for frontend
        success_response({"user_id": "123"})
        # Returns: {"data": {"userId": "123"}}

        # Opt-out: Keep snake_case
        success_response({"user_id": "123"}, convert_to_camel_case=False)
        # Returns: {"data": {"user_id": "123"}}
        
        # PascalCase for .NET clients
        success_response({"user_id": "123"}, convert_to_camel_case=CaseFormat.PASCAL)
        # Returns: {"data": {"UserId": "123"}}
        
        # kebab-case
        success_response({"user_id": "123"}, convert_to_camel_case="kebab")
        # Returns: {"data": {"user-id": "123"}}
        
        # Preserve metadata field content (no conversion inside metadata)
        success_response(
            {"user_id": "123", "metadata": {"column_name": "test"}},
            preserve_fields={"metadata"}
        )
        # Returns: {"data": {"userId": "123", "metadata": {"column_name": "test"}}}
    """
    # Determine target case format
    target_format = _resolve_case_format(convert_to_camel_case)
    
    # Convert data to target case format
    if target_format and data is not None and data != {}:
        ui_data = CaseConverter.convert_keys(data, target_format, preserve_fields=preserve_fields)
    else:
        ui_data = data

    body = {
        "data": ui_data,
        "timestamp": datetime.now(UTC).isoformat(),
        "status_code": status_code,
        "success": True,
    }

    if start_time:
        body["diagnostics"] = {
            "start_time": start_time,
            "end_time": time.time(),
            "duration": time.time() - start_time,
        }

    if message:
        body["message"] = message

    return {
        "statusCode": status_code,
        "headers": get_allowed_headers(),
        "body": json.dumps(body, default=str),
    }


def error_response(
    error: str, error_code: str, status_code: int = 400
) -> Dict[str, Any]:
    """
    Create an error API Gateway response.

    Args:
        error: Error message
        error_code: Standardized error code
        status_code: HTTP status code (default: 400)

    Returns:
        API Gateway response dictionary
    """

    body = {
        "error": error,
        "error_code": error_code,
        "timestamp": datetime.now(UTC).isoformat(),
        "status_code": status_code,
        "success": False,
    }

    body = json_snake_to_camel(body)

    return {
        "statusCode": status_code,
        "headers": get_allowed_headers(),
        "body": json.dumps(body, default=str),
    }


def validation_error_response(error: str, status_code: int = 400) -> Dict[str, Any]:
    """
    Create a validation error response.

    Args:
        error: Validation error message
        status_code: HTTP status code (default: 400)

    Returns:
        API Gateway response dictionary
    """
    return error_response(error, "VALIDATION_ERROR", status_code)


def service_result_to_response(
    result,
    success_status: int = 200,
    convert_to_camel_case: Union[bool, CaseFormat, str] = True,
    start_time: Optional[float] = None,
    sanitize_access_denied: bool = True,
    preserve_fields: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Convert a ServiceResult to an API Gateway response.

    Args:
        result: ServiceResult object from service layer
        success_status: HTTP status code for successful operations
        convert_to_camel_case: Case conversion option. Can be:
            - True: Convert to camelCase (default, backwards compatible)
            - False: Keep snake_case
            - CaseFormat enum: Convert to specified format
            - str: Case format name ("camel", "snake", "pascal", "kebab")
        start_time: Optional start time for diagnostics
        sanitize_access_denied: If True (default), converts ACCESS_DENIED errors
            to NOT_FOUND in the API response to prevent resource enumeration.
            Set to False for admin endpoints that need to show the real error.
        preserve_fields: Set of field names whose nested content should NOT have
            case conversion applied. The field name itself IS converted, but the
            nested content is preserved as-is. Useful for user-defined metadata.
            Example: preserve_fields={"metadata"} keeps metadata content unchanged.

    Returns:
        API Gateway response dictionary
        
    Security:
        By default, ACCESS_DENIED errors for resource access are converted to
        NOT_FOUND responses. This prevents attackers from enumerating valid
        resource IDs by checking which return 403 vs 404. The real error is
        logged internally for debugging/auditing.
    """
    if result.success:
        # Handle model serialization for different data types
        data = result.data
        if hasattr(data, "to_dictionary"):
            # Single model object
            data = data.to_dictionary()
        elif isinstance(data, list) and data and hasattr(data[0], "to_dictionary"):
            # List of model objects
            data = [item.to_dictionary() for item in data]

        return success_response(
            data,
            success_status,
            convert_to_camel_case=convert_to_camel_case,
            start_time=start_time,
            preserve_fields=preserve_fields,
        )
    else:
        # Determine the error code to use for the response
        response_error_code = result.error_code
        response_message = result.message
        
        # Security: Sanitize ACCESS_DENIED to NOT_FOUND to prevent enumeration
        # The real error is already logged by the service layer
        is_access_denied = (
            result.error_code == ErrorCode.ACCESS_DENIED or 
            result.error_code == "ACCESS_DENIED"
        )
        if sanitize_access_denied and is_access_denied:
            response_error_code = ErrorCode.NOT_FOUND
            response_message = "Resource not found"
        
        # Get HTTP status code from ErrorCode enum (or use default mapping)
        try:
            # Try to convert string error code to ErrorCode enum
            error_code_enum = (
                ErrorCode(response_error_code) if response_error_code else None
            )
            status_code = (
                ErrorCode.get_http_status(error_code_enum) if error_code_enum else 400
            )
        except ValueError:
            # Fallback for unknown error codes
            legacy_map = {
                "DUPLICATE_NAME": 409,
                "DUPLICATE_ITEM": 409,
                "GROUP_NOT_FOUND": 404,
            }
            status_code = legacy_map.get(response_error_code, 400)

        # Create structured error response with nested structure
        error_data = {
            "message": response_message,
            "code": response_error_code,
            "details": result.error_details if not (sanitize_access_denied and is_access_denied) else None,
        }

        body = {
            "error": error_data,
            "timestamp": datetime.now(UTC).isoformat(),
            "status_code": status_code,
            "success": False,
        }

        body = json_snake_to_camel(body)

        return {
            "statusCode": status_code,
            "headers": get_allowed_headers(),
            "body": json.dumps(body, default=str),
        }


def get_allowed_headers() -> Dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT",
    }

    return headers


def extract_path_parameters(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract path parameters from API Gateway event.

    Args:
        event: API Gateway event

    Returns:
        Dictionary of path parameters
    """
    return event.get("pathParameters") or {}


def extract_query_parameters(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract query string parameters from API Gateway event.

    Args:
        event: API Gateway event

    Returns:
        Dictionary of query parameters
    """
    return event.get("queryStringParameters") or {}
