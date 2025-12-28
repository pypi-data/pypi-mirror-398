"""
Field Transformer - Transforms incoming data fields to internal representation.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import base64
from typing import Dict, Any


class FieldTransformer:
    """
    Transforms incoming data fields to internal representation.
    
    Handles:
    - Base64 decoding (file_data -> data)
    - Data type conversions
    - Field normalization
    
    Transformers are specific to modules (files, versions, etc.) to keep
    transformation logic centralized but domain-aware.
    
    Example:
        >>> data = {'file_data': 'SGVsbG8gV29ybGQ=', 'name': 'test.txt'}
        >>> transformed = FieldTransformer.transform_for_file(data)
        >>> transformed['data']
        b'Hello World'
        >>> 'file_data' in transformed
        False
    """
    
    @staticmethod
    def transform_for_file(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform incoming file data.
        
        Transformations:
        - Decode base64 strings in 'data' field if needed
        
        Args:
            data: Incoming data dict
        
        Returns:
            Transformed data dict
        
        Raises:
            ValueError: If base64 decoding fails
        
        Example:
            >>> data = {
            ...     'name': 'document.pdf',
            ...     'data': 'SGVsbG8=',  # base64 for "Hello"
            ...     'mime_type': 'application/pdf'
            ... }
            >>> result = FieldTransformer.transform_for_file(data)
            >>> result['data']
            b'Hello'
        """
        transformed = data.copy()
        
        # Handle 'data' field - decode base64 strings if needed
        if 'data' in transformed:
            file_data = transformed['data']
            
            # Remove if None/empty
            if not file_data:
                del transformed['data']
            # If string, assume base64 and decode
            elif isinstance(file_data, str):
                try:
                    transformed['data'] = base64.b64decode(file_data)
                except Exception as e:
                    raise ValueError(f"Invalid base64 data: {str(e)}")
            # If already bytes, no transformation needed
            elif not isinstance(file_data, bytes):
                raise ValueError(f"data must be bytes or base64 string, got {type(file_data)}")
        
        return transformed
    
    @staticmethod
    def transform_for_version(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform incoming file version data.
        
        Transformations:
        - file_data (base64 string) -> data (bytes)
        
        Args:
            data: Incoming data dict
        
        Returns:
            Transformed data dict
        
        Raises:
            ValueError: If base64 decoding fails
        
        Example:
            >>> data = {
            ...     'file_id': 'file-123',
            ...     'file_data': 'SGVsbG8=',
            ...     'change_description': 'Updated version'
            ... }
            >>> result = FieldTransformer.transform_for_version(data)
            >>> result['data']
            b'Hello'
        """
        transformed = data.copy()
        
        # Handle base64 file data (same as file)
        if 'file_data' in transformed:
            file_data_b64 = transformed.pop('file_data')
            
            if file_data_b64:
                try:
                    transformed['data'] = base64.b64decode(file_data_b64)
                except Exception as e:
                    raise ValueError(f"Invalid base64 file_data: {str(e)}")
        
        return transformed
    
    @staticmethod
    def encode_response_data(data: Dict[str, Any], fields_to_encode: list = None) -> Dict[str, Any]:
        """
        Encode binary data in response to base64.
        
        Useful for API responses that need to send binary data as JSON.
        
        Args:
            data: Response data dict
            fields_to_encode: List of field names to base64 encode (default: ['data'])
        
        Returns:
            Data dict with binary fields base64 encoded
        
        Example:
            >>> response = {'data': b'Hello', 'name': 'test.txt'}
            >>> encoded = FieldTransformer.encode_response_data(response)
            >>> encoded['data']
            'SGVsbG8='
        """
        if fields_to_encode is None:
            fields_to_encode = ['data']
        
        result = data.copy()
        
        for field in fields_to_encode:
            if field in result and isinstance(result[field], bytes):
                result[field] = base64.b64encode(result[field]).decode('utf-8')
        
        return result
    
    @staticmethod
    def normalize_boolean(value: Any) -> bool:
        """
        Normalize various boolean representations to Python bool.
        
        Handles: 'true', 'false', '1', '0', 1, 0, True, False
        
        Args:
            value: Value to normalize
        
        Returns:
            Boolean value
        
        Example:
            >>> FieldTransformer.normalize_boolean('true')
            True
            >>> FieldTransformer.normalize_boolean('0')
            False
            >>> FieldTransformer.normalize_boolean(1)
            True
        """
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        return bool(value)
    
    @staticmethod
    def normalize_integer(value: Any, default: int = 0) -> int:
        """
        Normalize value to integer.
        
        Args:
            value: Value to normalize
            default: Default if conversion fails
        
        Returns:
            Integer value
        
        Example:
            >>> FieldTransformer.normalize_integer('42')
            42
            >>> FieldTransformer.normalize_integer('invalid', default=-1)
            -1
        """
        if isinstance(value, int):
            return value
        
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
