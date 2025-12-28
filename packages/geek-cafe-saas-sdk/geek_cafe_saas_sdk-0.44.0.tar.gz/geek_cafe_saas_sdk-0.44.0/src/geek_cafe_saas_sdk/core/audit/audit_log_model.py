"""
Audit Log DynamoDB Model for persistent audit storage.

This model is used by DynamoDBAuditLogger to store audit events
in DynamoDB with proper indexing for queries.

Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from typing import Dict, Any, Optional, List
from geek_cafe_saas_sdk.core.models.base_model import BaseModel


class AuditLog(BaseModel):
    """
    DynamoDB model for audit log entries.
    
    Designed for 21 CFR Part 11 compliance with immutable audit records.
    
    Multi-Tenancy:
    - Actor: The user/tenant performing the action (actor_tenant_id, actor_user_id)
    - Resource Owner: The user/tenant whose data is being modified (tenant_id, user_id)
    
    Access Patterns (DynamoDB Keys):
    - pk: audit#{audit_id} - Primary lookup
    - sk: metadata
    - gsi1: Audit by resource (resource_type#resource_id) sorted by timestamp
    - gsi2: Audit by tenant sorted by timestamp
    - gsi3: Audit by actor (actor_tenant#actor_user) sorted by timestamp
    - gsi4: Audit by resource owner user (tenant#user_id) sorted by timestamp
    
    Note: This model is stored in a SEPARATE table from business data
    to ensure audit trail integrity and prevent accidental modification.
    """
    
    # Audit logs should never be modified after creation
    _required_properties = ["tenant_id", "actor_user_id", "action", "resource_type", "resource_id"]
    
    def __init__(self) -> None:
        super().__init__()
        
        # Actor (who performed the action)
        self.actor_tenant_id: str = ""  # Tenant/organization of the actor
        self.actor_user_id: str = ""  # User who performed the action
        self.actor_email: str = ""  # Email of actor (denormalized)
        self.actor_name: str = ""  # Display name of actor (denormalized)
        
        # Resource owner (whose data is being modified)
        self.tenant_id: str = ""  # Tenant/organization that owns the resource
        self.user_id: str = ""  # User who owns the resource (e.g., owner_id)
        
        # Action details
        self.action: str = ""  # CREATE, UPDATE, DELETE, etc.
        self.resource_type: str = ""  # file, directory, user, etc.
        self.resource_id: str = ""
        self.resource_name: str = ""
        self.resource_class_name: str = "" # the actual class name of the resource
        # Change tracking (stored as JSON)
        self._old_values: Dict[str, Any] = {}
        self._new_values: Dict[str, Any] = {}
        self._changed_fields: List[str] = []
        
        # Request context
        self.ip_address: str = ""
        self.user_agent: str = ""
        self.request_id: str = ""
        
        # Additional context
        self._audit_metadata: Dict[str, Any] = {}
        self.service_name: str = ""
        self.source_table_name: str = ""  # Table that was modified
        
        # Compliance fields
        self.signature_meaning: Optional[str] = None
        self.signature_hash: Optional[str] = None
        
        # Result
        self.success: bool = True
        self.error_message: str = ""
        
        # Setup indexes
        self._setup_indexes()
    
    @property
    def old_values(self) -> Dict[str, Any]:
        """Get old values (before state)."""
        return self._old_values
    
    @old_values.setter
    def old_values(self, value: Dict[str, Any]) -> None:
        """Set old values."""
        self._old_values = value if value else {}
    
    @property
    def new_values(self) -> Dict[str, Any]:
        """Get new values (after state)."""
        return self._new_values
    
    @new_values.setter
    def new_values(self, value: Dict[str, Any]) -> None:
        """Set new values."""
        self._new_values = value if value else {}
    
    @property
    def changed_fields(self) -> List[str]:
        """Get list of changed fields."""
        return self._changed_fields
    
    @changed_fields.setter
    def changed_fields(self, value: List[str]) -> None:
        """Set changed fields."""
        self._changed_fields = value if value else []
    
    @property
    def audit_metadata(self) -> Dict[str, Any]:
        """Get audit metadata."""
        return self._audit_metadata
    
    @audit_metadata.setter
    def audit_metadata(self, value: Dict[str, Any]) -> None:
        """Set audit metadata."""
        self._audit_metadata = value if value else {}
    
    def compute_changed_fields(self) -> List[str]:
        """
        Compute which fields changed between old_values and new_values.
        
        Returns:
            List of field names that differ between old and new values
        """
        if not self._old_values or not self._new_values:
            return []
        
        changed = []
        all_keys = set(self._old_values.keys()) | set(self._new_values.keys())
        
        for key in all_keys:
            old_val = self._old_values.get(key)
            new_val = self._new_values.get(key)
            if old_val != new_val:
                changed.append(key)
        
        self._changed_fields = changed
        return changed
    
    def _setup_indexes(self) -> None:
        """
        Setup DynamoDB indexes for audit log queries.
        
        Indexes:
        - primary: AUDIT#{id} / METADATA
        - gsi1: resource_type#resource_id / timestamp (query by resource)
        - gsi2: tenant_id / timestamp (query by tenant)
        - gsi3: tenant_id#user_id / timestamp (query by user)
        """
        # Primary index
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("audit", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Query by resource (resource_type#resource_id / timestamp)
        gsi1 = DynamoDBIndex()
        gsi1.name = "gsi1"
        gsi1.partition_key.attribute_name = f"{gsi1.name}_pk"
        gsi1.partition_key.value = lambda: DynamoDBKey.build_key(
            ("resource", self.resource_type),
            ("id", self.resource_id)
        )
        gsi1.sort_key.attribute_name = f"{gsi1.name}_sk"
        gsi1.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi1)
        
        # GSI2: Query by tenant (tenant_id / timestamp)
        gsi2 = DynamoDBIndex()
        gsi2.name = "gsi2"
        gsi2.partition_key.attribute_name = f"{gsi2.name}_pk"
        gsi2.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id)
        )
        gsi2.sort_key.attribute_name = f"{gsi2.name}_sk"
        gsi2.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi2)
        
        # GSI3: Query by actor (actor_tenant#actor_user / timestamp)
        gsi3 = DynamoDBIndex()
        gsi3.name = "gsi3"
        gsi3.partition_key.attribute_name = f"{gsi3.name}_pk"
        gsi3.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.actor_tenant_id),
            ("user", self.actor_user_id)
        )
        gsi3.sort_key.attribute_name = f"{gsi3.name}_sk"
        gsi3.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi3)
        
        # GSI4: Query by resource owner user (tenant#user_id / timestamp)
        gsi4 = DynamoDBIndex()
        gsi4.name = "gsi4"
        gsi4.partition_key.attribute_name = f"{gsi4.name}_pk"
        gsi4.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("owner", self.user_id)
        )
        gsi4.sort_key.attribute_name = f"{gsi4.name}_sk"
        gsi4.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi4)
