"""
No-Op Audit Logger - Disabled audit logging implementation.

This implementation does nothing and is used when audit logging
is disabled via configuration.

Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import List, Optional, Dict, Any
from .audit_event import AuditEvent


class NoOpAuditLogger:
    """
    No-op audit logger that does nothing.
    
    Used when audit logging is disabled. All methods return success
    without performing any operations.
    
    Example:
        # When AUDIT_LOG_ENABLED=false
        logger = NoOpAuditLogger()
        logger.log(event)  # Does nothing, returns True
    """
    
    @property
    def is_enabled(self) -> bool:
        """Always returns False - auditing is disabled."""
        return False
    
    def log(self, event: AuditEvent) -> bool:
        """
        No-op log method.
        
        Args:
            event: Ignored
            
        Returns:
            Always True
        """
        return True
    
    def log_batch(self, events: List[AuditEvent]) -> bool:
        """
        No-op batch log method.
        
        Args:
            events: Ignored
            
        Returns:
            Always True
        """
        return True
    
    def query_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        *,
        limit: int = 100,
        start_key: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """
        No-op query method.
        
        Returns:
            Empty list
        """
        return []
    
    def query_by_user(
        self,
        tenant_id: str,
        user_id: str,
        *,
        limit: int = 100,
        start_key: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """
        No-op query method.
        
        Returns:
            Empty list
        """
        return []
    
    def query_by_tenant(
        self,
        tenant_id: str,
        *,
        limit: int = 100,
        start_key: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """
        No-op query method.
        
        Returns:
            Empty list
        """
        return []
