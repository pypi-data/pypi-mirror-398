"""
LambdaEvent wrapper for convenient event parameter extraction.

Provides clean, type-safe access to Lambda event parameters with
built-in type conversion and validation.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional, TypeVar, Callable, List, Union


T = TypeVar('T')


class LambdaEvent:
    """
    Wrapper for AWS Lambda event with convenient accessor methods.
    
    Reduces boilerplate in handlers by centralizing parameter extraction,
    type conversion, and default handling.
    
    Example:
        >>> event = LambdaEvent(raw_event)
        >>> file_id = event.path("fileId", "id")  # Try both keys
        >>> limit = event.query_int("limit", default=50)
        >>> hard_delete = event.query_bool("hardDelete")
        >>> payload = event.body()
    """
    
    def __init__(self, raw_event: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """
        Initialize event wrapper.
        
        Args:
            raw_event: Raw Lambda event dictionary from API Gateway
            config: Optional configuration dictionary for external values
                   (e.g., bucket names, feature flags, environment-specific settings)
        
        Example:
            >>> config = {"upload_bucket": "my-uploads", "max_file_size": 10485760}
            >>> event = LambdaEvent(raw_event, config=config)
            >>> bucket = event.config("upload_bucket")
        """
        self._event = raw_event
        self._config = config or {}
    
    # ========================================
    # Path Parameters
    # ========================================
    
    def path(self, *keys: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get path parameter, trying multiple keys in order.  The path key is the key you define
        in your route in API Gateway.  It must match the key you define in your route and is case-sensitive.
        
        Useful for handlers that accept multiple parameter names
        (e.g., "file-id", "fileId" or "id").
        
        Args:
            *keys: Parameter keys to try in order
            default: Default value if none found
        
        Returns:
            First matching parameter value or default
        
        Example:
            >>> event.path("file-id", "fileId", "id")  # Try fileId first, then id
            >>> event.path("user-id","user-id", "userId", default="anonymous")
        """
        params = self._event.get("pathParameters") or {}
        for key in keys:
            if key in params and params[key] is not None:
                return params[key]
        return default
    
    def path_required(self, *keys: str) -> str:
        """
        Get required path parameter, raising error if missing.
        
        Args:
            *keys: Parameter keys to try in order
        
        Returns:
            First matching parameter value
        
        Raises:
            ValueError: If no matching parameter found
        
        Example:
            >>> event.path_required("file-id", "fileId", "id")
        """
        value = self.path(*keys)
        if value is None:
            raise ValueError(f"Missing required path parameter: {' or '.join(keys)}")
        return value
    
    # ========================================
    # Query Parameters
    # ========================================
    
    def query(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get query string parameter.
        
        Args:
            key: Parameter key
            default: Default value if not found
        
        Returns:
            Parameter value or default
        
        Example:
            >>> event.query("search")
            >>> event.query("filter", default="all")
        """
        params = self._event.get("queryStringParameters") or {}
        return params.get(key, default)
    
    def query_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """
        Get query parameter as integer.
        
        Args:
            key: Parameter key
            default: Default value if not found
        
        Returns:
            Integer value or default
        
        Raises:
            ValueError: If value cannot be converted to int
        
        Example:
            >>> event.query_int("limit", default=50)
            >>> event.query_int("page", default=1)
        """
        value = self.query(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Invalid integer value for '{key}': {value}")
    
    def query_bool(self, key: str, default: bool = False) -> bool:
        """
        Get query parameter as boolean.
        
        Accepts: 'true', 'false', '1', '0', 'yes', 'no' (case-insensitive).
        
        Args:
            key: Parameter key
            default: Default value if not found
        
        Returns:
            Boolean value or default
        
        Example:
            >>> event.query_bool("hardDelete")
            >>> event.query_bool("includeDeleted", default=False)
        """
        value = self.query(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def query_list(self, key: str, separator: str = ',', default: Optional[List[str]] = None) -> List[str]:
        """
        Get query parameter as list by splitting on separator.
        
        Args:
            key: Parameter key
            separator: Separator character (default: comma)
            default: Default value if not found
        
        Returns:
            List of values or default
        
        Example:
            >>> event.query_list("tags")  # "tag1,tag2,tag3" → ["tag1", "tag2", "tag3"]
            >>> event.query_list("ids", separator="|")
        """
        value = self.query(key)
        if value is None:
            return default or []
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    def query_all(self) -> Dict[str, str]:
        """
        Get all query string parameters.
        
        Returns:
            Dictionary of all query parameters
        
        Example:
            >>> params = event.query_all()
        """
        return self._event.get("queryStringParameters") or {}
    
    # ========================================
    # Request Body
    # ========================================
    
    def body(self) -> Dict[str, Any]:
        """
        Get parsed request body.
        
        Body should already be parsed by handler wrapper
        (JSON parsing, base64 decoding, case conversion, etc.).
        
        Returns:
            Parsed body dictionary
        
        Example:
            >>> payload = event.body()
            >>> name = payload.get("name")
        """
        return self._event.get("parsed_body") or {}
    
    def body_raw(self) -> Optional[str]:
        """
        Get raw request body (before parsing).
        
        Returns:
            Raw body string
        
        Example:
            >>> raw = event.body_raw()
        """
        return self._event.get("body")
    
    # ========================================
    # Headers
    # ========================================
    
    def header(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get request header (case-insensitive).
        
        Args:
            key: Header name
            default: Default value if not found
        
        Returns:
            Header value or default
        
        Example:
            >>> event.header("Content-Type")
            >>> event.header("Authorization")
        """
        headers = self._event.get("headers") or {}
        # Headers are case-insensitive in HTTP
        key_lower = key.lower()
        for header_key, value in headers.items():
            if header_key.lower() == key_lower:
                return value
        return default
    
    def headers_all(self) -> Dict[str, str]:
        """
        Get all request headers.
        
        Returns:
            Dictionary of all headers
        
        Example:
            >>> headers = event.headers_all()
        """
        return self._event.get("headers") or {}
    
    # ========================================
    # Request Context
    # ========================================
    
    def request_context(self, key: Optional[str] = None) -> Any:
        """
        Get request context or specific key from context.
        
        Args:
            key: Optional specific key to retrieve
        
        Returns:
            Request context or specific value
        
        Example:
            >>> event.request_context("requestId")
            >>> event.request_context("authorizer")
        """
        context = self._event.get("requestContext") or {}
        if key is None:
            return context
        return context.get(key)
    
    # ========================================
    # Raw Event Access
    # ========================================
    
    @property
    def raw(self) -> Dict[str, Any]:
        """
        Access raw Lambda event dictionary.
        
        Use this for any fields not covered by convenience methods.
        
        Returns:
            Raw event dictionary
        
        Example:
            >>> raw_event = event.raw
            >>> custom_field = event.raw.get("customField")
        """
        return self._event
    
    # ========================================
    # Configuration
    # ========================================
    
    def config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Configuration allows external consumers to inject runtime values
        like bucket names, feature flags, or environment-specific settings.
        
        Args:
            key: Configuration key
            default: Default value if not found
        
        Returns:
            Configuration value or default
        
        Example:
            >>> # In consumer/invoker code:
            >>> config = {
            ...     "upload_bucket": "my-uploads-bucket",
            ...     "download_bucket": "my-downloads-bucket",
            ...     "max_file_size": 104857600
            ... }
            >>> event = LambdaEvent(raw_event, config=config)
            >>> 
            >>> # In handler code:
            >>> bucket = event.config("upload_bucket")
            >>> max_size = event.config("max_file_size", default=100*1024*1024)
        """
        return self._config.get(key, default)
    
    def config_required(self, key: str) -> Any:
        """
        Get required configuration value, raising error if missing.
        
        Args:
            key: Configuration key
        
        Returns:
            Configuration value
        
        Raises:
            ValueError: If configuration key not found
        
        Example:
            >>> bucket = event.config_required("upload_bucket")
        """
        if key not in self._config:
            raise ValueError(f"Missing required configuration: {key}")
        return self._config[key]
    
    def config_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Dictionary of all configuration
        
        Example:
            >>> config = event.config_all()
        """
        return self._config.copy()
    
    def has_config(self, key: str) -> bool:
        """
        Check if configuration key exists.
        
        Args:
            key: Configuration key
        
        Returns:
            True if key exists in configuration
        
        Example:
            >>> if event.has_config("upload_bucket"):
            ...     bucket = event.config("upload_bucket")
        """
        return key in self._config
    
    # ========================================
    # Utility Methods
    # ========================================
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get any top-level event field.
        
        Args:
            key: Field key
            default: Default value if not found
        
        Returns:
            Field value or default
        
        Example:
            >>> event.get("httpMethod")
            >>> event.get("resource")
        """
        return self._event.get(key, default)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        method = self._event.get("httpMethod", "UNKNOWN")
        path = self._event.get("path", "UNKNOWN")
        return f"LambdaEvent(method={method}, path={path})"
