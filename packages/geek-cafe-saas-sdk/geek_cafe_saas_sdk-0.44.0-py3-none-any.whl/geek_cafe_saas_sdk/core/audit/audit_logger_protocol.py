"""
Audit Logger Protocol - Interface for audit logging implementations.

This module defines the IAuditLogger protocol that all audit logger
implementations must follow.

Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Protocol, List, Optional, Dict, Any
from .audit_event import AuditEvent


class IAuditLogger(Protocol):
    """
    Protocol for audit logging implementations.
    
    All audit loggers must implement this interface to be used with
    the DatabaseService audit logging infrastructure.
    
    Implementations:
    - DynamoDBAuditLogger: Logs to DynamoDB table
    - S3AuditLogger: Logs to S3 bucket as JSON files
    - CompositeAuditLogger: Logs to multiple destinations
    - NoOpAuditLogger: No-op implementation (disabled auditing)
    
    Example:
        class MyCustomAuditLogger:
            def log(self, event: AuditEvent) -> bool:
                # Custom implementation
                return True
            
            def log_batch(self, events: List[AuditEvent]) -> bool:
                for event in events:
                    self.log(event)
                return True
            
            @property
            def is_enabled(self) -> bool:
                return True
    """
    
    def log(self, event: AuditEvent) -> bool:
        """
        Log a single audit event.
        
        Args:
            event: The audit event to log
            
        Returns:
            True if logging succeeded, False otherwise
            
        Note:
            Implementations should be fail-safe - logging failures
            should not raise exceptions that break business operations.
        """
        ...
    
    def log_batch(self, events: List[AuditEvent]) -> bool:
        """
        Log multiple audit events in a batch.
        
        Args:
            events: List of audit events to log
            
        Returns:
            True if all events were logged successfully
            
        Note:
            Implementations may optimize batch operations (e.g., DynamoDB batch_write).
            Default implementation can iterate and call log() for each event.
        """
        ...
    
    @property
    def is_enabled(self) -> bool:
        """
        Check if audit logging is enabled.
        
        Returns:
            True if audit logging is active, False if disabled
        """
        ...
    
    def query_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        *,
        limit: int = 100,
        start_key: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """
        Query audit events for a specific resource.
        
        Args:
            resource_type: Type of resource (e.g., "file", "user")
            resource_id: ID of the resource
            limit: Maximum number of events to return
            start_key: Pagination key for continued queries
            
        Returns:
            List of audit events for the resource, ordered by timestamp descending
            
        Note:
            Not all implementations may support querying. S3AuditLogger may
            return empty list or raise NotImplementedError.
        """
        ...
    
    def query_by_user(
        self,
        tenant_id: str,
        user_id: str,
        *,
        limit: int = 100,
        start_key: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """
        Query audit events for a specific user.
        
        Args:
            tenant_id: Tenant context
            user_id: User ID to query
            limit: Maximum number of events to return
            start_key: Pagination key for continued queries
            
        Returns:
            List of audit events by the user, ordered by timestamp descending
        """
        ...
    
    def query_by_tenant(
        self,
        tenant_id: str,
        *,
        limit: int = 100,
        start_key: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """
        Query all audit events for a tenant.
        
        Args:
            tenant_id: Tenant to query
            limit: Maximum number of events to return
            start_key: Pagination key for continued queries
            
        Returns:
            List of audit events for the tenant, ordered by timestamp descending
        """
        ...
