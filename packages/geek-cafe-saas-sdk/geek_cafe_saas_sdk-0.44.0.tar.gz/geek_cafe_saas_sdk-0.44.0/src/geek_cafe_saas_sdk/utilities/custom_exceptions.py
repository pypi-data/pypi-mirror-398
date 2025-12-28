"""Custom exceptions for the Geek Cafe SaaS Services application.
This module contains all custom exceptions used throughout the application.
"""

from .http_status_code import HttpStatusCodes


class Error(Exception):
    """Base class for exceptions in this module."""
    
    def __init__(self, message: str, status_code: int, details: str | None = None):
        """Initialize the base error class.
        
        Args:
            message: The error message
            status_code: HTTP status code
            details: Optional additional details
        """
        self.message = {
            "status_code": status_code,
            "message": message,
        }
        
        if details is not None:
            self.message["details"] = details
            
        super().__init__(self.message)


class DbFailures(Error):
    """Exception for database failures."""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            status_code=HttpStatusCodes.HTTP_422_UNEXPECTED_OUTCOME.value
        )


class UnknownUserException(Error):
    """Exception for unknown user errors."""
    
    def __init__(self, message: str = "Unknown User Exception. The user account is not valid"):
        super().__init__(
            message=message,
            status_code=HttpStatusCodes.HTTP_404_NOT_FOUND.value
        )


class UserAccountPermissionException(Error):
    """Exception for user permission errors."""
    
    def __init__(
        self,
        message: str = "You are not authorized for the requested action.",
        details: str | None = None,
    ):
        super().__init__(
            message=message,
            status_code=HttpStatusCodes.HTTP_403_FORBIDDEN.value,
            details=details
        )


class UserAccountSubscriptionException(Error):
    """Exception for user subscription errors."""
    
    def __init__(
        self,
        message: str = "User Subscription Exception. The user accounts subscription is not valid",
    ):
        super().__init__(
            message=message,
            status_code=HttpStatusCodes.HTTP_403_FORBIDDEN.value
        )


class SubscriptionException(Error):
    """Exception for organization subscription errors."""
    
    def __init__(
        self,
        message: str = "Organization Subscription Exception. The organizations accounts subscription is not valid",
    ):
        super().__init__(
            message=message,
            status_code=HttpStatusCodes.HTTP_403_FORBIDDEN.value
        )


class SecurityError(Error):
    """Exception for security-related errors."""
    
    def __init__(
        self,
        message: str = "You are not authorized to make this action.",
    ):
        super().__init__(
            message=message,
            status_code=HttpStatusCodes.HTTP_403_FORBIDDEN.value
        )


class TenancyStatusException(Error):
    """Exception for tenancy status errors."""
    
    def __init__(
        self,
        message: str = "Tenancy Exception. The organizations accounts is not active",
    ):
        super().__init__(
            message=message,
            status_code=HttpStatusCodes.HTTP_403_FORBIDDEN.value
        )


class SubscriptionDisabledException(Error):
    """Exception for disabled subscription errors."""
    
    def __init__(
        self,
        message: str = "Disabled Subscription Exception. The organizations subscription has been disabled.",
    ):
        super().__init__(
            message=message,
            status_code=HttpStatusCodes.HTTP_403_FORBIDDEN.value
        )


class UnknownParameterService(Error):
    """Exception for unknown parameter service errors."""
    
    def __init__(
        self,
        message: str = "An unknown parameter service has been requested",
    ):
        message = (
            f"{message} "
            f"Check the dose type and dose frequency configurations. "
            f"Expected configurations: Frequency=[single|steady-state]. Type=[ev|iv-bolus|iv-infusion]."
        )
        super().__init__(
            message=message,
            status_code=HttpStatusCodes.HTTP_404_NOT_FOUND.value
        )


class GeneralUserException(Error):
    """Exception for general user errors."""
    
    def __init__(
        self,
        message: str = "Unknown Error Occurred with user",
        code: int = HttpStatusCodes.HTTP_422_UNEXPECTED_OUTCOME.value,
    ):
        super().__init__(
            message=message,
            status_code=code
        )


class InvalidHttpMethod(Error):
    """Exception for invalid HTTP method errors."""
    
    def __init__(
        self,
        message: str = "Invalid Http Method",
        code: int = HttpStatusCodes.HTTP_422_UNEXPECTED_OUTCOME.value,
    ):
        super().__init__(
            message=message,
            status_code=code
        )


class InvalidRoutePath(Error):
    """Exception for invalid route path errors."""
    
    def __init__(self, message: str = "Invalid Route"):
        super().__init__(
            message=message,
            status_code=HttpStatusCodes.HTTP_404_NOT_FOUND.value
        )
