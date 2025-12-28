"""
Model Field Validator - Validates incoming data against model structure.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Set, Type
from geek_cafe_saas_sdk.core.validation_result import ValidationResult, FieldError
from boto3_assist.dynamodb.dynamodb_model_base import DynamoDBModelBase


class ModelFieldValidator:
    """
    Validates incoming data against a model's expected fields.
    
    Features:
    - Detects unknown fields (fields not in model)
    - Provides helpful error messages
    - Lists expected fields
    - Model-driven (no hardcoded field lists)
    
    Example:
        >>> validation = ModelFieldValidator.validate_fields(
        ...     data={'name': 'test.pdf', 'unknown_field': 'bad'},
        ...     model_class=File,
        ...     allow_extra=False
        ... )
        >>> if not validation.is_valid:
        ...     print(validation.to_error_message())
    """
    
    @staticmethod
    def get_model_fields(model_class: Type[DynamoDBModelBase], extras: Set[str] = None) -> Set[str]:
        """
        Get all expected field names from a model class.
        
        Uses the model's to_dictionary() method to get all fields, then adds any extras.
        
        Args:
            model_class: Model class to inspect
            extras: Optional set of extra fields to allow (e.g., 'data' for file uploads)
        
        Returns:
            Set of field names
        
        Example:
            >>> fields = ModelFieldValidator.get_model_fields(File, extras={'data'})
            >>> 'name' in fields
            True
            >>> 'data' in fields  # From extras
            True
        """
        fields = set()
        
        # Create an instance and use to_dictionary() to get all model fields
        # This reuses internal logic that knows about all properties and fields
        instance = model_class()
        _dict = instance.to_dictionary()
        for key in _dict:
            fields.add(key)
        
        # Add any extra fields if provided
        if extras:
            fields.update(extras)

        return fields
    
    @staticmethod
    def validate_fields(
        data: Dict[str, Any],
        model_class: Type[DynamoDBModelBase],
        allow_extra: bool = False,
        strict: bool = True,
        extras: Set[str] = set()
    ) -> ValidationResult:
        """
        Validate incoming data fields against model structure.
        
        Args:
            data: Incoming data dictionary
            model_class: Model class to validate against
            allow_extra: If True, allow extra fields (just warn). If False, error on extra fields.
            strict: If True, perform strict validation. If False, be more lenient.
        
        Returns:
            ValidationResult with any errors/warnings
        
        Example:
            >>> result = ModelFieldValidator.validate_fields(
            ...     data={'name': 'test.pdf', 'bad_field': 'oops'},
            ...     model_class=File,
            ...     allow_extra=False
            ... )
            >>> result.is_valid
            False
            >>> 'bad_field' in result.to_error_message()
            True
        """
        result = ValidationResult.success()
        
        # Get expected fields from model
        expected_fields = ModelFieldValidator.get_model_fields(model_class, extras)
        
        # Check for unknown fields
        incoming_fields = set(data.keys())
        unknown_fields = incoming_fields - expected_fields
        
        if unknown_fields:
            unknown_sorted = sorted(unknown_fields)
            
            if allow_extra:
                # Just warn
                result.add_warning(
                    f"Unknown fields will be ignored: {', '.join(unknown_sorted)}"
                )
            else:
                # Error for each unknown field
                for field in unknown_sorted:
                    result.add_error(
                        field=field,
                        error_type='unknown',
                        message=f"Unknown field '{field}' not supported by {model_class.__name__}",
                        expected=f"Supported fields: {', '.join(sorted(expected_fields))}",
                        received=field
                    )
        
        return result
    
    @staticmethod
    def get_supported_fields_message(model_class: Type[DynamoDBModelBase], extras: Set[str] = None) -> str:
        """
        Get human-readable message of supported fields.
        
        Args:
            model_class: Model class
            extras: Optional set of extra fields to include
        
        Returns:
            Message string
        
        Example:
            >>> msg = ModelFieldValidator.get_supported_fields_message(File, extras={'data'})
            >>> 'name' in msg
            True
        """
        fields = sorted(ModelFieldValidator.get_model_fields(model_class, extras))
        return f"Supported fields for {model_class.__name__}: {', '.join(fields)}"
    
    @staticmethod
    def get_supported_fields_list(model_class: Type[DynamoDBModelBase], extras: Set[str] = None) -> list:
        """
        Get list of supported fields for API responses.
        
        Args:
            model_class: Model class
            extras: Optional set of extra fields to include
        
        Returns:
            Sorted list of field names
        
        Example:
            >>> fields = ModelFieldValidator.get_supported_fields_list(File, extras={'data'})
            >>> isinstance(fields, list)
            True
            >>> 'name' in fields
            True
        """
        return sorted(ModelFieldValidator.get_model_fields(model_class, extras))
    
    @staticmethod
    def filter_to_known_fields(
        data: Dict[str, Any],
        model_class: Type[DynamoDBModelBase]
    ) -> Dict[str, Any]:
        """
        Filter data to only include known model fields.
        
        Useful when allow_extra=True and you want to strip unknown fields.
        
        Args:
            data: Incoming data dictionary
            model_class: Model class
        
        Returns:
            Dictionary with only known fields
        
        Example:
            >>> filtered = ModelFieldValidator.filter_to_known_fields(
            ...     data={'name': 'test.pdf', 'unknown': 'bad'},
            ...     model_class=File
            ... )
            >>> 'name' in filtered
            True
            >>> 'unknown' in filtered
            False
        """
        known_fields = ModelFieldValidator.get_model_fields(model_class)
        return {
            key: value
            for key, value in data.items()
            if key in known_fields
        }
