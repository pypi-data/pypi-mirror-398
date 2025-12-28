"""
FeatureFlag model for runtime-configurable feature gating.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import List, Dict, Any, Optional
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_model import BaseModel


class FeatureFlag(BaseModel):
    """
    Runtime-configurable feature flag.

    Access patterns (single-table design):
    - Primary (id): feature_flag#{id} / metadata
    - GSI1 (feature + tenant):
        gsi1_pk = feature#{feature_key}
        gsi1_sk = scope#tenant#{tenant_id}
    - GSI2 (feature + user):
        gsi2_pk = feature#{feature_key}
        gsi2_sk = scope#user#{user_id}
    - GSI3 (feature + everyone):
        gsi3_pk = feature#{feature_key}
        gsi3_sk = scope#everyone
    """

    def __init__(self):
        super().__init__()

        # Identity and scope
        self._feature_key: str | None = None
        self._scope: str | None = None          # 'everyone' | 'tenant' | 'user'
        self._scope_id: str | None = None       # tenant_id or user_id depending on scope

        # Configuration
        self._enabled: bool = False
        self._environments: List[str] | None = None  # ['dev','staging','prod']
        self._permissions_required: List[str] | None = None
        self._percentage: int | None = None     # 0-100 rollout
        self._start_ts: float | None = None     # epoch seconds
        self._end_ts: float | None = None       # epoch seconds

        # Metadata bag
        self._metadata: Dict[str, Any] | None = None

        # IMPORTANT: setup indexes last
        self._setup_indexes()

    def _setup_indexes(self):
        """Define primary and GSIs for feature flag queries."""
        # Primary index (by id)
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("feature_flag", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)

        # GSI1: feature + tenant
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("feature", self.feature_key))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("scope", "tenant"), ("tenant", self.tenant_id or self._scope_id))
        self.indexes.add_secondary(gsi)

        # GSI2: feature + user
        gsi = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("feature", self.feature_key))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("scope", "user"), ("user", self._scope_id))
        self.indexes.add_secondary(gsi)

        # GSI3: feature + everyone
        gsi = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("feature", self.feature_key))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("scope", "everyone"))
        self.indexes.add_secondary(gsi)

    # ============ Properties ============

    @property
    def feature_key(self) -> str | None:
        return self._feature_key

    @feature_key.setter
    def feature_key(self, value: str | None):
        self._feature_key = value

    @property
    def scope(self) -> str | None:
        return self._scope

    @scope.setter
    def scope(self, value: str | None):
        if value and value not in ("everyone", "tenant", "user"):
            raise ValueError("scope must be one of 'everyone', 'tenant', or 'user'")
        self._scope = value

    @property
    def scope_id(self) -> str | None:
        return self._scope_id

    @scope_id.setter
    def scope_id(self, value: str | None):
        self._scope_id = value

    @property
    def enabled(self) -> bool:
        return bool(self._enabled)

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = bool(value)

    @property
    def environments(self) -> List[str] | None:
        return self._environments

    @environments.setter
    def environments(self, value: List[str] | None):
        self._environments = value if value else None

    @property
    def permissions_required(self) -> List[str] | None:
        return self._permissions_required

    @permissions_required.setter
    def permissions_required(self, value: List[str] | None):
        self._permissions_required = value if value else None

    @property
    def percentage(self) -> int | None:
        return self._percentage

    @percentage.setter
    def percentage(self, value: int | None):
        if value is None:
            self._percentage = None
            return
        if not (0 <= int(value) <= 100):
            raise ValueError("percentage must be between 0 and 100")
        self._percentage = int(value)

    @property
    def start_ts(self) -> float | None:
        return self._start_ts

    @start_ts.setter
    def start_ts(self, value: float | None):
        self._start_ts = value

    @property
    def end_ts(self) -> float | None:
        return self._end_ts

    @end_ts.setter
    def end_ts(self, value: float | None):
        self._end_ts = value

    @property
    def metadata(self) -> Dict[str, Any] | None:
        return self._metadata

    @metadata.setter
    def metadata(self, value: Dict[str, Any] | None):
        if value is not None and not isinstance(value, dict):
            raise ValueError("metadata must be a dictionary")
        self._metadata = value
