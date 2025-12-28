"""
KeywordSearch Model - Searchable keyword index for any resource.

This model provides a DynamoDB-backed keyword search capability for resources
like files, projects, tasks, etc. It enables tenant-wide and user-scoped
keyword searches with efficient reverse lookups for keyword refresh.

Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from dataclasses import dataclass, field
from typing import Optional, List
import re

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey

from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


@dataclass
class IndexConfig:
    """Configuration for a DynamoDB index."""
    key: str
    name: str
    pk_attribute: str
    sk_attribute: str
    enabled: bool = True
    description: str = ""


def normalize_keyword(keyword: str) -> str:
    """
    Normalize a keyword for consistent storage and searching.
    
    - Lowercase
    - Strip whitespace
    - Remove special characters (keep alphanumeric, hyphens, underscores)
    
    Args:
        keyword: Raw keyword string
        
    Returns:
        Normalized keyword string
    """
    if not keyword:
        return ""
    
    # Lowercase and strip
    normalized = keyword.lower().strip()
    
    # Remove special characters except hyphens and underscores
    normalized = re.sub(r'[^a-z0-9\-_]', '', normalized)
    
    return normalized


def extract_keywords(text: str, min_length: int = 2) -> List[str]:
    """
    Extract and normalize keywords from a text string.
    
    Args:
        text: Text to extract keywords from
        min_length: Minimum keyword length (default 2)
        
    Returns:
        List of unique normalized keywords
    """
    if not text:
        return []
    
    # Split on whitespace and common delimiters
    words = re.split(r'[\s,;.!?\-_/\\|]+', text)
    
    # Normalize and filter
    keywords = set()
    for word in words:
        normalized = normalize_keyword(word)
        if len(normalized) >= min_length:
            keywords.add(normalized)
    
    return sorted(keywords)


class KeywordSearch(BaseTenantUserModel):
    """
    Keyword search index entry for a resource.
    
    This model stores keyword-to-resource mappings that enable:
    - Tenant-wide keyword searches (primary index)
    - User-scoped keyword searches (GSI1)
    - Reverse lookups by resource for keyword refresh (GSI2)
    
    Key Design:
    - Primary: pk=tenant#keyword, sk=resource_type#resource_id#field
    - GSI1: pk=tenant#user#keyword, sk=resource_type#resource_id#field
    - GSI2: pk=tenant#resource_type#resource_id, sk=keyword#field
    
    Example:
        # Create a keyword entry for a file
        entry = KeywordSearch()
        entry.tenant_id = "tenant_123"
        entry.normalized_keyword = "report"
        entry.resource_type = "file"
        entry.resource_id = "file_456"
        entry.field = "title"  # optional
        entry.user_id = "user_789"  # optional, for user-scoped searches
    """
    
    # Default index configuration
    DEFAULT_INDEX_CONFIG: dict = field(default_factory=lambda: {
        "primary": IndexConfig(
            key="primary",
            name="primary",
            pk_attribute="pk",
            sk_attribute="sk",
            enabled=True,
            description="Tenant-wide keyword search"
        ),
        "gsi1": IndexConfig(
            key="gsi1",
            name="gsi1",
            pk_attribute="gsi1_pk",
            sk_attribute="gsi1_sk",
            enabled=True,
            description="User-scoped keyword search"
        ),
        "gsi2": IndexConfig(
            key="gsi2",
            name="gsi2",
            pk_attribute="gsi2_pk",
            sk_attribute="gsi2_sk",
            enabled=True,
            description="Reverse lookup by resource"
        ),
    })
    
    def __init__(self, index_config: Optional[dict] = None):
        """
        Initialize KeywordSearch model.
        
        Args:
            index_config: Optional custom index configuration
        """
        super().__init__()
        
        # Index configuration
        self._index_config = index_config or self._get_default_index_config()
        
        # Core attributes
        self._normalized_keyword: str = ""
        self._resource_type: str = ""
        self._resource_id: str = ""
        self._field: Optional[str] = None
        
        # Original keyword (before normalization) for display
        self._original_keyword: Optional[str] = None
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    @classmethod
    def _get_default_index_config(cls) -> dict:
        """Get default index configuration."""
        return {
            "primary": IndexConfig(
                key="primary",
                name="primary",
                pk_attribute="pk",
                sk_attribute="sk",
                enabled=True,
                description="Tenant-wide keyword search"
            ),
            "gsi1": IndexConfig(
                key="gsi1",
                name="gsi1",
                pk_attribute="gsi1_pk",
                sk_attribute="gsi1_sk",
                enabled=True,
                description="User-scoped keyword search"
            ),
            "gsi2": IndexConfig(
                key="gsi2",
                name="gsi2",
                pk_attribute="gsi2_pk",
                sk_attribute="gsi2_sk",
                enabled=True,
                description="Reverse lookup by resource"
            ),
        }
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for keyword search queries."""
        
        # Primary index: Tenant + Keyword → Resources
        self._setup_primary_index()
        
        # GSI1: User + Keyword (user-scoped search)
        self._setup_gsi1()
        
        # GSI2: Resource reverse lookup (for refresh)
        self._setup_gsi2()
    
    def _setup_primary_index(self):
        """
        Primary index: Tenant-wide keyword search.
        
        pk = tenant#{tenant_id}#keyword#{normalized_keyword}
        sk = resource_type#{resource_type}#resource#{resource_id}[#field#{field}]
        """
        config = self._index_config.get("primary")
        if not config or not config.enabled:
            return
        
        primary = DynamoDBIndex()
        primary.name = config.name
        primary.partition_key.attribute_name = config.pk_attribute
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("keyword", self.normalized_keyword),
        )
        primary.sort_key.attribute_name = config.sk_attribute
        primary.sort_key.value = lambda: self._build_resource_sk()
        self.indexes.add_primary(primary)
    
    def _setup_gsi1(self):
        """
        GSI1: User-scoped keyword search.
        
        pk = tenant#{tenant_id}#user#{user_id}#keyword#{normalized_keyword}
        sk = resource_type#{resource_type}#resource#{resource_id}[#field#{field}]
        """
        config = self._index_config.get("gsi1")
        if not config or not config.enabled:
            return
        
        gsi = DynamoDBIndex()
        gsi.name = config.name
        gsi.partition_key.attribute_name = config.pk_attribute
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("user", self.user_id),
            ("keyword", self.normalized_keyword),
        )
        gsi.sort_key.attribute_name = config.sk_attribute
        gsi.sort_key.value = lambda: self._build_resource_sk()
        self.indexes.add_secondary(gsi)
    
    def _setup_gsi2(self):
        """
        GSI2: Resource reverse lookup for keyword refresh.
        
        pk = tenant#{tenant_id}#resource_type#{resource_type}#resource#{resource_id}
        sk = keyword#{normalized_keyword}[#field#{field}]
        """
        config = self._index_config.get("gsi2")
        if not config or not config.enabled:
            return
        
        gsi = DynamoDBIndex()
        gsi.name = config.name
        gsi.partition_key.attribute_name = config.pk_attribute
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("resource_type", self.resource_type),
            ("resource", self.resource_id),
        )
        gsi.sort_key.attribute_name = config.sk_attribute
        gsi.sort_key.value = lambda: self._build_keyword_sk()
        self.indexes.add_secondary(gsi)
    
    def _build_resource_sk(self) -> str:
        """Build sort key for resource identification.
        
        When resource_type/resource_id are empty, produces a prefix
        suitable for begins_with queries.
        """
        # Always include resource_type prefix for begins_with support
        if not self.resource_type:
            return DynamoDBKey.build_key(("resource_type", ""))
        if not self.resource_id:
            return DynamoDBKey.build_key(
                ("resource_type", self.resource_type),
                ("resource", ""),
            )
        if self.field:
            return DynamoDBKey.build_key(
                ("resource_type", self.resource_type),
                ("resource", self.resource_id),
                ("field", self.field),
            )
        return DynamoDBKey.build_key(
            ("resource_type", self.resource_type),
            ("resource", self.resource_id),
        )
    
    def _build_keyword_sk(self) -> str:
        """Build sort key for keyword (used in GSI2).
        
        When normalized_keyword is empty, produces a prefix
        suitable for begins_with queries.
        """
        if not self.normalized_keyword:
            return DynamoDBKey.build_key(("keyword", ""))
        if self.field:
            return DynamoDBKey.build_key(
                ("keyword", self.normalized_keyword),
                ("field", self.field),
            )
        return DynamoDBKey.build_key(
            ("keyword", self.normalized_keyword),
        )
    
    # Properties
    
    @property
    def normalized_keyword(self) -> str:
        """Normalized keyword for searching."""
        return self._normalized_keyword
    
    @normalized_keyword.setter
    def normalized_keyword(self, value: str):
        self._normalized_keyword = value
    
    @property
    def resource_type(self) -> str:
        """Type of resource (e.g., 'file', 'project', 'task')."""
        return self._resource_type
    
    @resource_type.setter
    def resource_type(self, value: str):
        self._resource_type = value
    
    @property
    def resource_id(self) -> str:
        """ID of the resource."""
        return self._resource_id
    
    @resource_id.setter
    def resource_id(self, value: str):
        self._resource_id = value
    
    @property
    def field(self) -> Optional[str]:
        """Optional field name where keyword was found (e.g., 'title', 'description')."""
        return self._field
    
    @field.setter
    def field(self, value: Optional[str]):
        self._field = value
    
    @property
    def original_keyword(self) -> Optional[str]:
        """Original keyword before normalization (for display)."""
        return self._original_keyword
    
    @original_keyword.setter
    def original_keyword(self, value: Optional[str]):
        self._original_keyword = value
    
    def set_keyword(self, keyword: str):
        """
        Set keyword with automatic normalization.
        
        Args:
            keyword: Raw keyword string
        """
        self._original_keyword = keyword
        self._normalized_keyword = normalize_keyword(keyword)
