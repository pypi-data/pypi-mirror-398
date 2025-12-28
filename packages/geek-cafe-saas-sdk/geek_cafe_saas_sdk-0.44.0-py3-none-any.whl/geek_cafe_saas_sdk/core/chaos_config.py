"""
Chaos Engineering Configuration for controlled fault injection.

Enables testing of error paths and exception handlers without mocking services.
Only active in non-production environments with proper authorization.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class ChaosConfig:
    """
    Configuration for chaos engineering fault injection.
    
    Allows controlled injection of failures for testing purposes.
    
    Example:
        >>> chaos = ChaosConfig(
        ...     enabled=True,
        ...     target_operations=['file_service.create'],
        ...     fault_type='exception'
        ... )
        >>> if chaos.should_trigger('file_service.create'):
        ...     # Inject fault
    """
    
    enabled: bool = False
    target_operations: List[str] = field(default_factory=list)
    fault_type: str = 'exception'  # exception, error_result, delay
    probability: float = 1.0  # 0.0 to 1.0 (for probabilistic failures)
    exception_type: str = 'RuntimeError'
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    delay_ms: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChaosConfig':
        """
        Create ChaosConfig from dictionary.
        
        Args:
            data: Dictionary with chaos configuration
            
        Returns:
            ChaosConfig instance
        """
        return cls(
            enabled=data.get('enabled', False),
            target_operations=data.get('operations', []),
            fault_type=data.get('fault_type', 'exception'),
            probability=data.get('probability', 1.0),
            exception_type=data.get('exception_type', 'RuntimeError'),
            error_code=data.get('error_code'),
            error_message=data.get('error_message'),
            delay_ms=data.get('delay_ms')
        )
    
    def should_trigger(self, operation: str) -> bool:
        """
        Check if fault should be triggered for given operation.
        
        Args:
            operation: Operation identifier (e.g., 'file_service.create')
            
        Returns:
            True if fault should be injected
        """
        if not self.enabled:
            return False
        
        # Check if operation matches any target
        if not self._operation_matches(operation):
            return False
        
        # Apply probability
        if self.probability < 1.0:
            import random
            return random.random() < self.probability
        
        return True
    
    def _operation_matches(self, operation: str) -> bool:
        """Check if operation matches any target patterns."""
        if not self.target_operations:
            return False
        
        for target in self.target_operations:
            # Support wildcards
            if target.endswith('.*'):
                prefix = target[:-2]
                if operation.startswith(prefix):
                    return True
            elif target == operation:
                return True
        
        return False


def is_chaos_enabled() -> bool:
    """
    Check if chaos engineering is enabled in current environment.
    
    Only enabled in non-production environments.
    
    Returns:
        True if chaos engineering is allowed
    """
    env = os.getenv('ENVIRONMENT', 'production').lower()
    return env in ['development', 'dev', 'staging', 'test', 'local']


def has_chaos_permission(permissions: List[str]) -> bool:
    """
    Check if user has permission to use chaos engineering.
    
    Args:
        permissions: List of user permissions
        
    Returns:
        True if user can inject faults
    """
    # Require explicit permission in all environments
    return 'chaos_engineering:execute' in permissions


def extract_chaos_config(user_context: Dict[str, Any]) -> Optional[ChaosConfig]:
    """
    Extract chaos configuration from user context.
    
    Args:
        user_context: User context dictionary from RequestContext
        
    Returns:
        ChaosConfig if valid, None otherwise
    """
    # Check if chaos is enabled in environment
    if not is_chaos_enabled():
        return None
    
    # Check permissions
    permissions = user_context.get('permissions', [])
    if not has_chaos_permission(permissions):
        return None
    
    # Extract chaos configuration
    chaos_data = user_context.get('chaos_engineering', {})
    if not chaos_data:
        return None
    
    try:
        config = ChaosConfig.from_dict(chaos_data)
        if config.enabled:
            logger.warning(
                f"🎭 CHAOS ENGINEERING ENABLED",
                extra={
                    'operations': config.target_operations,
                    'fault_type': config.fault_type,
                    'user_id': user_context.get('user_id'),
                    'tenant_id': user_context.get('tenant_id')
                }
            )
        return config
    except Exception as e:
        logger.error(f"Failed to parse chaos config: {e}")
        return None
