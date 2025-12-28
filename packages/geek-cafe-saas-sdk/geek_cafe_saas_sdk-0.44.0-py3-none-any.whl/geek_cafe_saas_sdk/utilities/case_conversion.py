"""
Case Conversion Utilities.

Provides functions to convert JSON keys between different case formats:
- snake_case (Python convention)
- camelCase (JavaScript/JSON convention)
- PascalCase (C#/.NET convention)
- kebab-case (URL/CSS convention)

Modeled after boto3_assist.utilities.serialization_utility.JsonConversions
but with support for additional case formats.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union


class CaseFormat(str, Enum):
    """Supported case formats for JSON key conversion."""
    SNAKE = "snake"      # snake_case
    CAMEL = "camel"      # camelCase
    PASCAL = "pascal"    # PascalCase
    KEBAB = "kebab"      # kebab-case
    
    @classmethod
    def from_string(cls, value: str) -> "CaseFormat":
        """
        Parse a case format from a string value.
        
        Accepts various aliases for each format:
        - snake: snake, snake_case, snakecase
        - camel: camel, camelCase, camelcase
        - pascal: pascal, PascalCase, pascalcase
        - kebab: kebab, kebab-case, kebabcase
        
        Args:
            value: String representation of case format
            
        Returns:
            CaseFormat enum value
            
        Raises:
            ValueError: If the value doesn't match any known format
        """
        if not value:
            raise ValueError("Case format value cannot be empty")
            
        normalized = value.lower().strip().replace("-", "").replace("_", "")
        
        if normalized in ("snake", "snakecase"):
            return cls.SNAKE
        elif normalized in ("camel", "camelcase"):
            return cls.CAMEL
        elif normalized in ("pascal", "pascalcase"):
            return cls.PASCAL
        elif normalized in ("kebab", "kebabcase"):
            return cls.KEBAB
        else:
            raise ValueError(f"Unknown case format: {value}")


class CaseConverter:
    """
    Utility class for converting strings and JSON structures between case formats.
    
    Usage:
        # Convert a single string
        CaseConverter.to_camel("user_name")  # "userName"
        CaseConverter.to_snake("userName")   # "user_name"
        CaseConverter.to_pascal("user_name") # "UserName"
        CaseConverter.to_kebab("userName")   # "user-name"
        
        # Convert all keys in a JSON structure
        data = {"user_name": "John", "created_at": "2024-01-01"}
        CaseConverter.convert_keys(data, CaseFormat.CAMEL)
        # {"userName": "John", "createdAt": "2024-01-01"}
    """
    
    # =========================================================================
    # String Conversion Methods
    # =========================================================================
    
    @staticmethod
    def to_snake(value: str) -> str:
        """
        Convert a string to snake_case.
        
        Args:
            value: String in any case format
            
        Returns:
            String in snake_case
            
        Examples:
            to_snake("userName") -> "user_name"
            to_snake("UserName") -> "user_name"
            to_snake("user-name") -> "user_name"
        """
        if not value:
            return value
        
        # Handle kebab-case first
        value = value.replace("-", "_")
        
        # Insert underscores before uppercase letters
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    
    @staticmethod
    def to_camel(value: str) -> str:
        """
        Convert a string to camelCase.
        
        Args:
            value: String in any case format
            
        Returns:
            String in camelCase
            
        Examples:
            to_camel("user_name") -> "userName"
            to_camel("UserName") -> "userName"
            to_camel("user-name") -> "userName"
        """
        if not value:
            return value
        
        # First convert to snake_case as intermediate
        snake = CaseConverter.to_snake(value)
        
        # Split by underscores and capitalize each component except the first
        components = snake.split("_")
        return components[0].lower() + "".join(x.title() for x in components[1:])
    
    @staticmethod
    def to_pascal(value: str) -> str:
        """
        Convert a string to PascalCase.
        
        Args:
            value: String in any case format
            
        Returns:
            String in PascalCase
            
        Examples:
            to_pascal("user_name") -> "UserName"
            to_pascal("userName") -> "UserName"
            to_pascal("user-name") -> "UserName"
        """
        if not value:
            return value
        
        # First convert to snake_case as intermediate
        snake = CaseConverter.to_snake(value)
        
        # Split by underscores and capitalize each component
        components = snake.split("_")
        return "".join(x.title() for x in components)
    
    @staticmethod
    def to_kebab(value: str) -> str:
        """
        Convert a string to kebab-case.
        
        Args:
            value: String in any case format
            
        Returns:
            String in kebab-case
            
        Examples:
            to_kebab("user_name") -> "user-name"
            to_kebab("userName") -> "user-name"
            to_kebab("UserName") -> "user-name"
        """
        if not value:
            return value
        
        # First convert to snake_case, then replace underscores with hyphens
        return CaseConverter.to_snake(value).replace("_", "-")
    
    @staticmethod
    def convert_string(value: str, target_format: CaseFormat) -> str:
        """
        Convert a string to the specified case format.
        
        Args:
            value: String to convert
            target_format: Target case format
            
        Returns:
            Converted string
        """
        if target_format == CaseFormat.SNAKE:
            return CaseConverter.to_snake(value)
        elif target_format == CaseFormat.CAMEL:
            return CaseConverter.to_camel(value)
        elif target_format == CaseFormat.PASCAL:
            return CaseConverter.to_pascal(value)
        elif target_format == CaseFormat.KEBAB:
            return CaseConverter.to_kebab(value)
        else:
            return value
    
    # =========================================================================
    # JSON Key Conversion Methods
    # =========================================================================
    
    @staticmethod
    def convert_keys(
        data: Union[Dict[str, Any], List[Any], Any],
        target_format: CaseFormat,
        deep: bool = True,
        preserve_fields: Optional[Set[str]] = None
    ) -> Union[Dict[str, Any], List[Any], Any]:
        """
        Convert all keys in a JSON structure to the specified case format.
        
        Args:
            data: JSON-like structure (dict, list, or primitive)
            target_format: Target case format for keys
            deep: If True, recursively convert nested structures (default: True)
            preserve_fields: Set of field names whose VALUES should not have their
                keys converted. The field name itself IS converted, but the nested
                content is preserved as-is. Useful for user-defined metadata.
                Matches both snake_case and camelCase versions of field names.
            
        Returns:
            Data structure with converted keys
            
        Examples:
            data = {"user_name": "John", "address_info": {"street_name": "Main"}}
            convert_keys(data, CaseFormat.CAMEL)
            # {"userName": "John", "addressInfo": {"streetName": "Main"}}
            
            # With preserve_fields - metadata content is NOT converted:
            data = {"user_name": "John", "metadata": {"column_name": "test"}}
            convert_keys(data, CaseFormat.CAMEL, preserve_fields={"metadata"})
            # {"userName": "John", "metadata": {"column_name": "test"}}
        """
        convert_func = lambda key: CaseConverter.convert_string(key, target_format)
        return CaseConverter._convert_keys_recursive(data, convert_func, deep, preserve_fields)
    
    @staticmethod
    def _convert_keys_recursive(
        data: Union[Dict[str, Any], List[Any], Any],
        convert_func,
        deep: bool = True,
        preserve_fields: Optional[Set[str]] = None
    ) -> Union[Dict[str, Any], List[Any], Any]:
        """
        Recursively convert dictionary keys using the provided function.
        
        Args:
            data: Input data (dict, list, or other)
            convert_func: Function to convert keys
            deep: If True, convert keys in nested structures
            preserve_fields: Set of field names whose values should not be converted
            
        Returns:
            Data with converted keys
        """
        if isinstance(data, dict):
            new_dict = {}
            for key, value in data.items():
                new_key = convert_func(key)
                
                # Check if this field's VALUE should be preserved (not converted)
                # Match against both original key and converted key
                should_preserve = False
                if preserve_fields:
                    # Check original key, converted key, and snake_case version
                    snake_key = CaseConverter.to_snake(key)
                    should_preserve = (
                        key in preserve_fields or
                        new_key in preserve_fields or
                        snake_key in preserve_fields
                    )
                
                if should_preserve:
                    # Preserve the value as-is (no conversion of nested keys)
                    new_dict[new_key] = value
                elif deep:
                    new_dict[new_key] = CaseConverter._convert_keys_recursive(
                        value, convert_func, deep, preserve_fields
                    )
                else:
                    new_dict[new_key] = value
            return new_dict
        elif isinstance(data, list):
            return [
                (
                    CaseConverter._convert_keys_recursive(item, convert_func, deep, preserve_fields)
                    if deep
                    else item
                )
                for item in data
            ]
        else:
            return data
    
    # =========================================================================
    # Convenience Methods (matching boto3_assist API)
    # =========================================================================
    
    @staticmethod
    def json_snake_to_camel(
        data: Union[Dict[str, Any], List[Any]],
        deep: bool = True
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Convert all keys from snake_case to camelCase.
        
        Matches boto3_assist.utilities.serialization_utility.JsonConversions API.
        
        Args:
            data: JSON-like structure
            deep: If True, convert nested structures
            
        Returns:
            Data with camelCase keys
        """
        return CaseConverter.convert_keys(data, CaseFormat.CAMEL, deep)
    
    @staticmethod
    def json_camel_to_snake(
        data: Union[Dict[str, Any], List[Any]],
        deep: bool = True
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Convert all keys from camelCase to snake_case.
        
        Matches boto3_assist.utilities.serialization_utility.JsonConversions API.
        
        Args:
            data: JSON-like structure
            deep: If True, convert nested structures
            
        Returns:
            Data with snake_case keys
        """
        return CaseConverter.convert_keys(data, CaseFormat.SNAKE, deep)
    
    @staticmethod
    def json_to_pascal(
        data: Union[Dict[str, Any], List[Any]],
        deep: bool = True
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Convert all keys to PascalCase.
        
        Args:
            data: JSON-like structure
            deep: If True, convert nested structures
            
        Returns:
            Data with PascalCase keys
        """
        return CaseConverter.convert_keys(data, CaseFormat.PASCAL, deep)
    
    @staticmethod
    def json_to_kebab(
        data: Union[Dict[str, Any], List[Any]],
        deep: bool = True
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Convert all keys to kebab-case.
        
        Args:
            data: JSON-like structure
            deep: If True, convert nested structures
            
        Returns:
            Data with kebab-case keys
        """
        return CaseConverter.convert_keys(data, CaseFormat.KEBAB, deep)
