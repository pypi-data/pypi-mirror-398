"""
Composite Audit Logger - Logs to multiple destinations.

This implementation allows logging to multiple audit loggers
simultaneously (e.g., DynamoDB for queries + S3 for archival).

Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import List, Optional, Dict, Any
from aws_lambda_powertools import Logger

from .audit_event import AuditEvent
from .audit_logger_protocol import IAuditLogger

logger = Logger()


class CompositeAuditLogger:
    """
    Audit logger that logs to multiple destinations.
    
    Useful for scenarios where you want:
    - DynamoDB for fast queries
    - S3 for long-term archival with Object Lock
    
    Behavior:
    - log() calls all loggers, returns True if ANY succeed
    - query methods use the primary logger (first in list)
    - Failures in one logger don't affect others
    
    Example:
        dynamodb_logger = DynamoDBAuditLogger(table_name="audit-logs")
        s3_logger = S3AuditLogger(bucket_name="audit-archive")
        
        composite = CompositeAuditLogger(
            loggers=[dynamodb_logger, s3_logger],
            primary_logger=dynamodb_logger  # Used for queries
        )
        
        # Logs to both DynamoDB and S3
        composite.log(event)
        
        # Queries from DynamoDB (primary)
        events = composite.query_by_resource("file", "file_123")
    """
    
    def __init__(
        self,
        *,
        loggers: List[IAuditLogger],
        primary_logger: Optional[IAuditLogger] = None,
        fail_open: bool = True
    ):
        """
        Initialize composite audit logger.
        
        Args:
            loggers: List of audit loggers to write to
            primary_logger: Logger to use for queries (defaults to first in list)
            fail_open: If True, continue even if some loggers fail
        """
        if not loggers:
            raise ValueError("At least one logger is required")
        
        self._loggers = loggers
        self._primary_logger = primary_logger or loggers[0]
        self._fail_open = fail_open
        self._enabled = True
    
    @property
    def is_enabled(self) -> bool:
        """Check if audit logging is enabled."""
        return self._enabled and any(l.is_enabled for l in self._loggers)
    
    @is_enabled.setter
    def is_enabled(self, value: bool) -> None:
        """Enable or disable audit logging."""
        self._enabled = value
    
    @property
    def loggers(self) -> List[IAuditLogger]:
        """Get the list of loggers."""
        return self._loggers
    
    @property
    def primary_logger(self) -> IAuditLogger:
        """Get the primary logger used for queries."""
        return self._primary_logger
    
    def log(self, event: AuditEvent) -> bool:
        """
        Log audit event to all configured loggers.
        
        Args:
            event: The audit event to log
            
        Returns:
            True if at least one logger succeeded
        """
        if not self._enabled:
            return True
        
        successes = 0
        failures = 0
        
        for audit_logger in self._loggers:
            try:
                if audit_logger.is_enabled:
                    if audit_logger.log(event):
                        successes += 1
                    else:
                        failures += 1
            except Exception as e:
                logger.error(
                    f"Composite logger failed for {type(audit_logger).__name__}: {e}"
                )
                failures += 1
                if not self._fail_open:
                    raise
        
        # Return True if at least one logger succeeded
        return successes > 0
    
    def log_batch(self, events: List[AuditEvent]) -> bool:
        """
        Log multiple audit events to all configured loggers.
        
        Args:
            events: List of audit events to log
            
        Returns:
            True if at least one logger succeeded for all events
        """
        if not self._enabled:
            return True
        
        if not events:
            return True
        
        successes = 0
        failures = 0
        
        for audit_logger in self._loggers:
            try:
                if audit_logger.is_enabled:
                    if audit_logger.log_batch(events):
                        successes += 1
                    else:
                        failures += 1
            except Exception as e:
                logger.error(
                    f"Composite batch logger failed for {type(audit_logger).__name__}: {e}"
                )
                failures += 1
                if not self._fail_open:
                    raise
        
        return successes > 0
    
    def query_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        *,
        limit: int = 100,
        start_key: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """
        Query audit events for a specific resource using primary logger.
        
        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            limit: Maximum number of events to return
            start_key: Pagination key
            
        Returns:
            List of audit events from primary logger
        """
        return self._primary_logger.query_by_resource(
            resource_type, resource_id, limit=limit, start_key=start_key
        )
    
    def query_by_user(
        self,
        tenant_id: str,
        user_id: str,
        *,
        limit: int = 100,
        start_key: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """
        Query audit events for a specific user using primary logger.
        
        Args:
            tenant_id: Tenant context
            user_id: User ID to query
            limit: Maximum number of events to return
            start_key: Pagination key
            
        Returns:
            List of audit events from primary logger
        """
        return self._primary_logger.query_by_user(
            tenant_id, user_id, limit=limit, start_key=start_key
        )
    
    def query_by_tenant(
        self,
        tenant_id: str,
        *,
        limit: int = 100,
        start_key: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """
        Query all audit events for a tenant using primary logger.
        
        Args:
            tenant_id: Tenant to query
            limit: Maximum number of events to return
            start_key: Pagination key
            
        Returns:
            List of audit events from primary logger
        """
        return self._primary_logger.query_by_tenant(
            tenant_id, limit=limit, start_key=start_key
        )
