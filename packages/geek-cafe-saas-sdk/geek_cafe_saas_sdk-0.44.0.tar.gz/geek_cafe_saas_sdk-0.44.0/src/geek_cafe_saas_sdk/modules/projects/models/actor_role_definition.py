"""
ActorRoleDefinition model for tenant-configurable project roles.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Optional
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class ActorRoleDefinition(BaseTenantUserModel):
    """
    ActorRoleDefinition model for configurable project roles.
    
    Defines roles that can be assigned to project actors (e.g., PM, Developer, Analyst).
    Roles are tenant-specific, allowing each tenant to customize their role definitions.
    
    Access Patterns (DynamoDB Keys):
    - pk: tenant#{tenant_id}
    - sk: role#{code}
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._code: str | None = None  # Machine-friendly code (e.g., "pm", "dev")
        
        # Role Information
        self._name: str | None = None  # Display name (e.g., "Project Manager")
        self._description: str | None = None
        
        # Flags
        self._is_default: bool = False  # Auto-assign to new projects
        self._is_system_defined: bool = False  # Protected from deletion/rename
        self._is_active: bool = True
        
        # Display
        self._sort_order: int = 0  # For UI ordering
        self._color: str | None = None  # UI color code
        self._icon: str | None = None  # UI icon identifier
        
        # Model metadata
        self.model_name = "actor_role_definition"
        self.model_name_plural = "actor_role_definitions"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for role definition queries."""
        
        # Primary index: Role by tenant and code
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("role", self.code or ""))
        self.indexes.add_primary(primary)
    
    # Properties - Identity
    @property
    def code(self) -> str | None:
        """Machine-friendly role code."""
        return self._code
    
    @code.setter
    def code(self, value: str | None):
        self._code = value.lower() if value else None
    
    # Properties - Role Information
    @property
    def name(self) -> str | None:
        """Display name for the role."""
        return self._name
    
    @name.setter
    def name(self, value: str | None):
        self._name = value
    
    @property
    def description(self) -> str | None:
        """Role description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    # Properties - Flags
    @property
    def is_default(self) -> bool:
        """Whether this role is auto-assigned to new projects."""
        return self._is_default
    
    @is_default.setter
    def is_default(self, value: bool):
        self._is_default = value if value is not None else False
    
    @property
    def is_system_defined(self) -> bool:
        """Whether this role is protected from deletion/rename."""
        return self._is_system_defined
    
    @is_system_defined.setter
    def is_system_defined(self, value: bool):
        self._is_system_defined = value if value is not None else False
    
    @property
    def is_active(self) -> bool:
        """Whether this role is active."""
        return self._is_active
    
    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = value if value is not None else True
    
    # Properties - Display
    @property
    def sort_order(self) -> int:
        """Sort order for UI display."""
        return self._sort_order
    
    @sort_order.setter
    def sort_order(self, value: int):
        self._sort_order = value if value is not None else 0
    
    @property
    def color(self) -> str | None:
        """UI color code."""
        return self._color
    
    @color.setter
    def color(self, value: str | None):
        self._color = value
    
    @property
    def icon(self) -> str | None:
        """UI icon identifier."""
        return self._icon
    
    @icon.setter
    def icon(self, value: str | None):
        self._icon = value
    
    # Helper Methods
    def can_delete(self) -> bool:
        """Check if this role can be deleted."""
        return not self._is_system_defined
    
    def can_rename(self) -> bool:
        """Check if this role can be renamed."""
        return not self._is_system_defined


# Default system roles
DEFAULT_ROLES = [
    {"code": "pm", "name": "Project Manager", "is_default": True, "is_system_defined": True, "sort_order": 1},
    {"code": "dev", "name": "Developer", "is_default": False, "is_system_defined": True, "sort_order": 2},
    {"code": "analyst", "name": "Analyst", "is_default": False, "is_system_defined": True, "sort_order": 3},
    {"code": "designer", "name": "Designer", "is_default": False, "is_system_defined": True, "sort_order": 4},
    {"code": "qa", "name": "QA Engineer", "is_default": False, "is_system_defined": True, "sort_order": 5},
    {"code": "stakeholder", "name": "Stakeholder", "is_default": False, "is_system_defined": True, "sort_order": 6},
]
