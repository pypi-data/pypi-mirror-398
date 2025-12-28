"""
Service decorators for standardized error handling and validation.

Provides reusable decorators to reduce boilerplate in service methods
following DRY and Single Responsibility principles.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from functools import wraps
from typing import Callable, Any, Set, Optional
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.core.error_codes import ErrorCode


def service_method(operation_name: Optional[str] = None):
    """
    Decorator for standardized error handling in service methods.
    
    Automatically wraps service methods with consistent exception handling,
    converting known exceptions to appropriate ServiceResult error responses.
    
    Args:
        operation_name: Operation name for error context (defaults to method name)
    
    Returns:
        Decorated function with error handling
    
    Example:
        >>> @service_method("get_by_id")
        >>> def get_by_id(self, *, resource_id: str):
        >>>     # Just business logic - no try/except needed
        >>>     file = self._get_model_by_id(resource_id)
        >>>     if not file:
        >>>         raise NotFoundError(f"File not found: {resource_id}")
        >>>     return ServiceResult.success_result(file)
    
    Handles:
        - ValidationError → VALIDATION_ERROR
        - NotFoundError → NOT_FOUND
        - AccessDeniedError → ACCESS_DENIED
        - Exception → INTERNAL_ERROR (with full stack trace)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            
            except ValidationError as e:
                return ServiceResult.error_result(
                    message=str(e),
                    error_code=ErrorCode.VALIDATION_ERROR,
                    error_details=getattr(e, 'details', None)
                )
            
            except NotFoundError as e:
                return ServiceResult.error_result(
                    message=str(e),
                    error_code=ErrorCode.NOT_FOUND
                )
            
            except AccessDeniedError as e:
                return ServiceResult.error_result(
                    message=str(e),
                    error_code=ErrorCode.ACCESS_DENIED
                )
            
            except Exception as e:
                # Get operation name from decorator param or function name
                op_name = operation_name or func.__name__
                context = f"{self.__class__.__name__}.{op_name}"
                
                return ServiceResult.exception_result(
                    exception=e,
                    error_code=ErrorCode.INTERNAL_ERROR,
                    context=context
                )
        
        return wrapper
    return decorator


def require_params(*required_keys: str):
    """
    Decorator to validate required parameters in **kwargs.
    
    Checks that all specified keys are present and not None before
    executing the method. Returns validation error if any are missing.
    
    Args:
        *required_keys: Parameter keys that must be present
    
    Returns:
        Decorated function with parameter validation
    
    Example:
        >>> @require_params('resource_id')
        >>> def get_by_id(self, **kwargs):
        >>>     resource_id = kwargs['resource_id']  # Guaranteed to exist
        >>>     # ... rest of method
    
    Note:
        Use this for backwards compatibility with **kwargs pattern.
        For new code, prefer explicit parameters:
        
        >>> def get_by_id(self, *, resource_id: str, **kwargs):
        >>>     # Type hints work, IDE autocomplete, self-documenting
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Check for missing required parameters
            missing = [
                key for key in required_keys 
                if key not in kwargs or kwargs[key] is None
            ]
            
            if missing:
                return ServiceResult.error_result(
                    message=f"Missing required parameters: {', '.join(missing)}",
                    error_code=ErrorCode.VALIDATION_ERROR,
                    error_details={'missing_params': missing}
                )
            
            return func(self, *args, **kwargs)
        
        return wrapper
    return decorator


def validate_enum(param_name: str, valid_values: Set[str], case_sensitive: bool = False):
    """
    Decorator to validate that a parameter is one of a set of valid values.
    
    Args:
        param_name: Name of the parameter to validate
        valid_values: Set of valid values
        case_sensitive: Whether comparison is case-sensitive
    
    Returns:
        Decorated function with enum validation
    
    Example:
        >>> @validate_enum('permission', {'view', 'download', 'edit'})
        >>> def create_share(self, *, permission: str, **kwargs):
        >>>     # permission guaranteed to be valid
        >>>     ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            value = kwargs.get(param_name)
            
            if value is None:
                return func(self, *args, **kwargs)
            
            # Normalize for comparison if case-insensitive
            compare_value = value if case_sensitive else str(value).lower()
            compare_set = valid_values if case_sensitive else {v.lower() for v in valid_values}
            
            if compare_value not in compare_set:
                return ServiceResult.error_result(
                    message=f"Invalid {param_name}: '{value}'. Must be one of: {', '.join(sorted(valid_values))}",
                    error_code=ErrorCode.VALIDATION_ERROR,
                    error_details={
                        'param': param_name,
                        'value': value,
                        'valid_values': sorted(valid_values)
                    }
                )
            
            return func(self, *args, **kwargs)
        
        return wrapper
    return decorator


def require_ownership(resource_param: str = 'resource_id', user_param: str = 'user_id'):
    """
    Decorator to enforce that user owns the resource.
    
    Checks that the resource owner_id matches the requesting user_id.
    Assumes the service has already fetched the resource.
    
    Args:
        resource_param: Name of parameter containing the resource
        user_param: Name of parameter containing the user ID
    
    Returns:
        Decorated function with ownership validation
    
    Example:
        >>> @require_ownership(resource_param='file')
        >>> def update_file(self, *, file: File, **kwargs):
        >>>     # Ownership already validated
        >>>     ...
    
    Note:
        This is less useful with RequestContext pattern since we
        typically validate inline. Kept for backwards compatibility.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            resource = kwargs.get(resource_param)
            user_id = kwargs.get(user_param)
            
            if resource and user_id:
                if hasattr(resource, 'owner_id') and resource.owner_id != user_id:
                    return ServiceResult.error_result(
                        message="You do not have permission to access this resource",
                        error_code=ErrorCode.ACCESS_DENIED
                    )
            
            return func(self, *args, **kwargs)
        
        return wrapper
    return decorator


def cache_result(ttl_seconds: int = 60):
    """
    Decorator to cache service method results.
    
    Simple in-memory cache for expensive operations. Cache key is based
    on method name and stringified arguments.
    
    Args:
        ttl_seconds: Time-to-live for cached results
    
    Returns:
        Decorated function with result caching
    
    Example:
        >>> @cache_result(ttl_seconds=300)
        >>> def get_expensive_data(self, *, user_id: str):
        >>>     # Expensive operation cached for 5 minutes
        >>>     ...
    
    Note:
        Use sparingly and only for truly expensive, read-only operations.
        Cache is per-instance, so won't persist across Lambda invocations.
    """
    import time
    from typing import Dict, Tuple, Any
    
    # Cache storage: {cache_key: (result, expiration_time)}
    cache: Dict[str, Tuple[Any, float]] = {}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Check cache
            now = time.time()
            if cache_key in cache:
                result, expiration = cache[cache_key]
                if now < expiration:
                    return result
            
            # Execute function
            result = func(self, *args, **kwargs)
            
            # Cache successful results only
            if isinstance(result, ServiceResult) and result.success:
                cache[cache_key] = (result, now + ttl_seconds)
            
            return result
        
        return wrapper
    return decorator
