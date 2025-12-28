"""
Service interfaces for SaaS applications.

These interfaces define the contract that all SaaS service implementations
must follow. Using Protocol for duck typing compatibility.
"""

from typing import Protocol, Optional, Dict, Any, List
from datetime import datetime


class ISecurityService(Protocol):
    """
    Interface for security validation service.
    
    All SaaS applications need security - this enforces the contract for:
    - Authentication: Who is the user?
    - Authorization: What can they do?
    - Tenant isolation: Can they access this tenant's data?
    """
    
    def load_from_event(self, event: Dict[str, Any], context: Any = None) -> None:
        """
        Load security context from Lambda event.
        
        Args:
            event: Lambda event with authentication info (API Gateway authorizer)
            context: Lambda context object
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If user lacks required permissions
        """
        ...
    
    @property
    def user_id(self) -> Optional[str]:
        """Get authenticated user ID."""
        ...
    
    @property
    def tenant_id(self) -> Optional[str]:
        """Get authenticated tenant ID."""
        ...
    
    @property
    def email(self) -> Optional[str]:
        """Get authenticated user email."""
        ...
    
    @property
    def roles(self) -> List[str]:
        """Get user roles."""
        ...
    
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        ...
    
    def is_tenant_admin(self) -> bool:
        """Check if user is admin for their tenant."""
        ...
    
    def validate_tenant_access(self, resource_tenant_id: str) -> bool:
        """
        Validate user has access to tenant resource.
        
        Args:
            resource_tenant_id: Tenant ID of the resource being accessed
            
        Returns:
            True if user can access resource, False otherwise
        """
        ...
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            permission: Permission string to check
            
        Returns:
            True if user has permission
        """
        ...


class IAuditService(Protocol):
    """
    Interface for audit logging service.
    
    Logs all significant operations for compliance, security, and debugging.
    """
    
    def log_event(
        self,
        event_type: str,
        resource_type: str,
        resource_id: str,
        action: str,
        result: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (e.g., "api_call", "data_access")
            resource_type: Type of resource (e.g., "file", "user", "execution")
            resource_id: ID of resource being accessed
            action: Action performed (e.g., "create", "read", "update", "delete")
            result: Result of operation ("success", "failure", "denied")
            metadata: Additional context data
        """
        ...
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a security-related event.
        
        Args:
            event_type: Type of security event (e.g., "auth_failure", "suspicious_activity")
            severity: Severity level ("info", "warning", "critical")
            message: Human-readable message
            metadata: Additional context
        """
        ...


class IFeatureFlagService(Protocol):
    """
    Interface for feature flag service.
    
    Enables gradual rollouts, A/B testing, and feature toggles.
    """
    
    def is_enabled(
        self,
        flag_name: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        default: bool = False
    ) -> bool:
        """
        Check if feature flag is enabled.
        
        Args:
            flag_name: Name of feature flag
            tenant_id: Optional tenant ID for tenant-specific flags
            user_id: Optional user ID for user-specific flags
            default: Default value if flag not found
            
        Returns:
            True if flag is enabled
        """
        ...
    
    def get_variant(
        self,
        flag_name: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        default: str = "control"
    ) -> str:
        """
        Get feature flag variant for A/B testing.
        
        Args:
            flag_name: Name of feature flag
            tenant_id: Optional tenant ID
            user_id: Optional user ID
            default: Default variant if not found
            
        Returns:
            Variant name (e.g., "control", "variant_a", "variant_b")
        """
        ...


class IMetricsService(Protocol):
    """
    Interface for metrics/analytics service.
    
    Tracks usage, performance, and business metrics.
    """
    
    def increment(
        self,
        metric_name: str,
        value: float = 1.0,
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            metric_name: Name of metric (e.g., "api_calls", "files_uploaded")
            value: Value to increment by
            dimensions: Metric dimensions (e.g., {"tenant_id": "123", "endpoint": "/files"})
        """
        ...
    
    def gauge(
        self,
        metric_name: str,
        value: float,
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a gauge metric (point-in-time value).
        
        Args:
            metric_name: Name of metric (e.g., "queue_depth", "memory_usage")
            value: Current value
            dimensions: Metric dimensions
        """
        ...
    
    def timing(
        self,
        metric_name: str,
        duration_ms: float,
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a timing metric.
        
        Args:
            metric_name: Name of metric (e.g., "request_duration", "db_query_time")
            duration_ms: Duration in milliseconds
            dimensions: Metric dimensions
        """
        ...
    
    def record_business_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a business metric.
        
        Args:
            metric_name: Name of metric (e.g., "revenue", "active_users")
            value: Metric value
            unit: Unit of measurement
            dimensions: Metric dimensions
        """
        ...


class INotificationService(Protocol):
    """
    Interface for notification service.
    
    Sends notifications via email, SMS, push, etc.
    """
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send email notification.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            reply_to: Optional reply-to address
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            
        Returns:
            True if email sent successfully
        """
        ...
    
    def send_sms(
        self,
        to: str,
        message: str
    ) -> bool:
        """
        Send SMS notification.
        
        Args:
            to: Phone number
            message: SMS message
            
        Returns:
            True if SMS sent successfully
        """
        ...
    
    def send_push_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send push notification to user's devices.
        
        Args:
            user_id: User ID
            title: Notification title
            body: Notification body
            data: Optional data payload
            
        Returns:
            True if notification sent successfully
        """
        ...


class IStorageService(Protocol):
    """
    Interface for file/object storage service.
    
    Abstracts S3, Azure Blob, Google Cloud Storage, etc.
    """
    
    def generate_presigned_upload_url(
        self,
        key: str,
        expires_in: int = 3600,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate presigned URL for uploading files.
        
        Args:
            key: Object key/path
            expires_in: URL expiration in seconds
            content_type: Optional content type
            metadata: Optional object metadata
            
        Returns:
            Dict with url, fields, expires_at
        """
        ...
    
    def generate_presigned_download_url(
        self,
        key: str,
        expires_in: int = 3600,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate presigned URL for downloading files.
        
        Args:
            key: Object key/path
            expires_in: URL expiration in seconds
            filename: Optional filename for Content-Disposition header
            
        Returns:
            Presigned URL
        """
        ...
    
    def upload_file(
        self,
        bucket: str,
        key: str,
        file_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Upload file to storage.
        
        Args:
            key: Object key/path
            file_path: Local file path
            content_type: Optional content type
            metadata: Optional object metadata
            
        Returns:
            True if upload successful
        """
        ...
    
    def download_file(
        self,
        bucket: str,
        key: str,
        file_path: str
    ) -> bool:
        """
        Download file from storage.
        
        Args:
            key: Object key/path
            file_path: Local file path to save to
            
        Returns:
            True if download successful
        """
        ...
    
    def delete_file(self, key: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            key: Object key/path
            
        Returns:
            True if deletion successful
        """
        ...
    
    def file_exists(self, key: str) -> bool:
        """
        Check if file exists.
        
        Args:
            key: Object key/path
            
        Returns:
            True if file exists
        """
        ...


class ICacheService(Protocol):
    """
    Interface for caching service.
    
    Provides fast access to frequently used data (Redis, Memcached, etc.)
    """
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        ...
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional TTL in seconds
            
        Returns:
            True if set successful
        """
        ...
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deletion successful
        """
        ...
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        ...
    
    def increment(
        self,
        key: str,
        amount: int = 1
    ) -> int:
        """
        Increment counter in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value after increment
        """
        ...
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache entries.
        
        Args:
            pattern: Optional pattern to match keys (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        ...
