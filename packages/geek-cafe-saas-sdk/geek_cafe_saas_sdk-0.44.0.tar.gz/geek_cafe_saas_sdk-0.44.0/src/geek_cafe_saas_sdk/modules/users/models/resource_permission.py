"""
Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.

ResourcePermission model for ABAC (Attribute-Based Access Control).
Grants specific permissions to users on specific resources.
"""

from typing import List, Dict, Any
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_model import BaseModel


class ResourcePermission(BaseModel):
    """
    Resource-level permission grant.
    
    Allows granting specific permissions to users on specific resources.
    Supports resource sharing and delegation.
    
    Examples:
    - Grant "events:write" to user-456 on event-789
    - Grant "chat:admin" to user-123 on channel-abc
    - Grant "analytics:read" to user-999 on tenant-def
    
    Access Patterns:
    - Get grants for user on resource (GSI1: user + resource)
    - List all user's grants (GSI2: user only)
    - List all grants on resource (GSI3: resource only)
    - Check specific grant (primary key)
    """
    
    def __init__(self):
        super().__init__()
        
        # Who has access
        self._user_id: str | None = None
        self._tenant_id: str | None = None
        
        # What they can access
        self._resource_type: str | None = None  # "event", "chat_channel", "group", etc.
        self._resource_id: str | None = None
        
        # What they can do
        self._permissions: List[str] = []  # ["read", "write", "delete"]
        
        # Context
        self._granted_by: str | None = None  # User ID who granted this
        self._granted_at: int | None = None  # UTC timestamp
        self._expires_at: int | None = None  # Optional expiration
        self._reason: str | None = None  # Why granted
        
        # Metadata
        self._metadata: Dict[str, Any] = {}
        
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for resource permission queries."""
        
        # Primary index: specific grant
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("user", self.user_id),
            ("resource", self.resource_type),
            ("resource_id", self.resource_id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            ("grant", self.id)
        )
        self.indexes.add_primary(primary)
        
        # GSI1: User's grants on a specific resource
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("user", self.user_id)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("resource", self.resource_type),
            ("resource_id", self.resource_id)
        )
        self.indexes.add_secondary(gsi)
        
        # GSI2: All grants for a user (across all resources)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("user_grants", self.user_id)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("resource", self.resource_type),
            ("resource_id", self.resource_id),
            ("grant", self.id)
        )
        self.indexes.add_secondary(gsi)
        
        # GSI3: All grants on a resource (who has access)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("resource", self.resource_type),
            ("resource_id", self.resource_id)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("user", self.user_id)
        )
        self.indexes.add_secondary(gsi)
        
        # GSI4: Grants by tenant (for admin view)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi4"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("resource", self.resource_type),
            ("resource_id", self.resource_id),
            ("user", self.user_id)
        )
        self.indexes.add_secondary(gsi)
    
    # User ID
    @property
    def user_id(self) -> str | None:
        """User being granted access."""
        return self._user_id
    
    @user_id.setter
    def user_id(self, value: str | None):
        self._user_id = value
    
    # Tenant ID
    @property
    def tenant_id(self) -> str | None:
        """Tenant context for the grant."""
        return self._tenant_id
    
    @tenant_id.setter
    def tenant_id(self, value: str | None):
        self._tenant_id = value
    
    # Resource Type
    @property
    def resource_type(self) -> str | None:
        """Type of resource (e.g., 'event', 'chat_channel')."""
        return self._resource_type
    
    @resource_type.setter
    def resource_type(self, value: str | None):
        self._resource_type = value
    
    # Resource ID
    @property
    def resource_id(self) -> str | None:
        """ID of the specific resource."""
        return self._resource_id
    
    @resource_id.setter
    def resource_id(self, value: str | None):
        self._resource_id = value
    
    # Permissions
    @property
    def permissions(self) -> List[str]:
        """Permissions granted (e.g., ['read', 'write'])."""
        return self._permissions
    
    @permissions.setter
    def permissions(self, value: List[str]):
        self._permissions = value if value else []
    
    # Granted By
    @property
    def granted_by(self) -> str | None:
        """User ID who granted this permission."""
        return self._granted_by
    
    @granted_by.setter
    def granted_by(self, value: str | None):
        self._granted_by = value
    
    # Granted At
    @property
    def granted_at(self) -> int | None:
        """UTC timestamp when granted."""
        return self._granted_at
    
    @granted_at.setter
    def granted_at(self, value: int | None):
        self._granted_at = value
    
    # Expires At
    @property
    def expires_at(self) -> int | None:
        """UTC timestamp when grant expires (None = never)."""
        return self._expires_at
    
    @expires_at.setter
    def expires_at(self, value: int | None):
        self._expires_at = value
    
    # Reason
    @property
    def reason(self) -> str | None:
        """Reason for granting permission."""
        return self._reason
    
    @reason.setter
    def reason(self, value: str | None):
        self._reason = value
    
    # Metadata
    @property
    def metadata(self) -> Dict[str, Any]:
        """Additional metadata."""
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]):
        self._metadata = value if value else {}
    
    # Helper Methods
    
    def is_expired(self) -> bool:
        """Check if grant has expired."""
        if self.expires_at is None:
            return False
        import time
        return time.time() > self.expires_at
    
    def has_permission(self, permission: str) -> bool:
        """Check if grant includes specific permission."""
        return permission in self.permissions
