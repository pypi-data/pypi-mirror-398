"""
S3 Audit Logger - Stores audit events in S3 as JSON files.

This implementation stores audit events in S3 with a hierarchical
key structure for easy browsing and compliance archival.

Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime, UTC
import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger

from .audit_event import AuditEvent

logger = Logger()


class S3AuditLogger:
    """
    Audit logger that stores events in S3 as JSON files.
    
    Features:
    - Stores audit events as JSON files in S3
    - Hierarchical key structure for easy browsing
    - Supports S3 Object Lock for immutability (21 CFR Part 11)
    - Fail-safe: logging errors don't break business operations
    
    Key Structure:
        {prefix}/tenant={tenant_id}/year={YYYY}/month={MM}/day={DD}/{audit_id}.json
    
    Example:
        audit-logs/tenant=tenant_123/year=2024/month=12/day=15/abc123.json
    
    S3 Bucket Configuration for 21 CFR Part 11:
    - Enable S3 Object Lock (Governance or Compliance mode)
    - Enable versioning
    - Configure lifecycle rules for retention
    - Enable server-side encryption
    
    Example:
        logger = S3AuditLogger(
            bucket_name="my-audit-logs",
            prefix="audit-logs"
        )
        
        event = AuditEvent(
            tenant_id="tenant_123",
            user_id="user_456",
            action="CREATE",
            resource_type="file",
            resource_id="file_789"
        )
        
        logger.log(event)
    """
    
    def __init__(
        self,
        *,
        bucket_name: str,
        prefix: str = "audit-logs",
        s3_client: Optional[Any] = None,
        fail_open: bool = True
    ):
        """
        Initialize S3 audit logger.
        
        Args:
            bucket_name: S3 bucket name for audit logs
            prefix: Key prefix for audit log files
            s3_client: Optional boto3 S3 client (creates new if not provided)
            fail_open: If True, logging failures don't raise exceptions
        """
        self._bucket_name = bucket_name
        self._prefix = prefix.rstrip("/")
        self._s3_client = s3_client or boto3.client("s3")
        self._fail_open = fail_open
        self._enabled = True
    
    @property
    def is_enabled(self) -> bool:
        """Check if audit logging is enabled."""
        return self._enabled
    
    @is_enabled.setter
    def is_enabled(self, value: bool) -> None:
        """Enable or disable audit logging."""
        self._enabled = value
    
    def log(self, event: AuditEvent) -> bool:
        """
        Log a single audit event to S3.
        
        Args:
            event: The audit event to log
            
        Returns:
            True if logging succeeded, False otherwise
        """
        if not self._enabled:
            return True
        
        try:
            # Ensure event has an ID
            if not event.id:
                event.prep_for_save()
            
            # Generate S3 key with hierarchical structure
            key = self._generate_key(event)
            
            # Convert event to JSON (AuditEvent is now AuditLog with to_dictionary)
            body = json.dumps(event.to_dictionary(), default=str, indent=2)
            
            # Upload to S3
            self._s3_client.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=body.encode("utf-8"),
                ContentType="application/json",
                Metadata={
                    "tenant_id": event.tenant_id or "",
                    "actor_user_id": event.actor_user_id or "",
                    "action": event.action or "",
                    "resource_type": event.resource_type or "",
                    "resource_id": event.resource_id or ""
                }
            )
            
            logger.debug(
                "Audit event logged to S3",
                extra={
                    "audit_id": event.id,
                    "s3_key": key,
                    "action": event.action
                }
            )
            return True
            
        except ClientError as e:
            logger.error(
                f"Failed to log audit event to S3: {e}",
                extra={
                    "action": event.action,
                    "resource_type": event.resource_type,
                    "resource_id": event.resource_id,
                    "error": str(e)
                }
            )
            if not self._fail_open:
                raise
            return False
        except Exception as e:
            logger.error(f"Unexpected error logging audit to S3: {e}")
            if not self._fail_open:
                raise
            return False
    
    def log_batch(self, events: List[AuditEvent]) -> bool:
        """
        Log multiple audit events.
        
        Note: S3 doesn't have native batch write, so this iterates
        through events. For high-volume scenarios, consider using
        DynamoDB or a queue-based approach.
        
        Args:
            events: List of audit events to log
            
        Returns:
            True if all events were logged successfully
        """
        if not self._enabled:
            return True
        
        if not events:
            return True
        
        success = True
        for event in events:
            if not self.log(event):
                success = False
        
        return success
    
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
        
        Note: S3 is not optimized for queries. This method lists objects
        and filters, which is inefficient for large datasets.
        For query-heavy workloads, use DynamoDBAuditLogger.
        
        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            limit: Maximum number of events to return
            start_key: Not supported for S3
            
        Returns:
            List of audit events (may be empty or incomplete)
        """
        logger.warning(
            "S3AuditLogger.query_by_resource is not available. "
            "Consider using DynamoDBAuditLogger for query-heavy workloads."
        )
        # S3 is not designed for queries - return empty list
        # Users should use DynamoDB for query capabilities
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
        Query audit events for a specific user.
        
        Note: Not efficiently supported by S3. Use DynamoDBAuditLogger.
        """
        logger.warning(
            "S3AuditLogger.query_by_user is not available. "
            "Consider using DynamoDBAuditLogger for query-heavy workloads."
        )
        return []
    
    def query_by_tenant(
        self,
        tenant_id: str,
        *,
        limit: int = 100,
        start_key: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """
        Query all audit events for a tenant.
        
        This method can list objects by tenant prefix, but is still
        not as efficient as DynamoDB for large datasets.
        
        Args:
            tenant_id: Tenant to query
            limit: Maximum number of events to return
            start_key: Continuation token from previous query
            
        Returns:
            List of audit events for the tenant
        """
        try:
            prefix = f"{self._prefix}/tenant={tenant_id}/"
            
            paginator = self._s3_client.get_paginator("list_objects_v2")
            
            events = []
            for page in paginator.paginate(
                Bucket=self._bucket_name,
                Prefix=prefix,
                PaginationConfig={"MaxItems": limit}
            ):
                for obj in page.get("Contents", []):
                    try:
                        response = self._s3_client.get_object(
                            Bucket=self._bucket_name,
                            Key=obj["Key"]
                        )
                        body = response["Body"].read().decode("utf-8")
                        data = json.loads(body)
                        # AuditEvent is now AuditLog, use map() instead of from_dict
                        event = AuditEvent()
                        event.map(data)
                        events.append(event)
                    except Exception as e:
                        logger.warning(f"Failed to read audit log {obj['Key']}: {e}")
                        continue
                    
                    if len(events) >= limit:
                        break
                
                if len(events) >= limit:
                    break
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to query audit by tenant from S3: {e}")
            return []
    
    def _generate_key(self, event: AuditEvent) -> str:
        """
        Generate S3 key for audit event.
        
        Format: {prefix}/tenant={tenant_id}/year={YYYY}/month={MM}/day={DD}/{audit_id}.json
        
        This hierarchical structure allows:
        - Easy browsing by tenant
        - Time-based partitioning for lifecycle rules
        - Efficient prefix-based listing
        """
        # Use event timestamp or current time
        # AuditEvent is now AuditLog which uses created_utc_ts
        if event.created_utc_ts:
            dt = datetime.fromtimestamp(event.created_utc_ts, UTC)
        else:
            dt = datetime.now(UTC)
        
        return (
            f"{self._prefix}/"
            f"tenant={event.tenant_id}/"
            f"year={dt.year}/"
            f"month={dt.month:02d}/"
            f"day={dt.day:02d}/"
            f"{event.id}.json"
        )
