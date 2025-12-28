"""
File model for file storage system.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel
from datetime import datetime


@dataclass
class IndexConfig:
    """
    Configuration for a single DynamoDB index.
    
    Allows consumers to customize index names, attribute names, and enable/disable indexes.
    
    Example:
        # Disable an index
        File.INDEX_CONFIG["gsi6"].enabled = False
        
        # Rename an index
        File.INDEX_CONFIG["gsi1"].name = "files_by_owner"
        File.INDEX_CONFIG["gsi1"].pk_attribute = "files_by_owner_pk"
        File.INDEX_CONFIG["gsi1"].sk_attribute = "files_by_owner_sk"
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

class File(BaseTenantUserModel):
    """
    File metadata and references.
    
    Represents a file in the system with metadata, virtual path, and S3 location.
    Does not contain file data (stored in S3) - only metadata and references.
    
    Multi-Tenancy:
    - tenant_id: Organization/company (can have multiple users)
    - owner_id: Specific user within the tenant who owns this file
    
    Index Configuration:
    Indexes can be customized via the INDEX_CONFIG class attribute. Each index can be:
    - Renamed (change name and attribute names)
    - Disabled (set enabled=False)
    
    Example - Disable an index:
        class MyFile(File):
            INDEX_CONFIG = File.get_default_index_config()
            INDEX_CONFIG["gsi6"].enabled = False
    
    Example - Rename an index:
        class MyFile(File):
            INDEX_CONFIG = File.get_default_index_config()
            INDEX_CONFIG["gsi1"].name = "files_by_owner"
            INDEX_CONFIG["gsi1"].pk_attribute = "files_by_owner_pk"
            INDEX_CONFIG["gsi1"].sk_attribute = "files_by_owner_sk"
    
    Access Patterns (DynamoDB Keys):
    - pk: FILE#{file_id}
    - sk: metadata
    - gsi1: Files by owner, sorted by created_utc_ts
    - gsi2: Files by category
    - gsi3: Files by root_id (lineage)
    - gsi4: Files by parent_id (lineage)
    - gsi5: Files by directory_id
    - gsi6: Files by virtual_path
    
    Versioning:
    - Uses explicit versioning with unique S3 keys per version
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
        return {
            "gsi1": IndexConfig(
                key="gsi1",
                name="gsi1",
                pk_attribute="gsi1_pk",
                sk_attribute="gsi1_sk",
                enabled=True,
                description="Files by owner, sorted by created_utc_ts"
            ),
            "gsi2": IndexConfig(
                key="gsi2",
                name="gsi2",
                pk_attribute="gsi2_pk",
                sk_attribute="gsi2_sk",
                enabled=True,
                description="Files by category"
            ),
            "gsi3": IndexConfig(
                key="gsi3",
                name="gsi3",
                pk_attribute="gsi3_pk",
                sk_attribute="gsi3_sk",
                enabled=True,
                description="Files by root_id (lineage)"
            ),
            "gsi4": IndexConfig(
                key="gsi4",
                name="gsi4",
                pk_attribute="gsi4_pk",
                sk_attribute="gsi4_sk",
                enabled=True,
                description="Files by parent_id (lineage)"
            ),
            "gsi5": IndexConfig(
                key="gsi5",
                name="gsi5",
                pk_attribute="gsi5_pk",
                sk_attribute="gsi5_sk",
                enabled=True,
                description="Files by directory_id"
            ),
            "gsi6": IndexConfig(
                key="gsi6",
                name="gsi6",
                pk_attribute="gsi6_pk",
                sk_attribute="gsi6_sk",
                enabled=True,
                description="Files by directory_id and virtual path"
            ),
            "gsi7": IndexConfig(
                key="gsi7",
                name="gsi7",
                pk_attribute="gsi7_pk",
                sk_attribute="gsi7_sk",
                enabled=True,
                description="GSI7: Files by virtual_path and name."
            ),
        }
    
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
        
        # Identity (inherited from BaseModel: id, tenant_id)
        
        
        # File Information
        self._name: str | None = None  # Display name (e.g., "report.pdf")
        self._mime_type: str | None = None  # MIME type (e.g., "application/pdf")
        self._size: int = 0  # Size in bytes
        self._checksum: str | None = None  # MD5/SHA256 checksum
        
        # Virtual Location (logical structure in DynamoDB)
        self._directory_id: str | None = None  # Parent directory ID (null = root)
        self._virtual_path: str | None = None  # Full virtual path (/docs/reports/Q1.pdf)
        
        # S3 Physical Location
        self._bucket: str | None = None  # S3 bucket name
        self._key: str | None = None  # S3 object key (physical location)
        
        # Versioning
        self._version_id: str | None = None  # Version identifier (user-set or from S3)
        
        # Metadata
        self._description: str | None = None  # Optional description
        
        
        # status - Lifecycle/visibility state
        self._status: str | None = "active"  # "active", "pending", "archived", "deleted"

        # state - Processing/operational state  
        self._state: str | None = "ready"  # "ready", "uploading", "processing", "validating", "converting", "failed"
        
        # Lineage Tracking (for data processing pipelines)
        self._lineage: str = "original"  # "original" or "derived", "versioned" (can add "child" for multi-level)
        self._parent_id: str | None = None  # Parent file in hierarchy (None for root files)
        self._root_id: str | None = None  # Root file in hierarchy (self.id for root files)

        # category
        self._category: str | None = None  # category (e.g., "analytics", "analysis-input", "reports", "documents")
        # visibility        
        self._visibility: str = "private"  # "private" | "tenant" | "public" | "system"
        # retention_policy
        self._retention_policy: str | None = "permanent"  # "none" | "temporary" | "permanent" | "legal-hold" | "retain-90-days" | "retain-permanently"
        
        self._is_hidden: bool = False  # True if the file should not be visible in the UI
                    
        self._allowed_status: List[str] = ["active", "archived", "deleted", "pending"]  # List of allowed states
        
        self._uploaded_utc_ts: int | None = None  # UTC timestamp of when the file was uploaded
        self._uploaded_utc: datetime | None = None  # UTC datetime of when the file was uploaded
        self.uploaded_by_id: str | None = None  # User ID who uploaded the file

        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()

        # were done initializing / force properties to exist
        object.__setattr__(self, '_initializing', False)
        object.__setattr__(self, '_init_complete', True)
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for file queries."""
        
        # Primary index: File by ID (always enabled)
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("file", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Files by owner, sorted by created_utc_ts
        self._setup_gsi1()
        
        # GSI2: Files by category
        self._setup_gsi2()
        
        # GSI3: Files by root_id (lineage)
        self._setup_gsi3()
        
        # GSI4: Files by parent_id (lineage)
        self._setup_gsi4()
        
        # GSI5: Files by directory_id
        self._setup_gsi5()
        
        # GSI6: Files by virtual_path
        self._setup_gsi6()

        # GSI7: Files by virtual_path and name
        self._setup_gsi7()
    
    def _setup_gsi1(self):
        """GSI1: Files by owner, sorted by created_utc_ts."""
        config = self._get_index_config("gsi1")
        if not config or not config.enabled:
            return
        
        gsi = DynamoDBIndex()
        gsi.name = config.name
        gsi.partition_key.attribute_name = config.pk_attribute
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id), ("owner", self.owner_id))
        gsi.sort_key.attribute_name = config.sk_attribute
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("ts", self.created_utc_ts))
        self.indexes.add_secondary(gsi)
    
    def _setup_gsi2(self):
        """GSI2: Files by status and virtual path."""
        config = self._get_index_config("gsi2")
        if not config or not config.enabled:
            return
        
        gsi = DynamoDBIndex()
        gsi.name = config.name
        gsi.partition_key.attribute_name = config.pk_attribute
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id), ("owner", self.owner_id))
        gsi.sort_key.attribute_name = config.sk_attribute
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("status", self.status), ("file", self.virtual_path))
        self.indexes.add_secondary(gsi)

    def _setup_gsi3(self):
        """GSI3: Files by category, status, and virtual path."""
        config = self._get_index_config("gsi3")
        if not config or not config.enabled:
            return
        
        gsi = DynamoDBIndex()
        gsi.name = config.name
        gsi.partition_key.attribute_name = config.pk_attribute
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id), ("owner", self.owner_id))
        gsi.sort_key.attribute_name = config.sk_attribute
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("category", self.category), ("status", self.status),("file", self.virtual_path))
        self.indexes.add_secondary(gsi)
    
    def _setup_gsi4(self):
        """GSI4: Files by root_id (lineage)."""
        config = self._get_index_config("gsi4")
        if not config or not config.enabled:
            return
        
        gsi = DynamoDBIndex()
        gsi.name = config.name
        gsi.partition_key.attribute_name = config.pk_attribute
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id), ("owner", self.owner_id))
        gsi.sort_key.attribute_name = config.sk_attribute
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("root", self.root_id), ("ts", self.created_utc_ts))
        self.indexes.add_secondary(gsi)
    
    def _setup_gsi5(self):
        """GSI5: Files by parent_id (lineage)."""
        config = self._get_index_config("gsi5")
        if not config or not config.enabled:
            return
        
        gsi = DynamoDBIndex()
        gsi.name = config.name
        gsi.partition_key.attribute_name = config.pk_attribute
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id), ("owner", self.owner_id))
        gsi.sort_key.attribute_name = config.sk_attribute
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("parent", self.parent_id), ("ts", self.created_utc_ts))
        self.indexes.add_secondary(gsi)
    
    def _setup_gsi6(self):
        """GSI6: Files by directory_id and virtual path."""
        config = self._get_index_config("gsi6")
        if not config or not config.enabled:
            return
        
        gsi = DynamoDBIndex()
        gsi.name = config.name
        gsi.partition_key.attribute_name = config.pk_attribute
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("owner", self.owner_id))
        gsi.sort_key.attribute_name = config.sk_attribute
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("directory", self.directory_id), ("file", self.virtual_path))
        self.indexes.add_secondary(gsi)
    
    def _setup_gsi7(self):
        """GSI7: Files by virtual_path and name."""
        config = self._get_index_config("gsi7")
        if not config or not config.enabled:
            return
        
        gsi = DynamoDBIndex()
        gsi.name = config.name
        gsi.partition_key.attribute_name = config.pk_attribute
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("owner", self.owner_id))
        gsi.sort_key.attribute_name = config.sk_attribute
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("directory", self.virtual_path), ("file", self.name))
        self.indexes.add_secondary(gsi)

    
    
    # Properties - File Information
    @property
    def name(self) -> str | None:
        """Display file name."""
        return self._name
    
    @name.setter
    def name(self, value: str | None):
        self._name = value
    
    @property
    def extension(self) -> str | None:
        """File extension computed from name (e.g., '.pdf')."""
        if not self._name:
            return None
        from pathlib import Path
        suffix = Path(self._name).suffix
        return suffix if suffix else None
    
    @extension.setter
    def extension(self, value: str | None):
        """Setter for DynamoDB serialization - does nothing."""
        pass
    
    @property
    def mime_type(self) -> str | None:
        """MIME type (e.g., 'application/pdf')."""
        return self._mime_type
    
    @mime_type.setter
    def mime_type(self, value: str | None):
        self._mime_type = value
    
    @property
    def size(self) -> int:
        """File size in bytes."""
        return self._size
    
    @size.setter
    def size(self, value: int):
        self._size = value if value is not None else 0
    
    @property
    def checksum(self) -> str | None:
        """File checksum (MD5/SHA256)."""
        return self._checksum
    
    @checksum.setter
    def checksum(self, value: str | None):
        self._checksum = value
    
    # Properties - Virtual Location
    @property
    def directory_id(self) -> str | None:
        """Parent directory ID (null = root)."""
        return self._directory_id
    
    @directory_id.setter
    def directory_id(self, value: str | None):
        self._directory_id = value
    
    @property
    def virtual_path(self) -> str | None:
        """Full virtual path (e.g., /docs/reports/Q1.pdf)."""
        return self._virtual_path
    
    @virtual_path.setter
    def virtual_path(self, value: str | None):
        self._virtual_path = value
    
    # Properties - S3 Physical Location
    @property
    def bucket(self) -> str | None:
        """S3 bucket name."""
        return self._bucket
    
    @bucket.setter
    def bucket(self, value: str | None):
        self._bucket = value
    
    @property
    def key(self) -> str | None:
        """S3 object key (physical location)."""
        return self._key
    
    @key.setter
    def key(self, value: str | None):
        self._key = value
    
    # Properties - Versioning
    @property
    def version_id(self) -> str | None:
        """Version identifier (can be user-set or from S3)."""
        return self._version_id
    
    @version_id.setter
    def version_id(self, value: str | None):
        self._version_id = value
    
    @property
    def version_ts_utc(self) -> float:
        """Version timestamp (UTC epoch seconds) - alias for created_utc_ts for sequential version ordering."""
        return self.created_utc_ts
    
    @version_ts_utc.setter
    def version_ts_utc(self, value: float):
        """Set version timestamp - updates created_utc_ts."""
        self.created_utc_ts = value
    
    # Properties - Metadata
    @property
    def description(self) -> str | None:
        """File description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
        
    
    # Properties - status
    @property
    def status(self) -> str:
        """
        File status: 'active', 'archived', 'deleted', "pending".
        If you need different statuses, add or override the _allowed_status list.
        """
        return self._status
    
    @status.setter
    def status(self, value: str):
        if value:
            value = value.lower()
        else:
            # allow for None (needed for queries)
            self._status = None
            return

        if value not in self._allowed_status:
            raise ValueError(f"Invalid status: {value}. Must be in {self._allowed_status}")
        self._status = value
    

    # Properties - state
    @property
    def state(self) -> str:
        """File state: 'ready', 'evaluating', 'validating', 'converting', 'processing', 'failed', 'deleted'."""
        return self._state
    
    @state.setter
    def state(self, value: str):
        # if value not in ["ready", "evaluating", "validating", "converting", "processing", "failed", "deleted"]:
        #     raise ValueError(f"Invalid state: {value}. Must be 'ready', 'evaluating', 'validating', 'converting', 'processing', 'failed', or 'deleted'")
        self._state = value
    
    # Properties - Lineage Tracking
    @property
    def lineage(self) -> str:
        """File lineage: 'original' or 'derived'."""
        return self._lineage
    
    @lineage.setter
    def lineage(self, value: str | None):
        # if value not in ["original", "derived"]:
        #     raise ValueError(f"Invalid lineage: {value}. Must be 'original' or 'derived'")
        self._lineage = value
    
    @property
    def root_id(self) -> str | None:
        """Root file in hierarchy (self.id for root files)."""
        return self._root_id or self.id 
    
    @root_id.setter
    def root_id(self, value: str | None):
        self._root_id = value

    @property
    def parent_id(self) -> str | None:
        """Parent file in hierarchy (None for root/original files)."""
        return self._parent_id
    
    @parent_id.setter
    def parent_id(self, value: str | None):
        self._parent_id = value
    
    @property
    def category(self) -> str | None:
        """Get the category of the file."""
        return self._category
    
    @category.setter
    def category(self, value: str | None):
        self._category = value

    @property
    def visibility(self) -> str:
        """Get the visibility of the file."""
        return self._visibility
    
    @visibility.setter
    def visibility(self, value: str):
        if value not in ["private", "tenant", "public", "system"]:
            raise ValueError(f"Invalid visibility: {value}. Must be 'private', 'tenant', 'public', or 'system'")
        self._visibility = value
    
    @property
    def retention_policy(self) -> str | None:
        """Get the retention_policy of the file."""
        return self._retention_policy
    
    @retention_policy.setter
    def retention_policy(self, value: str | None):
        self._retention_policy = value

    @property
    def is_hidden(self) -> bool:
        """Get the is_hidden of the file."""
        return self._is_hidden
    
    @is_hidden.setter
    def is_hidden(self, value: bool):
        self._is_hidden = value

    @property
    def content_type(self) -> str| None:
        """Get the is_deleted of the file."""
        return self._mime_type
    
    @content_type.setter
    def content_type(self, value: str | None):
        self._mime_type = value

    @property
    def uploaded_utc(self) -> datetime | str | None:
        """Get the uploaded_utc of the file."""
        return self._uploaded_utc
    
    @uploaded_utc.setter
    def uploaded_utc(self, value: datetime |str  | None):
        self._uploaded_utc = self._safe_date_conversion(value)
    
    @property
    def uploaded_utc_ts(self) -> int | None:
        """Get the uploaded_utc_ts of the file."""
        return self._uploaded_utc_ts
    
    @uploaded_utc_ts.setter
    def uploaded_utc_ts(self, value: int | None):
        self._uploaded_utc_ts = self._safe_number_conversion(value)

   
    
    