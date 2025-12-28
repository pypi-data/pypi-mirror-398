"""
Resource metadata entry model for extending any resource with additional metadata.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from typing import Dict, Optional
from dataclasses import dataclass
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


@dataclass
class IndexConfig:
    """
    Configuration for a single DynamoDB index.

    Allows consumers to customize index names, attribute names, and enable/disable indexes.

    Example:
        # Disable an index
        ResourceMetaEntry.INDEX_CONFIG["gsi6"].enabled = False

        # Rename an index
        ResourceMetaEntry.INDEX_CONFIG["gsi1"].name = "resources_by_owner"
        ResourceMetaEntry.INDEX_CONFIG["gsi1"].pk_attribute = "resources_by_owner_pk"
        ResourceMetaEntry.INDEX_CONFIG["gsi1"].sk_attribute = "resources_by_owner_sk"
    """

    key: str  # Internal key for lookup (e.g., "gsi1", "gsi2")
    name: str  # DynamoDB index name
    pk_attribute: str  # Partition key attribute name
    sk_attribute: str  # Sort key attribute name
    enabled: bool = True  # Whether this index is enabled
    description: str = ""  # Human-readable description

    def __post_init__(self):
        # Default attribute names based on index name if not provided
        if not self.pk_attribute:
            self.pk_attribute = f"{self.name}_pk"
        if not self.sk_attribute:
            self.sk_attribute = f"{self.name}_sk"


class ResourceMetaEntry(BaseTenantUserModel):
    """
    Extended metadata entry for any resource.

    Use this when you want to add additional metadata to any resource without
    overloading the original record. The id of the record should match the
    resource it extends. You can create multiple metadata entries per resource,
    each distinguished by a unique key.

    Multi-Tenancy:
    - tenant_id: Organization/company (can have multiple users)
    - owner_id: Specific user within the tenant who owns this entry

    Index Configuration:
    Indexes can be customized via the INDEX_CONFIG class attribute. Each index can be:
    - Renamed (change name and attribute names)
    - Disabled (set enabled=False)

    Access Patterns (DynamoDB Keys):
    - pk: resource#{resource_id}
    - sk: metadata#key#{key-name}

    Usage Examples:
        # File metadata extension
        entry = ResourceMetaEntry()
        entry.id = file_id
        entry.key = "thumbnails"
        entry.metadata = {"small": "url1", "large": "url2"}

        # User preferences extension
        entry = ResourceMetaEntry()
        entry.id = user_id
        entry.key = "preferences"
        entry.metadata = {"theme": "dark", "language": "en"}

        # Order metadata extension
        entry = ResourceMetaEntry()
        entry.id = order_id
        entry.key = "shipping_updates"
        entry.metadata = {"carrier": "UPS", "tracking": "1Z999..."}
    """

    # Default index configuration - can be overridden by subclasses
    INDEX_CONFIG: Dict[str, IndexConfig] = None  # Set in get_default_index_config()

    @classmethod
    def get_default_index_config(cls) -> Dict[str, IndexConfig]:
        """
        Get the default index configuration.

        Call this to get a fresh copy of the default config that can be modified.
        Subclasses should override this to customize indexes.

        Returns:
            Dict mapping index keys to IndexConfig objects
        """
        return {}

    def _get_index_config(self, key: str) -> Optional[IndexConfig]:
        """
        Get index configuration for a given key.

        Uses instance INDEX_CONFIG if set, otherwise uses class default.

        Args:
            key: Index key (e.g., "gsi1")

        Returns:
            IndexConfig or None if not found
        """
        config = self.INDEX_CONFIG or self.get_default_index_config()
        return config.get(key)

    def _is_index_enabled(self, key: str) -> bool:
        """
        Check if an index is enabled.

        Args:
            key: Index key (e.g., "gsi1")

        Returns:
            True if enabled, False otherwise
        """
        config = self._get_index_config(key)
        return config.enabled if config else False

    def __init__(self):
        super().__init__()

        # Meta Information
        self._name: str | None = None  # Display name (e.g., "config data")
        self._key: str | None = None  # The Dictionary Key Name "config_data"
        self._description: str | None = None
        self._resource_type: str | None = None # The type of resource this metadata extends (e.g., "file", "user", "order")
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()

        # were done initializing / force properties to exist
        object.__setattr__(self, "_initializing", False)
        object.__setattr__(self, "_init_complete", True)

    def _setup_indexes(self):
        """Setup DynamoDB indexes for resource metadata queries."""

        # Primary index: Resource by ID (always enabled)
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("resource", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            ("metadata", ""), ("key", self.key)
        )
        self.indexes.add_primary(primary)

    # Properties - Meta Information

    @property
    def name(self) -> str | None:
        """Display name."""
        return self._name

    @name.setter
    def name(self, value: str | None):
        self._name = value

    @property
    def key(self) -> str | None:
        """Metadata Key."""
        return self._key

    @key.setter
    def key(self, value: str | None):
        self._key = value

    @property
    def description(self) -> str | None:
        """Description of this metadata entry."""
        return self._description

    @description.setter
    def description(self, value: str | None):
        self._description = value

    @property
    def resource_type(self) -> str | None:
        """Resource type of this metadata entry."""
        return self._resource_type

    @resource_type.setter
    def resource_type(self, value: str | None):
        self._resource_type = value

    
    @property
    def resource_id(self) -> str | None:
        """Resource ID of this metadata entry - same as id."""
        return self.id
    
    @resource_id.setter
    def resource_id(self, value: str):
        self.id = value