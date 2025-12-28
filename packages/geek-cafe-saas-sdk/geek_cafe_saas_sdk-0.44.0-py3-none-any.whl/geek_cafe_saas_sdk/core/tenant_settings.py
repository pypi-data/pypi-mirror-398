"""
Geek Cafe, LLC
MIT License. See Project Root for the license information.

TenantSettings - Cached tenant configuration for request-scoped access.

This module provides a lightweight settings object that is loaded once per request
and cached in RequestContext. It avoids repeated database lookups for tenant
configuration during a single request lifecycle.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Protocol, runtime_checkable


@dataclass
class TenantSettings:
    """
    Cached tenant settings for request-scoped access control decisions.
    
    This is a lightweight snapshot of tenant configuration that affects
    security and access control. It's loaded once per request and cached
    in RequestContext to avoid repeated database lookups.
    
    Attributes:
        tenant_id: The tenant ID these settings belong to
        allow_tenant_wide_access: If True, any user in the tenant can access
            any resource in the tenant (less strict). If False, resources
            require explicit ownership or sharing (more strict).
            Default: False (strict mode)
        features: Feature flags from tenant configuration
        plan_tier: Tenant's subscription plan tier
        is_active: Whether the tenant is active
    """
    tenant_id: str
    allow_tenant_wide_access: bool = False
    features: Dict[str, Any] = field(default_factory=dict)
    plan_tier: str = "free"
    is_active: bool = True
    
    def has_feature(self, feature_key: str) -> bool:
        """Check if tenant has a specific feature enabled."""
        return self.features.get(feature_key, False) is True
    
    @classmethod
    def default(cls, tenant_id: str) -> "TenantSettings":
        """
        Create default settings for a tenant.
        
        Used when tenant settings cannot be loaded (fail-safe to strict mode).
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            TenantSettings with secure defaults
        """
        return cls(
            tenant_id=tenant_id,
            allow_tenant_wide_access=False,  # Strict by default
            features={},
            plan_tier="free",
            is_active=True
        )
    
    @classmethod
    def from_tenant(cls, tenant: Any) -> "TenantSettings":
        """
        Create settings from a Tenant model instance.
        
        Args:
            tenant: Tenant model instance
            
        Returns:
            TenantSettings populated from tenant
        """
        return cls(
            tenant_id=tenant.id,
            allow_tenant_wide_access=getattr(tenant, 'allow_tenant_wide_access', False),
            features=getattr(tenant, 'features', {}) or {},
            plan_tier=getattr(tenant, 'plan_tier', 'free') or 'free',
            is_active=tenant.is_active() if hasattr(tenant, 'is_active') else True
        )


@runtime_checkable
class ITenantSettingsLoader(Protocol):
    """
    Protocol for loading tenant settings.
    
    This allows dependency injection of the tenant loading mechanism,
    avoiding circular dependencies between RequestContext and DatabaseService.
    
    Implementations:
    - Production: Loads from DynamoDB via TenantService
    - Testing: Returns mock/default settings
    """
    
    def load_settings(self, tenant_id: str) -> Optional[TenantSettings]:
        """
        Load tenant settings by tenant ID.
        
        Args:
            tenant_id: The tenant ID to load settings for
            
        Returns:
            TenantSettings if found, None otherwise
        """
        ...


class DefaultTenantSettingsLoader:
    """
    Default loader that returns secure defaults.
    
    Used when no custom loader is configured. Returns strict settings
    to ensure security is not accidentally bypassed.
    """
    
    def load_settings(self, tenant_id: str) -> Optional[TenantSettings]:
        """Return default strict settings."""
        return TenantSettings.default(tenant_id)
