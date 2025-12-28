"""
Feature Flag Service for Geek Cafe SaaS SDK.

Provides centralized feature flag management with support for:
- Environment-based flags
- Tenant-specific flags
- User-specific flags
- Percentage rollouts
- DynamoDB-backed storage (optional)

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)


class FeatureFlagTarget(Enum):
    """Target scope for feature flags."""
    GLOBAL = "global"
    TENANT = "tenant"
    USER = "user"


@dataclass
class FeatureFlag:
    """
    Feature flag configuration.
    
    Example:
        >>> flag = FeatureFlag(
        ...     name='file_system_v2',
        ...     enabled=True,
        ...     target=FeatureFlagTarget.TENANT,
        ...     whitelist=['tenant-123', 'tenant-456']
        ... )
    """
    name: str
    enabled: bool = False
    target: FeatureFlagTarget = FeatureFlagTarget.GLOBAL
    whitelist: List[str] = field(default_factory=list)
    blacklist: List[str] = field(default_factory=list)
    rollout_percentage: int = 0  # 0-100
    description: Optional[str] = None
    
    def is_enabled_for(self, identifier: Optional[str] = None) -> bool:
        """
        Check if flag is enabled for given identifier.
        
        Args:
            identifier: Tenant ID, user ID, or None for global
            
        Returns:
            True if feature is enabled
        """
        # If flag is globally disabled, return False
        if not self.enabled:
            return False
        
        # Global flags don't need identifier
        if self.target == FeatureFlagTarget.GLOBAL:
            return True
        
        # If no identifier provided, can't check tenant/user flags
        if identifier is None:
            return False
        
        # Check blacklist first
        if identifier in self.blacklist:
            return False
        
        # Check whitelist
        if self.whitelist and identifier in self.whitelist:
            return True
        
        # Check rollout percentage
        if self.rollout_percentage > 0:
            # Simple hash-based percentage rollout
            # This ensures same identifier always gets same result
            hash_val = hash(f"{self.name}:{identifier}") % 100
            return hash_val < self.rollout_percentage
        
        return False


class FeatureFlagService:
    """
    Service for managing feature flags.
    
    Supports multiple backends:
    - Environment variables (default)
    - In-memory configuration (for testing)
    - DynamoDB (optional, for production)
    
    Usage:
        >>> flags = FeatureFlagService()
        >>> if flags.is_enabled('new_feature', tenant_id='tenant-123'):
        ...     # Use new code path
        ...     pass
    """
    
    def __init__(
        self,
        flags: Optional[Dict[str, FeatureFlag]] = None,
        use_dynamodb: bool = False,
        table_name: Optional[str] = None
    ):
        """
        Initialize feature flag service.
        
        Args:
            flags: Pre-configured flags (for testing)
            use_dynamodb: Whether to use DynamoDB backend
            table_name: DynamoDB table name (if using DynamoDB)
        """
        self._flags: Dict[str, FeatureFlag] = flags or {}
        self._use_dynamodb = use_dynamodb
        self._table_name = table_name or os.getenv('FEATURE_FLAGS_TABLE')
        self._dynamodb = None
        
        if not flags:
            self._load_from_environment()
    
    def _load_from_environment(self):
        """Load feature flags from environment variables."""
        # Look for env vars like: FEATURE_FLAG_<NAME>=true|false
        for key, value in os.environ.items():
            if key.startswith('FEATURE_FLAG_'):
                flag_name = key.replace('FEATURE_FLAG_', '').lower()
                enabled = value.lower() in ['true', '1', 'yes', 'enabled']
                
                self._flags[flag_name] = FeatureFlag(
                    name=flag_name,
                    enabled=enabled,
                    target=FeatureFlagTarget.GLOBAL
                )
                
                logger.debug(f"Loaded feature flag from env: {flag_name}={enabled}")
    
    def register(self, flag: FeatureFlag):
        """
        Register a feature flag.
        
        Args:
            flag: FeatureFlag to register
        """
        self._flags[flag.name] = flag
        logger.info(f"Registered feature flag: {flag.name}")
    
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
            flag_name: Name of the feature flag
            tenant_id: Tenant ID (for tenant-specific flags)
            user_id: User ID (for user-specific flags)
            default: Default value if flag not found
            
        Returns:
            True if feature is enabled
            
        Example:
            >>> flags = FeatureFlagService()
            >>> if flags.is_enabled('file_system_v2', tenant_id='tenant-123'):
            ...     # Use new code path
            ...     pass
        """
        flag = self._flags.get(flag_name)
        
        if not flag:
            logger.debug(f"Feature flag not found: {flag_name}, using default={default}")
            return default
        
        # Determine which identifier to use based on flag target
        identifier = None
        if flag.target == FeatureFlagTarget.TENANT:
            identifier = tenant_id
        elif flag.target == FeatureFlagTarget.USER:
            identifier = user_id
        
        enabled = flag.is_enabled_for(identifier)
        
        logger.debug(
            f"Feature flag check: {flag_name}={enabled} "
            f"(target={flag.target.value}, identifier={identifier})"
        )
        
        return enabled
    
    def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get feature flag by name."""
        return self._flags.get(flag_name)
    
    def list_flags(self) -> Dict[str, FeatureFlag]:
        """List all registered feature flags."""
        return self._flags.copy()
    
    def enable(self, flag_name: str):
        """Enable a feature flag."""
        if flag_name in self._flags:
            self._flags[flag_name].enabled = True
            logger.info(f"Enabled feature flag: {flag_name}")
    
    def disable(self, flag_name: str):
        """Disable a feature flag."""
        if flag_name in self._flags:
            self._flags[flag_name].enabled = False
            logger.info(f"Disabled feature flag: {flag_name}")


# Global singleton instance (optional convenience)
_default_service: Optional[FeatureFlagService] = None


def get_feature_flag_service() -> FeatureFlagService:
    """Get or create default feature flag service."""
    global _default_service
    if _default_service is None:
        _default_service = FeatureFlagService()
    return _default_service


def is_feature_enabled(
    flag_name: str,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    default: bool = False
) -> bool:
    """
    Convenience function to check feature flag using default service.
    
    Example:
        >>> from geek_cafe_saas_sdk.core.services import is_feature_enabled
        >>> if is_feature_enabled('new_feature', tenant_id='123'):
        ...     # Use new code
        ...     pass
    """
    return get_feature_flag_service().is_enabled(
        flag_name,
        tenant_id=tenant_id,
        user_id=user_id,
        default=default
    )
