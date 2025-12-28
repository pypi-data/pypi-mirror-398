"""
FileVersion model for file versioning system.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from boto3_assist.utilities.string_utility import StringUtility
import datetime as dt
from typing import Optional, Dict, Any
from geek_cafe_saas_sdk.core.models.base_model import BaseModel


class FileVersion(BaseModel):
    """
    File version metadata.
    
    Tracks explicit versions when using "explicit" versioning strategy.
    For "s3_native" strategy, tracks S3 version IDs for reference.
    
    Access Patterns (DynamoDB Keys):
    - pk: FILE#{tenant_id}#{file_id}
    - sk: VERSION#{version_number}
    - gsi1_pk: FILE#{tenant_id}#{file_id}
    - gsi1_sk: VERSION#{version_number}
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._file_id: str | None = None  # Parent file ID
        self._version_id: str | None = None  # Unique version identifier
        self._version_number: int = 1  # Sequential version number (1, 2, 3...)
        
        # S3 Location
        self._s3_key: str | None = None  # S3 key for this version (explicit versioning)
        self._s3_version_id: str | None = None  # S3 version ID (s3_native versioning)
        self._s3_bucket: str | None = None  # S3 bucket (for convenience)
        
        # Version Information
        self._file_size: int = 0  # Size of this version in bytes
        self._checksum: str | None = None  # MD5/SHA256 checksum
        self._mime_type: str | None = None  # MIME type
        
        # Change Information
        self._created_by: str | None = None  # User who created this version
        self._change_description: str | None = None  # Optional description of changes
        
        # State
        self._is_current: bool = False  # Is this the current version?
        self._status: str = "active"  # "active", "archived"
        
        # Timestamps (inherited from BaseModel)
        # created_utc_ts - when this version was created
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for file version queries."""
        
        # Primary index: Version by ID
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("file_version", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("version", self.id))
        self.indexes.add_primary(primary)
        
        # GSI1: Versions by file (ordered by version number)
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("file", self.file_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("version", self.version_number))
        self.indexes.add_secondary(gsi)
    
    # Properties - Identity
    @property
    def file_id(self) -> str | None:
        """Parent file ID."""
        return self._file_id
    
    @file_id.setter
    def file_id(self, value: str | None):
        self._file_id = value
    
    @property
    def version_id(self) -> str | None:
        """Unique version identifier."""
        return self._version_id or self.id
    
    @version_id.setter
    def version_id(self, value: str | None):
        self._version_id = value
        if value:
            self.id = value
    
    @property
    def version_number(self) -> int:
        """Sequential version number."""
        return self._version_number
    
    @version_number.setter
    def version_number(self, value: int):
        self._version_number = value if value is not None else 1
    
    @property
    def version_ts_utc(self) -> float:
        """Version timestamp (UTC epoch seconds) - alias for created_utc_ts for sequential ordering."""
        return self.created_utc_ts
    
    @version_ts_utc.setter
    def version_ts_utc(self, value: float):
        """Set version timestamp - updates created_utc_ts."""
        self.created_utc_ts = value
    
    # Properties - S3 Location
    @property
    def key(self) -> str | None:
        """S3 key for this version."""
        return self._s3_key
    
    @key.setter
    def key(self, value: str | None):
        self._s3_key = value
    
    @property
    def s3_version_id(self) -> str | None:
        """S3 version ID (for s3_native strategy)."""
        return self._s3_version_id
    
    @s3_version_id.setter
    def s3_version_id(self, value: str | None):
        self._s3_version_id = value
    
    @property
    def bucket(self) -> str | None:
        """S3 bucket name."""
        return self._s3_bucket
    
    @bucket.setter
    def bucket(self, value: str | None):
        self._s3_bucket = value
    
    # Properties - Version Information
    @property
    def file_size(self) -> int:
        """Size of this version in bytes."""
        return self._file_size
    
    @file_size.setter
    def file_size(self, value: int):
        self._file_size = value if value is not None else 0
    
    @property
    def size(self) -> int:
        """Alias for file_size."""
        return self._file_size
    
    @size.setter
    def size(self, value: int):
        """Alias for file_size."""
        self._file_size = value if value is not None else 0
    
    @property
    def checksum(self) -> str | None:
        """File checksum."""
        return self._checksum
    
    @checksum.setter
    def checksum(self, value: str | None):
        self._checksum = value
    
    @property
    def mime_type(self) -> str | None:
        """MIME type."""
        return self._mime_type
    
    @mime_type.setter
    def mime_type(self, value: str | None):
        self._mime_type = value
    
    # Properties - Change Information
    @property
    def created_by(self) -> str | None:
        """User who created this version."""
        return self._created_by
    
    @created_by.setter
    def created_by(self, value: str | None):
        self._created_by = value
    
    @property
    def change_description(self) -> str | None:
        """Description of changes in this version."""
        return self._change_description
    
    @change_description.setter
    def change_description(self, value: str | None):
        self._change_description = value
    
    # Properties - State
    @property
    def is_current(self) -> bool:
        """Is this the current version?"""
        return self._is_current
    
    @is_current.setter
    def is_current(self, value: bool):
        self._is_current = bool(value)
    
    @property
    def status(self) -> str:
        """Version status: 'active' or 'archived'."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        if value not in ["active", "archived"]:
            raise ValueError(f"Invalid status: {value}. Must be 'active' or 'archived'")
        self._status = value
