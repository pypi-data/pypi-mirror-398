"""
Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.

Role model for RBAC (Role-Based Access Control).
Roles aggregate permissions and can be assigned to users.
"""

from typing import List, Dict, Any
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_model import BaseModel


class Role(BaseModel):
    """
    Role definition model.
    
    Groups permissions together for easy assignment to users.
    Supports hierarchical roles (platform vs tenant-level).
    
    Examples:
    - platform_admin: Full system access
    - tenant_admin: Full access within tenant
    - tenant_user: Standard user permissions
    - tenant_organizer: Enhanced event management
    
    Access Patterns:
    - Get role by code (primary key)
    - List all roles (scan/query all)
    - List roles by scope (GSI1: global vs tenant)
    - List roles by tenant (GSI2: tenant-specific custom roles)
    """
    
    def __init__(self):
        super().__init__()
        
        # Core fields
        self._code: str | None = None  # Unique code: "tenant_admin"
        self._name: str | None = None  # Display name: "Tenant Administrator"
        self._description: str | None = None
        
        # Permissions
        self._permissions: List[str] = []  # List of permission codes
        
        # Scope
        self._scope: str = "tenant"  # "global" or "tenant"
        self._tenant_id: str | None = None  # If tenant-specific custom role
        
        # Hierarchy
        self._inherits_from: List[str] = []  # Role codes to inherit from
        self._level: int = 0  # Hierarchical level (higher = more power)
        
        # Metadata
        self._is_system: bool = True  # System roles can't be deleted
        self._is_assignable: bool = True  # Can be assigned to users
        self._metadata: Dict[str, Any] = {}
        
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for role queries."""
        
        # Primary index: role by code
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("role", self.code)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            ("role", self.code)
        )
        self.indexes.add_primary(primary)
        
        # GSI1: Roles by scope (global vs tenant)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("role_scope", self.scope)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("level", str(self.level).zfill(5)),
            ("code", self.code)
        )
        self.indexes.add_secondary(gsi)
        
        # GSI2: Custom roles by tenant
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id or "system")
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("role", self.code)
        )
        self.indexes.add_secondary(gsi)
    
    # Code
    @property
    def code(self) -> str | None:
        """Role code (e.g., 'tenant_admin')."""
        return self._code
    
    @code.setter
    def code(self, value: str | None):
        self._code = value
    
    # Name
    @property
    def name(self) -> str | None:
        """Display name."""
        return self._name
    
    @name.setter
    def name(self, value: str | None):
        self._name = value
    
    # Description
    @property
    def description(self) -> str | None:
        """Role description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    # Permissions
    @property
    def permissions(self) -> List[str]:
        """List of permission codes."""
        return self._permissions
    
    @permissions.setter
    def permissions(self, value: List[str]):
        self._permissions = value if value else []
    
    # Scope
    @property
    def scope(self) -> str:
        """Role scope: 'global' or 'tenant'."""
        return self._scope
    
    @scope.setter
    def scope(self, value: str):
        if value not in ["global", "tenant"]:
            raise ValueError("Scope must be 'global' or 'tenant'")
        self._scope = value
    
    # Tenant ID
    @property
    def tenant_id(self) -> str | None:
        """Tenant ID for tenant-specific custom roles."""
        return self._tenant_id
    
    @tenant_id.setter
    def tenant_id(self, value: str | None):
        self._tenant_id = value
    
    # Inherits From
    @property
    def inherits_from(self) -> List[str]:
        """Role codes this role inherits from."""
        return self._inherits_from
    
    @inherits_from.setter
    def inherits_from(self, value: List[str]):
        self._inherits_from = value if value else []
    
    # Level
    @property
    def level(self) -> int:
        """Hierarchical level (higher = more power)."""
        return self._level
    
    @level.setter
    def level(self, value: int):
        self._level = value
    
    # Is System
    @property
    def is_system(self) -> bool:
        """Whether this is a system role (cannot be deleted)."""
        return self._is_system
    
    @is_system.setter
    def is_system(self, value: bool):
        self._is_system = value
    
    # Is Assignable
    @property
    def is_assignable(self) -> bool:
        """Whether this role can be assigned to users."""
        return self._is_assignable
    
    @is_assignable.setter
    def is_assignable(self, value: bool):
        self._is_assignable = value
    
    # Metadata
    @property
    def metadata(self) -> Dict[str, Any]:
        """Additional metadata."""
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]):
        self._metadata = value if value else {}
