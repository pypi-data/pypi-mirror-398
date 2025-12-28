"""
Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.

Permission model for fine-grained access control.
Supports extensible permission definitions.
"""

from typing import Dict, Any
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_model import BaseModel


class Permission(BaseModel):
    """
    Permission definition model.
    
    Defines individual permissions that can be granted to roles or users.
    Extensible - applications can register custom permissions.
    
    Examples:
    - events:read, events:write, events:delete
    - chat:send_message, chat:manage_channel
    - analytics:view_dashboard
    
    Access Patterns:
    - Get permission by code (primary key)
    - List all permissions (scan/query all)
    - List permissions by category (GSI1)
    """
    
    def __init__(self):
        super().__init__()
        
        # Core fields
        self._code: str | None = None  # Unique code: "events:read"
        self._name: str | None = None  # Display name: "Read Events"
        self._description: str | None = None
        self._category: str | None = None  # "events", "chat", "analytics", etc.
        
        # Metadata
        self._is_system: bool = True  # System permissions can't be deleted
        self._metadata: Dict[str, Any] = {}
        
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for permission queries."""
        
        # Primary index: permission by code
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("permission", self.code)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            ("permission", self.code)
        )
        self.indexes.add_primary(primary)
        
        # GSI1: Permissions by category
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("permission_category", self.category or "uncategorized")
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("code", self.code)
        )
        self.indexes.add_secondary(gsi)
    
    # Code
    @property
    def code(self) -> str | None:
        """Permission code (e.g., 'events:read')."""
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
        """Permission description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    # Category
    @property
    def category(self) -> str | None:
        """Permission category (e.g., 'events', 'chat')."""
        return self._category
    
    @category.setter
    def category(self, value: str | None):
        self._category = value
    
    # Is System
    @property
    def is_system(self) -> bool:
        """Whether this is a system permission (cannot be deleted)."""
        return self._is_system
    
    @is_system.setter
    def is_system(self, value: bool):
        self._is_system = value
    
    # Metadata
    @property
    def metadata(self) -> Dict[str, Any]:
        """Additional metadata."""
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]):
        self._metadata = value if value else {}
