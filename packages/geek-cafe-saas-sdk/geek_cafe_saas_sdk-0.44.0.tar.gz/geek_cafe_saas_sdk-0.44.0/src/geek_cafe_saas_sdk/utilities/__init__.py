"""
Utilities package for geek-cafe-services.

This package contains utility functions and helpers that can be reused
across multiple Lambda functions and services.
"""

from .response import (
    success_response,
    error_response,
    validation_error_response,
    service_result_to_response,
    json_snake_to_camel,
    extract_path_parameters,
    extract_query_parameters,
)

from .custom_exceptions import (
    Error,
    DbFailures,
    UnknownUserException,
    UserAccountPermissionException,
    UserAccountSubscriptionException,
    SubscriptionException,
    SecurityError,
    TenancyStatusException,
    SubscriptionDisabledException,
    UnknownParameterService,
    GeneralUserException,
    InvalidHttpMethod,
    InvalidRoutePath,
)

from .http_status_code import HttpStatusCodes

from .environment_loader import (
    EnvironmentLoader,
)
from .environment_variables import (
    EnvironmentVariables,
)

from .lambda_event_utility import LambdaEventUtility
from .jwt_utility import JwtUtility

from .http_body_parameters import HttpBodyParameters
from .http_path_parameters import HttpPathParameters

__all__ = [
    # Response utilities
    "success_response",
    "error_response", 
    "validation_error_response",
    "service_result_to_response",
    "json_snake_to_camel",
    "extract_path_parameters",
    "extract_query_parameters",
    
    # Custom exceptions
    "Error",
    "DbFailures",
    "UnknownUserException",
    "UserAccountPermissionException",
    "UserAccountSubscriptionException",
    "SubscriptionException",
    "SecurityError",
    "TenancyStatusException",
    "SubscriptionDisabledException",
    "UnknownParameterService",
    "GeneralUserException",
    "InvalidHttpMethod",
    "InvalidRoutePath",
    
    # HTTP status codes
    "HttpStatusCodes",
    
    # Environment services
    "EnvironmentLoader",
    "EnvironmentVariables",
    
    # Lambda event utilities
    "LambdaEventUtility",
    "JwtUtility",
    
    # HTTP parameter utilities
    "HttpBodyParameters",
    "HttpPathParameters",
]
