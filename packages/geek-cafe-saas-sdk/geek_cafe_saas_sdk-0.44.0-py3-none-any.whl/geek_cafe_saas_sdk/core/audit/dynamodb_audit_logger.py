"""
DynamoDB Audit Logger - Stores audit events in DynamoDB.

This implementation stores audit events in a dedicated DynamoDB table
with proper indexing for compliance queries.

Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.dynamodb.dynamodb_index import DynamoDBKey
from aws_lambda_powertools import Logger

from .audit_event import AuditEvent
from .audit_log_model import AuditLog

if TYPE_CHECKING:
    from geek_cafe_saas_sdk.core.request_context import RequestContext

logger = Logger()


class DynamoDBAuditLogger:
    """
    Audit logger that stores events in DynamoDB.
    
    Features:
    - Stores audit events in dedicated table (separate from business data)
    - Supports batch writes for efficiency
    - Provides query methods for compliance reporting
    - Fail-safe: logging errors don't break business operations
    
    Table Requirements:
    - Primary Key: pk (String), sk (String)
    - GSI1: gsi1_pk, gsi1_sk (query by resource)
    - GSI2: gsi2_pk, gsi2_sk (query by tenant)
    - GSI3: gsi3_pk, gsi3_sk (query by user)
    
    Example:
        logger = DynamoDBAuditLogger(
            dynamodb=DynamoDB(),
            table_name="audit-logs"
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
        dynamodb: Optional[DynamoDB] = None,
        table_name: str,
        request_context: Optional["RequestContext"] = None,
        fail_open: bool = True
    ):
        """
        Initialize DynamoDB audit logger.
        
        Args:
            dynamodb: DynamoDB client instance (creates new if not provided)
            table_name: Name of the audit log table
            request_context: Security context for query access control.
                           Required for query methods (query_by_resource, query_by_user, query_by_tenant).
                           Not required for log/log_batch (write operations).
            fail_open: If True, logging failures don't raise exceptions
                      (recommended for production to not break business ops)
        """
        self._dynamodb = dynamodb or DynamoDB()
        self._table_name = table_name
        self._request_context = request_context
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
        Log a single audit event to DynamoDB.
        
        Args:
            event: The audit event to log (AuditEvent is an alias for AuditLog)
            
        Returns:
            True if logging succeeded, False otherwise
        """
        if not self._enabled:
            return True
        
        try:
            # AuditEvent is now AuditLog, so we can use it directly
            # Prepare for save (generates id, timestamps, keys)
            event.prep_for_save()
            
            # Save to DynamoDB
            self._dynamodb.save(table_name=self._table_name, item=event)
            
            logger.debug(
                "Audit event logged",
                extra={
                    "audit_id": event.id,
                    "action": event.action,
                    "resource_type": event.resource_type,
                    "resource_id": event.resource_id
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to log audit event: {e}",
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
    
    def log_batch(self, events: List[AuditEvent]) -> bool:
        """
        Log multiple audit events in a batch.
        
        Args:
            events: List of audit events to log (AuditEvent is an alias for AuditLog)
            
        Returns:
            True if all events were logged successfully
        """
        if not self._enabled:
            return True
        
        if not events:
            return True
        
        try:
            # AuditEvent is now AuditLog, so we can use them directly
            for event in events:
                event.prep_for_save()
            
            # Use batch write for efficiency
            # DynamoDB batch_write handles chunking into 25-item batches
            self._dynamodb.batch_write(
                table_name=self._table_name,
                items=events
            )
            
            logger.debug(f"Batch logged {len(events)} audit events")
            return True
            
        except Exception as e:
            logger.error(f"Failed to batch log audit events: {e}")
            if not self._fail_open:
                raise
            return False
    
    def _require_audit_access(self, tenant_id: Optional[str] = None) -> None:
        """
        Require audit log access (admin or auditor role).
        
        Args:
            tenant_id: Optional tenant ID for tenant-scoped queries.
                      If provided, tenant auditors can only query their own tenant.
        
        Raises:
            PermissionError: If user lacks audit access
            ValueError: If request_context not provided
        """
        if self._request_context is None:
            raise ValueError(
                "request_context is required for audit log queries. "
                "Provide it in __init__ or use a write-only logger."
            )
        
        # Platform admins and platform auditors can query anything
        if self._request_context.is_platform_admin() or self._request_context.is_platform_auditor():
            return
        
        # Tenant admins and tenant auditors can only query their own tenant
        if self._request_context.is_tenant_admin() or self._request_context.is_tenant_auditor():
            if tenant_id is None:
                # No tenant specified - allow (will be filtered by tenant in query)
                return
            if tenant_id == self._request_context.authenticated_tenant_id:
                return
            raise PermissionError(
                f"Access denied: Tenant auditors can only query audit logs for their own tenant. "
                f"Requested: {tenant_id}, Your tenant: {self._request_context.authenticated_tenant_id}"
            )
        
        raise PermissionError(
            "Access denied: Audit log queries require admin or auditor role. "
            f"Your roles: {self._request_context.roles}"
        )

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
        
        Requires: Platform admin, platform auditor, tenant admin, or tenant auditor role.
        Tenant-level roles can only query resources within their tenant.
        
        Args:
            resource_type: Type of resource (e.g., "file", "user")
            resource_id: ID of the resource
            limit: Maximum number of events to return
            start_key: Pagination key for continued queries
            
        Returns:
            List of audit events for the resource, ordered by timestamp descending
            
        Raises:
            PermissionError: If user lacks audit access
            ValueError: If request_context not provided
        """
        # Resource queries don't have tenant context upfront, so we check after
        # fetching and filter results for tenant-scoped users
        self._require_audit_access()
        
        try:
            # Build GSI1 key: resource_type#resource_id
            gsi_pk = DynamoDBKey.build_key(
                ("resource", resource_type),
                ("id", resource_id)
            )
            
            query_params = {
                "TableName": self._table_name,
                "IndexName": "gsi1",
                "KeyConditionExpression": "gsi1_pk = :pk",
                "ExpressionAttributeValues": {":pk": {"S": gsi_pk}},
                "ScanIndexForward": False,  # Descending (newest first)
                "Limit": limit
            }
            
            if start_key:
                query_params["ExclusiveStartKey"] = start_key
            
            response = self._dynamodb.client.query(**query_params)
            
            # Deserialize DynamoDB items
            from boto3.dynamodb.types import TypeDeserializer
            deserializer = TypeDeserializer()
            items = [
                {k: deserializer.deserialize(v) for k, v in item.items()}
                for item in response.get("Items", [])
            ]
            
            # AuditEvent is now AuditLog, so return them directly
            events = []
            user_tenant_id = self._request_context.authenticated_tenant_id if self._request_context else None
            is_tenant_scoped = (
                self._request_context and
                not self._request_context.is_platform_admin() and
                not self._request_context.is_platform_auditor()
            )
            
            for item in items:
                audit_log = AuditLog()
                audit_log.map(item)
                
                # Filter for tenant-scoped users
                if is_tenant_scoped and audit_log.tenant_id != user_tenant_id:
                    continue
                    
                events.append(audit_log)
            
            return events
            
        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"Failed to query audit by resource: {e}")
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
        
        Requires: Platform admin, platform auditor, tenant admin, or tenant auditor role.
        Tenant-level roles can only query users within their tenant.
        
        Args:
            tenant_id: Tenant context
            user_id: User ID to query
            limit: Maximum number of events to return
            start_key: Pagination key for continued queries
            
        Returns:
            List of audit events by the user, ordered by timestamp descending
            
        Raises:
            PermissionError: If user lacks audit access or tries to query another tenant
            ValueError: If request_context not provided
        """
        self._require_audit_access(tenant_id)
        
        try:
            # Build GSI3 key: tenant#user_id
            gsi_pk = DynamoDBKey.build_key(
                ("tenant", tenant_id),
                ("user", user_id)
            )
            
            query_params = {
                "TableName": self._table_name,
                "IndexName": "gsi3",
                "KeyConditionExpression": "gsi3_pk = :pk",
                "ExpressionAttributeValues": {":pk": {"S": gsi_pk}},
                "ScanIndexForward": False,
                "Limit": limit
            }
            
            if start_key:
                query_params["ExclusiveStartKey"] = start_key
            
            response = self._dynamodb.client.query(**query_params)
            
            # Deserialize DynamoDB items
            from boto3.dynamodb.types import TypeDeserializer
            deserializer = TypeDeserializer()
            items = [
                {k: deserializer.deserialize(v) for k, v in item.items()}
                for item in response.get("Items", [])
            ]
            
            # AuditEvent is now AuditLog, so return them directly
            events = []
            for item in items:
                audit_log = AuditLog()
                audit_log.map(item)
                events.append(audit_log)
            
            return events
            
        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"Failed to query audit by user: {e}")
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
        
        Requires: Platform admin, platform auditor, tenant admin, or tenant auditor role.
        Tenant-level roles can only query their own tenant.
        
        Args:
            tenant_id: Tenant to query
            limit: Maximum number of events to return
            start_key: Pagination key for continued queries
            
        Returns:
            List of audit events for the tenant, ordered by timestamp descending
            
        Raises:
            PermissionError: If user lacks audit access or tries to query another tenant
            ValueError: If request_context not provided
        """
        self._require_audit_access(tenant_id)
        
        try:
            # Build GSI2 key: tenant_id
            gsi_pk = DynamoDBKey.build_key(("tenant", tenant_id))
            
            query_params = {
                "TableName": self._table_name,
                "IndexName": "gsi2",
                "KeyConditionExpression": "gsi2_pk = :pk",
                "ExpressionAttributeValues": {":pk": {"S": gsi_pk}},
                "ScanIndexForward": False,
                "Limit": limit
            }
            
            if start_key:
                query_params["ExclusiveStartKey"] = start_key
            
            response = self._dynamodb.client.query(**query_params)
            
            # Deserialize DynamoDB items
            from boto3.dynamodb.types import TypeDeserializer
            deserializer = TypeDeserializer()
            items = [
                {k: deserializer.deserialize(v) for k, v in item.items()}
                for item in response.get("Items", [])
            ]
            
            # AuditEvent is now AuditLog, so return them directly
            events = []
            for item in items:
                audit_log = AuditLog()
                audit_log.map(item)
                events.append(audit_log)
            
            return events
            
        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"Failed to query audit by tenant: {e}")
            return []
