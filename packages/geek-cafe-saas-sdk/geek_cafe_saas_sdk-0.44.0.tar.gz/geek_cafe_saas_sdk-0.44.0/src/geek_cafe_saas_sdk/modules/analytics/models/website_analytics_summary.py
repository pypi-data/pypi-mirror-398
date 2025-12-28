from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from typing import Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_model import BaseTenantModel


class WebsiteAnalyticsSummary(BaseTenantModel):
    """
    Model for storing aggregated website analytics data.
    
    This model stores hourly/daily summaries of analytics data for efficient querying.
    Aggregated by an EventBridge scheduled job via the tally service.
    """
    
    def __init__(self):
        super().__init__()
        self._route: str | None = None  # URL route this summary is for
        self._slug: str | None = None  # Slug for the page
        self._analytics_type: str = "general"  # Type of analytics summarized
        self._period_start_ts: float | None = None  # Start of aggregation period
        self._period_end_ts: float | None = None  # End of aggregation period
        self._period_type: str = "hourly"  # hourly, daily, weekly, monthly
        
        # Aggregated metrics
        self._total_events: int = 0  # Total number of events in period
        self._unique_sessions: int = 0  # Number of unique sessions
        self._unique_users: int = 0  # Number of unique users
        
        # Aggregated data - flexible storage for computed metrics
        self._metrics: Dict[str, Any] = {}
        
        # Additional metadata
        self._content: Dict[str, Any] = {}
        
        self._setup_indexes()

    def _setup_indexes(self):
        # Primary index: summary by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("analytics-summary", self.id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("analytics-summary", self.id))
        self.indexes.add_primary(primary)
        
        ## GSI: 1
        # GSI: all analytics summaries sorted by period start
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("analytics-summary", "all"))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("period", self.period_start_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 2
        # GSI: summaries by route/slug for page-specific queries
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("route", self.route or self.slug)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("period", self.period_start_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 3
        # GSI: summaries by tenant sorted by period
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "analytics-summary"), ("period", self.period_start_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 4
        # GSI: summaries by type and period
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi4"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("analytics-type", self.analytics_type)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("period", self.period_start_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 5
        # GSI: summaries by tenant, type, and period for filtered queries
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi5"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id), ("type", self.analytics_type)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("period", self.period_start_ts)
        )
        self.indexes.add_secondary(gsi)

    @property
    def route(self) -> str | None:
        return self._route

    @route.setter
    def route(self, value: str | None):
        self._route = value
    
    @property
    def slug(self) -> str | None:
        return self._slug

    @slug.setter
    def slug(self, value: str | None):
        self._slug = value
    
    @property
    def analytics_type(self) -> str:
        return self._analytics_type

    @analytics_type.setter
    def analytics_type(self, value: str):
        self._analytics_type = value
    
    @property
    def period_start_ts(self) -> float | None:
        return self._period_start_ts

    @period_start_ts.setter
    def period_start_ts(self, value: float | None):
        self._period_start_ts = value
    
    @property
    def period_end_ts(self) -> float | None:
        return self._period_end_ts

    @period_end_ts.setter
    def period_end_ts(self, value: float | None):
        self._period_end_ts = value
    
    @property
    def period_type(self) -> str:
        return self._period_type

    @period_type.setter
    def period_type(self, value: str):
        self._period_type = value
    
    @property
    def total_events(self) -> int:
        return self._total_events

    @total_events.setter
    def total_events(self, value: int):
        self._total_events = value
    
    @property
    def unique_sessions(self) -> int:
        return self._unique_sessions

    @unique_sessions.setter
    def unique_sessions(self, value: int):
        self._unique_sessions = value
    
    @property
    def unique_users(self) -> int:
        return self._unique_users

    @unique_users.setter
    def unique_users(self, value: int):
        self._unique_users = value
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Get metrics (boto3-assist v0.30.0+ auto-converts Decimals to float)."""
        return self._metrics

    @metrics.setter
    def metrics(self, value: Dict[str, Any]):
        """Set metrics."""
        self._metrics = value if value is not None else {}
    
    @property
    def content(self) -> Dict[str, Any]:
        return self._content

    @content.setter
    def content(self, value: Dict[str, Any]):
        self._content = value
    
    # Helper methods
    def get_metric(self, key: str, default: Any = None) -> Any:
        """Get a specific metric value."""
        return self.metrics.get(key, default)
    
    def set_metric(self, key: str, value: Any):
        """Set a specific metric value."""
        self.metrics[key] = value
    
    def calculate_average(self, metric_key: str) -> float:
        """Calculate average for a metric stored as a list."""
        values = self.metrics.get(metric_key, [])
        if not values or not isinstance(values, list):
            return 0.0
        return sum(values) / len(values)
