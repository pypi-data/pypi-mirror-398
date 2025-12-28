"""
Geek Cafe, LLC
MIT License. See Project Root for the license information.

Standardized error codes for all services.
"""

from enum import Enum


class ErrorCode(str, Enum):
    """
    Standardized error codes for all services.
    
    Error codes are organized by category and map to HTTP status code equivalents.
    Using an enum ensures type safety and consistency across all services.
    """
    
    # Input/Validation Errors (4xx equivalent)
    VALIDATION_ERROR = "VALIDATION_ERROR"              # Invalid input data
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"  # Specific validation failure
    INVALID_FORMAT = "INVALID_FORMAT"                  # Data format issues
    INVALID_PARAMETER = "INVALID_PARAMETER"            # Parameter value issues
    
    # Authorization Errors (403 equivalent)
    ACCESS_DENIED = "ACCESS_DENIED"                    # User lacks permission
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"  # Role-based denial
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"  # No auth token provided
    
    # Resource Errors (404 equivalent)
    NOT_FOUND = "NOT_FOUND"                            # Resource doesn't exist
    RESOURCE_DELETED = "RESOURCE_DELETED"              # Resource was soft-deleted
    
    # Conflict Errors (409 equivalent)
    ALREADY_EXISTS = "ALREADY_EXISTS"                  # Duplicate resource
    CONCURRENT_MODIFICATION = "CONCURRENT_MODIFICATION"  # Optimistic lock failure
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"            # General conflict
    
    # Database Errors (500 equivalent)
    DATABASE_ERROR = "DATABASE_ERROR"                  # Generic DB error
    DATABASE_SAVE_FAILED = "DATABASE_SAVE_FAILED"      # Save operation failed
    DATABASE_DELETE_FAILED = "DATABASE_DELETE_FAILED"  # Delete operation failed
    DATABASE_QUERY_FAILED = "DATABASE_QUERY_FAILED"    # Query operation failed
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"  # Connection issues
    
    # Service/Business Logic Errors (500 equivalent)
    INTERNAL_ERROR = "INTERNAL_ERROR"                  # Unexpected error
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"        # Dependency failure
    OPERATION_FAILED = "OPERATION_FAILED"              # Business logic failure
    
    # Batch/Bulk Operation Errors
    PARTIAL_FAILURE = "PARTIAL_FAILURE"                # Some items in batch failed
    BATCH_OPERATION_FAILED = "BATCH_OPERATION_FAILED"  # Entire batch failed
    
    # Rate Limiting / Throttling (429 equivalent)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"        # Too many requests
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"                  # Usage quota exceeded
    
    def __str__(self) -> str:
        """Return the error code value as string."""
        return self.value
    
    @classmethod
    def is_client_error(cls, code: 'ErrorCode') -> bool:
        """
        Check if error code represents a client error (4xx equivalent).
        
        Args:
            code: Error code to check
            
        Returns:
            True if client error, False otherwise
        """
        client_errors = {
            cls.VALIDATION_ERROR,
            cls.MISSING_REQUIRED_FIELD,
            cls.INVALID_FORMAT,
            cls.INVALID_PARAMETER,
            cls.ACCESS_DENIED,
            cls.INSUFFICIENT_PERMISSIONS,
            cls.AUTHENTICATION_REQUIRED,
            cls.NOT_FOUND,
            cls.RESOURCE_DELETED,
            cls.ALREADY_EXISTS,
            cls.CONCURRENT_MODIFICATION,
            cls.RESOURCE_CONFLICT,
            cls.RATE_LIMIT_EXCEEDED,
            cls.QUOTA_EXCEEDED,
        }
        return code in client_errors
    
    @classmethod
    def is_server_error(cls, code: 'ErrorCode') -> bool:
        """
        Check if error code represents a server error (5xx equivalent).
        
        Args:
            code: Error code to check
            
        Returns:
            True if server error, False otherwise
        """
        return not cls.is_client_error(code)
    
    @classmethod
    def get_http_status(cls, code: 'ErrorCode') -> int:
        """
        Get suggested HTTP status code for error code.
        
        Args:
            code: Error code
            
        Returns:
            HTTP status code (e.g., 400, 404, 500)
        """
        status_map = {
            cls.VALIDATION_ERROR: 400,
            cls.MISSING_REQUIRED_FIELD: 400,
            cls.INVALID_FORMAT: 400,
            cls.INVALID_PARAMETER: 400,
            cls.AUTHENTICATION_REQUIRED: 401,
            cls.ACCESS_DENIED: 403,
            cls.INSUFFICIENT_PERMISSIONS: 403,
            cls.NOT_FOUND: 404,
            cls.RESOURCE_DELETED: 410,  # Gone
            cls.ALREADY_EXISTS: 409,
            cls.CONCURRENT_MODIFICATION: 409,
            cls.RESOURCE_CONFLICT: 409,
            cls.RATE_LIMIT_EXCEEDED: 429,
            cls.QUOTA_EXCEEDED: 429,
        }
        return status_map.get(code, 500)  # Default to 500 for server errors
