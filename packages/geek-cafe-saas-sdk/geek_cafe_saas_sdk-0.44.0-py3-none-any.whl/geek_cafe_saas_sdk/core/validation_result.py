"""
Validation Result - Structured validation error handling.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class FieldError:
    """
    Details about a field validation error.
    
    Attributes:
        field: Field name that failed validation
        error_type: Type of error ('unknown', 'invalid_type', 'required', 'invalid_value')
        message: Human-readable error message
        expected: Optional expected value/type
        received: Optional received value/type
    """
    field: str
    error_type: str
    message: str
    expected: Optional[Any] = None
    received: Optional[Any] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        result = {
            'field': self.field,
            'type': self.error_type,
            'message': self.message
        }
        if self.expected is not None:
            result['expected'] = str(self.expected)
        if self.received is not None:
            result['received'] = str(self.received)
        return result


@dataclass
class ValidationResult:
    """
    Result of field validation.
    
    Attributes:
        is_valid: Whether validation passed
        errors: List of field errors
        warnings: List of warning messages
    """
    is_valid: bool
    errors: List[FieldError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @staticmethod
    def success(warnings: Optional[List[str]] = None) -> 'ValidationResult':
        """
        Create successful validation result.
        
        Args:
            warnings: Optional list of warnings
        
        Returns:
            ValidationResult with is_valid=True
        """
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=warnings or []
        )
    
    @staticmethod
    def failure(errors: List[FieldError], warnings: Optional[List[str]] = None) -> 'ValidationResult':
        """
        Create failed validation result.
        
        Args:
            errors: List of field errors
            warnings: Optional list of warnings
        
        Returns:
            ValidationResult with is_valid=False
        """
        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings or []
        )
    
    def to_error_message(self) -> str:
        """
        Convert to human-readable error message.
        
        Returns:
            Formatted error message string
        """
        if not self.errors:
            return ""
        
        lines = ["Field validation failed:"]
        
        for error in self.errors:
            if error.expected and error.received:
                lines.append(
                    f"  - {error.field}: {error.message} "
                    f"(expected: {error.expected}, received: {error.received})"
                )
            else:
                lines.append(f"  - {error.field}: {error.message}")
        
        if self.warnings:
            lines.append("\nWarnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for API responses.
        
        Returns:
            Dictionary with validation results
        """
        return {
            'is_valid': self.is_valid,
            'errors': [error.to_dict() for error in self.errors],
            'warnings': self.warnings
        }
    
    def add_error(self, field: str, error_type: str, message: str, 
                  expected: Optional[Any] = None, received: Optional[Any] = None) -> None:
        """
        Add a field error.
        
        Args:
            field: Field name
            error_type: Error type
            message: Error message
            expected: Optional expected value
            received: Optional received value
        """
        self.errors.append(FieldError(
            field=field,
            error_type=error_type,
            message=message,
            expected=expected,
            received=received
        ))
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """
        Add a warning message.
        
        Args:
            warning: Warning message
        """
        self.warnings.append(warning)
    
    def merge(self, other: 'ValidationResult') -> 'ValidationResult':
        """
        Merge another validation result into this one.
        
        Args:
            other: Another ValidationResult to merge
        
        Returns:
            Self for chaining
        """
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False
        return self
    
    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.is_valid
    
    def __repr__(self) -> str:
        """String representation."""
        status = "valid" if self.is_valid else "invalid"
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        return f"ValidationResult({status}, errors={error_count}, warnings={warning_count})"
