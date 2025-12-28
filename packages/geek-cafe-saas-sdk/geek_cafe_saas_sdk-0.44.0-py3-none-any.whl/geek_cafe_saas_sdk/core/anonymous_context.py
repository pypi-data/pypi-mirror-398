"""
Anonymous Context Factory for Public Operations.

Provides standardized RequestContext for:
- Anonymous/public operations (contact forms, surveys, voting)
- System operations (background jobs, scheduled tasks)

Maintains security architecture while allowing public access.
"""

import os
from typing import Dict, Any, Optional
from .request_context import RequestContext


class AnonymousContextFactory:
    """
    Factory for creating RequestContext for anonymous/public operations.
    
    Use this for operations that don't require authentication but still
    need security context for audit trails and validation.
    
    Examples:
        - Public contact forms
        - Anonymous voting/polls
        - Public surveys
        - Newsletter signups
        - A/B testing
    """
    
    # Standard user IDs for special contexts
    ANONYMOUS_USER_ID = "anonymous"
    SYSTEM_USER_ID = "system"
    SYSTEM_TENANT_ID = "SYSTEM"  # Used for tenant provisioning operations
    
    @staticmethod
    def create_anonymous_context(
        tenant_id: str,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> RequestContext:
        """
        Create RequestContext for anonymous operations.
        
        Anonymous users:
        - Belong to a specific tenant
        - Have limited permissions (public:submit)
        - Tracked by IP and session for rate limiting
        - Show as 'anonymous' in audit trail
        
        Args:
            tenant_id: Tenant ID (required - anonymous users still belong to tenant)
            ip_address: Optional IP address for rate limiting/tracking
            session_id: Optional session ID for duplicate prevention
            additional_metadata: Extra metadata (e.g., referrer, user agent)
            
        Returns:
            RequestContext with anonymous user identity
            
        Example:
            >>> from geek_cafe_saas_sdk.core.anonymous_context import AnonymousContextFactory
            >>> 
            >>> # In public Lambda handler
            >>> context = AnonymousContextFactory.create_anonymous_context(
            ...     tenant_id='tenant_123',
            ...     ip_address='192.168.1.1',
            ...     session_id='sess_abc123'
            ... )
            >>> 
            >>> service = ContactThreadService(
            ...     dynamodb=db,
            ...     table_name=TABLE,
            ...     request_context=context
            ... )
            >>> 
            >>> result = service.create(
            ...     tenant_id='tenant_123',
            ...     user_id='anonymous',
            ...     payload={'message': 'Hello'}
            ... )
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for anonymous context")
        
        user_context = {
            'user_id': AnonymousContextFactory.ANONYMOUS_USER_ID,
            'tenant_id': tenant_id,
            'email': 'anonymous@public',
            'roles': ['public'],
            'permissions': ['public:submit'],
            'inboxes': [],
            
            # Special flags
            'is_anonymous': True,
            'is_authenticated': False,
            
            # Tracking for rate limiting and abuse prevention
            'ip_address': ip_address,
            'session_id': session_id,
            
            # Additional context
            'metadata': additional_metadata or {}
        }
        
        return RequestContext(user_context)
    
    @staticmethod
    def create_system_context(
        tenant_id: str,
        operation_name: Optional[str] = None
    ) -> RequestContext:
        """
        Create RequestContext for system operations.
        
        System context:
        - Used for background jobs and scheduled tasks
        - Has elevated permissions (*:*:*)
        - Shows as 'system' in audit trail
        - Not rate limited
        
        Args:
            tenant_id: Tenant ID for the operation
            operation_name: Optional name of the operation (for logging)
            
        Returns:
            RequestContext with system identity
            
        Example:
            >>> from geek_cafe_saas_sdk.core.anonymous_context import AnonymousContextFactory
            >>> 
            >>> # In background job
            >>> context = AnonymousContextFactory.create_system_context(
            ...     tenant_id='tenant_123',
            ...     operation_name='cleanup_old_data'
            ... )
            >>> 
            >>> service = AnalyticsService(
            ...     dynamodb=db,
            ...     table_name=TABLE,
            ...     request_context=context
            ... )
            >>> 
            >>> result = service.delete_old_records(days_old=90)
            >>> # Audit trail shows: deleted_by='system'
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for system context")
        
        user_context = {
            'user_id': AnonymousContextFactory.SYSTEM_USER_ID,
            'tenant_id': tenant_id,
            'email': 'system@internal',
            'roles': ['system'],
            'permissions': ['*:*:*'],  # System has all permissions
            'inboxes': [],
            
            # Special flags
            'is_system': True,
            'is_authenticated': True,
            
            # Context
            'operation_name': operation_name,
            'metadata': {'operation': operation_name} if operation_name else {}
        }
        
        return RequestContext(user_context)
    
    @staticmethod
    def create_test_context(
        user_id: str = "context_factory_anonymous_user",
        tenant_id: str = "context_factory_anonymous_tenant",
        roles: Optional[list] = None,
        permissions: Optional[list] = None,
        allow_tenant_wide_access: bool = False
    ) -> RequestContext:
        """
        Create RequestContext for testing.
        
        Convenience method for creating test contexts without full JWT setup.
        
        Args:
            user_id: Test user ID
            tenant_id: Test tenant ID
            roles: Optional list of roles
            permissions: Optional list of permissions
            allow_tenant_wide_access: If True, any user in tenant can access any resource.
                                     Default False for strict security.
            
        Returns:
            RequestContext for testing
            
        Example:
            >>> from geek_cafe_saas_sdk.core.anonymous_context import AnonymousContextFactory
            >>> 
            >>> # In test
            >>> context = AnonymousContextFactory.create_test_context(
            ...     user_id='user_123',
            ...     tenant_id='tenant_123',
            ...     permissions=['messages:create']
            ... )
        """
        from geek_cafe_saas_sdk.core.tenant_settings import TenantSettings
        
        user_context = {
            'user_id': user_id,
            'tenant_id': tenant_id,
            'email': f'{user_id}@test.com',
            'roles': roles or [],
            'permissions': permissions or [],
            'inboxes': [],
            'is_test': True
        }
        
        context = RequestContext(user_context)
        
        # Set tenant settings for testing
        context.set_tenant_settings(TenantSettings(
            tenant_id=tenant_id,
            allow_tenant_wide_access=allow_tenant_wide_access,
            features={},
            plan_tier='free',
            is_active=True
        ))
        
        return context
    
    @staticmethod
    def create_provisioning_context(
        operation_name: str = "tenant_provisioning"
    ) -> RequestContext:
        """
        Create RequestContext for tenant provisioning operations (signup flow).
        
        Provisioning context:
        - Used for creating new tenants during signup
        - Has SYSTEM tenant_id to bypass tenant isolation
        - Has elevated permissions for tenant creation
        - Shows as 'system' in audit trail
        
        Args:
            operation_name: Name of the provisioning operation (for logging)
            
        Returns:
            RequestContext with system identity for provisioning
            
        Example:
            >>> from geek_cafe_saas_sdk.core.anonymous_context import AnonymousContextFactory
            >>> 
            >>> # In signup handler
            >>> context = AnonymousContextFactory.create_provisioning_context(
            ...     operation_name='user_signup'
            ... )
            >>> 
            >>> tenant_service = TenantService(
            ...     dynamodb=db,
            ...     table_name=TABLE,
            ...     request_context=context
            ... )
            >>> 
            >>> result = tenant_service.create_with_user(
            ...     user_payload={...},
            ...     tenant_payload={...}
            ... )
            >>> # Creates new tenant, audit trail shows: created_by='system'
        """
        user_context = {
            'user_id': AnonymousContextFactory.SYSTEM_USER_ID,
            'tenant_id': AnonymousContextFactory.SYSTEM_TENANT_ID,
            'email': 'system@internal',
            'roles': ['system', 'provisioner'],
            'permissions': ['*:*:*'],  # System has all permissions
            'inboxes': [],
            
            # Special flags
            'is_system': True,
            'is_provisioning': True,
            'is_authenticated': True,
            
            # Context
            'operation_name': operation_name,
            'metadata': {'operation': operation_name, 'type': 'provisioning'}
        }
        
        return RequestContext(user_context)
    
    @staticmethod
    def is_anonymous(request_context: RequestContext) -> bool:
        """
        Check if request context is anonymous.
        
        Args:
            request_context: RequestContext to check
            
        Returns:
            True if anonymous, False otherwise
        """
        return request_context._user_context.get('is_anonymous', False)
    
    @staticmethod
    def is_system(request_context: RequestContext) -> bool:
        """
        Check if request context is system.
        
        Args:
            request_context: RequestContext to check
            
        Returns:
            True if system, False otherwise
        """
        return request_context._user_context.get('is_system', False)
    
    @staticmethod
    def get_ip_address(request_context: RequestContext) -> Optional[str]:
        """
        Get IP address from request context.
        
        Args:
            request_context: RequestContext
            
        Returns:
            IP address if available, None otherwise
        """
        return request_context._user_context.get('ip_address')
    
    @staticmethod
    def get_session_id(request_context: RequestContext) -> Optional[str]:
        """
        Get session ID from request context.
        
        Args:
            request_context: RequestContext
            
        Returns:
            Session ID if available, None otherwise
        """
        return request_context._user_context.get('session_id')
