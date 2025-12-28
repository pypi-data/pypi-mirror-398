"""
Base services container for SaaS applications.

Enforces that all SaaS applications have standard services:
- Security: authentication, authorization, tenant isolation
- Audit: event logging for compliance
- Feature Flags: gradual rollouts, A/B testing
- Metrics: usage and performance tracking
- Notifications: email, SMS, push
- Storage: file/object storage abstraction
- Cache: fast data access

Implementations provide concrete services while geek-cafe enforces the pattern.
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from aws_lambda_powertools import Logger

from .service_interfaces import (
    ISecurityService,
    IAuditService,
    IFeatureFlagService,
    IMetricsService,
    INotificationService,
    IStorageService,
    ICacheService
)

logger = Logger()


class ServicesContainer(ABC):
    """
    Base services container for SaaS applications.
    
    All SaaS applications built with geek-cafe must extend this class
    and provide concrete implementations of the required services.
    
    Pattern:
        1. Create container per Lambda invocation
        2. Container reuses connections from pool (performance)
        3. Security auto-loaded from event
        4. Services accessible via properties throughout request
    
    Example:
        # Concrete implementation
        class MyServicesContainer(ServicesContainer):
            def _initialize_services(self):
                self._security = MySecurityService(self.db)
                self._audit = MyAuditService(self.db)
                # ... other services
        
        # In Lambda handler
        container = MyServicesContainer(event, context)
        user_id = container.current_user_id
        container.audit.log_event(...)
    """
    
    def __init__(
        self,
        event: Optional[Dict[str, Any]] = None,
        context: Any = None
    ):
        """
        Initialize services container.
        
        Args:
            event: Lambda event (optional - can load security later)
            context: Lambda context (optional)
        """
        self.event = event
        self.context = context
        
        # Service instances (set by _initialize_services)
        self._security: Optional[ISecurityService] = None
        self._audit: Optional[IAuditService] = None
        self._feature_flags: Optional[IFeatureFlagService] = None
        self._metrics: Optional[IMetricsService] = None
        self._notifications: Optional[INotificationService] = None
        self._storage: Optional[IStorageService] = None
        self._cache: Optional[ICacheService] = None
        
        # Initialize concrete services (implemented by subclass)
        self._initialize_services()
        
        # Load security from event if provided
        if event:
            self.load_security(event, context)
    
    @abstractmethod
    def _initialize_services(self) -> None:
        """
        Initialize concrete service implementations.
        
        Subclasses MUST implement this to provide:
            self._security = ConcreteSecurityService()
            self._audit = ConcreteAuditService()
            self._feature_flags = ConcreteFeatureFlagService()
            self._metrics = ConcreteMetricsService()
            self._notifications = ConcreteNotificationService()
            self._storage = ConcreteStorageService()
            self._cache = ConcreteCacheService()
        
        Services should use connection pool for database connections:
            from geek_cafe_saas_sdk.core.connection_pool import get_pooled_connection
            db = get_pooled_connection('dynamodb')
        """
        pass
    
    def load_security(self, event: Dict[str, Any], context: Any = None) -> None:
        """
        Load security context from Lambda event.
        
        Automatically extracts authentication info from API Gateway
        authorizer claims and validates user/tenant access.
        
        Args:
            event: Lambda event with authentication info
            context: Lambda context
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If authorization fails
        """
        self.event = event
        self.context = context
        
        if self._security:
            try:
                self._security.load_from_event(event, context)
                logger.debug(
                    "Security loaded successfully",
                    extra={
                        "user_id": self._security.user_id,
                        "tenant_id": self._security.tenant_id
                    }
                )
            except Exception as e:
                logger.error(f"Failed to load security: {e}")
                raise
        else:
            logger.warning("Security service not initialized, skipping security load")
    
    # ========== Required Service Properties ==========
    
    @property
    def security(self) -> ISecurityService:
        """
        Get security service.
        
        Returns:
            Security service instance
            
        Raises:
            RuntimeError: If security service not initialized
        """
        if not self._security:
            raise RuntimeError(
                "Security service not initialized. "
                "Did you implement _initialize_services()?"
            )
        return self._security
    
    @property
    def audit(self) -> IAuditService:
        """
        Get audit service.
        
        Returns:
            Audit service instance
            
        Raises:
            RuntimeError: If audit service not initialized
        """
        if not self._audit:
            raise RuntimeError(
                "Audit service not initialized. "
                "Did you implement _initialize_services()?"
            )
        return self._audit
    
    @property
    def feature_flags(self) -> IFeatureFlagService:
        """
        Get feature flag service.
        
        Returns:
            Feature flag service instance
            
        Raises:
            RuntimeError: If feature flag service not initialized
        """
        if not self._feature_flags:
            raise RuntimeError(
                "Feature flag service not initialized. "
                "Did you implement _initialize_services()?"
            )
        return self._feature_flags
    
    @property
    def metrics(self) -> IMetricsService:
        """
        Get metrics service.
        
        Returns:
            Metrics service instance
            
        Raises:
            RuntimeError: If metrics service not initialized
        """
        if not self._metrics:
            raise RuntimeError(
                "Metrics service not initialized. "
                "Did you implement _initialize_services()?"
            )
        return self._metrics
    
    @property
    def notifications(self) -> INotificationService:
        """
        Get notifications service.
        
        Returns:
            Notifications service instance
            
        Raises:
            RuntimeError: If notifications service not initialized
        """
        if not self._notifications:
            raise RuntimeError(
                "Notifications service not initialized. "
                "Did you implement _initialize_services()?"
            )
        return self._notifications
    
    @property
    def storage(self) -> IStorageService:
        """
        Get storage service.
        
        Returns:
            Storage service instance
            
        Raises:
            RuntimeError: If storage service not initialized
        """
        if not self._storage:
            raise RuntimeError(
                "Storage service not initialized. "
                "Did you implement _initialize_services()?"
            )
        return self._storage
    
    @property
    def cache(self) -> ICacheService:
        """
        Get cache service.
        
        Returns:
            Cache service instance
            
        Raises:
            RuntimeError: If cache service not initialized
        """
        if not self._cache:
            raise RuntimeError(
                "Cache service not initialized. "
                "Did you implement _initialize_services()?"
            )
        return self._cache
    
    # ========== Convenience Properties ==========
    
    @property
    def current_user_id(self) -> Optional[str]:
        """
        Convenience property to get current authenticated user ID.
        
        Returns:
            User ID from security service
        """
        return self.security.user_id if self._security else None
    
    @property
    def current_tenant_id(self) -> Optional[str]:
        """
        Convenience property to get current authenticated tenant ID.
        
        Returns:
            Tenant ID from security service
        """
        return self.security.tenant_id if self._security else None
    
    @property
    def current_user_email(self) -> Optional[str]:
        """
        Convenience property to get current authenticated user email.
        
        Returns:
            User email from security service
        """
        return self.security.email if self._security else None
    
    @property
    def current_user_roles(self) -> list[str]:
        """
        Convenience property to get current user roles.
        
        Returns:
            List of user roles from security service
        """
        return self.security.roles if self._security else []
    
    # ========== Convenience Methods ==========
    
    def is_admin(self) -> bool:
        """
        Check if current user has admin privileges.
        
        Returns:
            True if user is admin
        """
        return self.security.is_admin() if self._security else False
    
    def is_tenant_admin(self) -> bool:
        """
        Check if current user is admin for their tenant.
        
        Returns:
            True if user is tenant admin
        """
        return self.security.is_tenant_admin() if self._security else False
    
    def log_audit_event(
        self,
        event_type: str,
        resource_type: str,
        resource_id: str,
        action: str,
        result: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Convenience method to log audit event.
        
        Args:
            event_type: Type of event
            resource_type: Type of resource
            resource_id: Resource ID
            action: Action performed
            result: Operation result
            metadata: Additional context
        """
        if self._audit:
            self.audit.log_event(
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                result=result,
                metadata=metadata
            )
    
    def increment_metric(
        self,
        metric_name: str,
        value: float = 1.0,
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Convenience method to increment metric.
        
        Args:
            metric_name: Metric name
            value: Value to increment
            dimensions: Metric dimensions
        """
        if self._metrics:
            self.metrics.increment(metric_name, value, dimensions)
    
    def __repr__(self) -> str:
        """String representation of container."""
        services_status = {
            "security": bool(self._security),
            "audit": bool(self._audit),
            "feature_flags": bool(self._feature_flags),
            "metrics": bool(self._metrics),
            "notifications": bool(self._notifications),
            "storage": bool(self._storage),
            "cache": bool(self._cache)
        }
        return f"<{self.__class__.__name__} services={services_status}>"
