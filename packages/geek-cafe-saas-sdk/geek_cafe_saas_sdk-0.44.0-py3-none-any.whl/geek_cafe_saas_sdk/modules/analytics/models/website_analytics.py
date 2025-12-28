
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from typing import Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class WebsiteAnalytics(BaseTenantUserModel):
    """
    Model for storing website analytics data.
    
    Supports different analytics types:
    - general: Page views, sessions, user interactions
    - error: Error tracking and debugging info
    - performance: Load times, resource metrics
    - custom: Custom event tracking
    """
    
    def __init__(self):
        super().__init__()
        self._route: str | None = None  # URL route/path (e.g., "/blog/post-123")
        self._slug: str | None = None  # Slug for the page (e.g., "post-123")
        self._analytics_type: str = "general"  # general, error, performance, custom
        self._data: Dict[str, Any] = {}  # Flexible storage for analytics data
        self._session_id: str | None = None
        self._user_agent: str | None = None
        self._ip_address: str | None = None
        self._referrer: str | None = None
        
        self._setup_indexes()

    def _setup_indexes(self):
        # Primary index: analytics by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("analytics", self.id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("analytics", self.id))
        self.indexes.add_primary(primary)
        
        ## GSI: 1
        # GSI: all analytics records sorted by timestamp
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("analytics", "all"))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 2
        # GSI: analytics by route/slug for page-specific queries
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("route", self.route or self.slug)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 3
        # GSI: analytics by tenant sorted by timestamp
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "analytics"), ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 4
        # GSI: analytics by type and timestamp (e.g., all errors, all performance metrics)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi4"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("analytics-type", self.analytics_type)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 5
        # GSI: analytics by tenant and type for filtered queries
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi5"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("type", self.analytics_type), ("ts", self.created_utc_ts)
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
    def data(self) -> Dict[str, Any]:
        return self._data

    @data.setter
    def data(self, value: Dict[str, Any]):
        self._data = value
    
    @property
    def session_id(self) -> str | None:
        return self._session_id

    @session_id.setter
    def session_id(self, value: str | None):
        self._session_id = value
    
    @property
    def user_agent(self) -> str | None:
        return self._user_agent

    @user_agent.setter
    def user_agent(self, value: str | None):
        self._user_agent = value
    
    @property
    def ip_address(self) -> str | None:
        return self._ip_address

    @ip_address.setter
    def ip_address(self, value: str | None):
        self._ip_address = value
    
    @property
    def referrer(self) -> str | None:
        return self._referrer

    @referrer.setter
    def referrer(self, value: str | None):
        self._referrer = value
    
    # Helper methods for different analytics types
    def set_page_view(self, route: str, **kwargs):
        """Set general page view analytics."""
        self.route = route
        self.analytics_type = "general"
        self.data = {
            "event": "page_view",
            "duration_ms": kwargs.get("duration_ms"),
            "scroll_depth": kwargs.get("scroll_depth"),
            **kwargs
        }
    
    def set_error(self, route: str, error_message: str, **kwargs):
        """Set error analytics."""
        self.route = route
        self.analytics_type = "error"
        self.data = {
            "event": "error",
            "error_message": error_message,
            "error_type": kwargs.get("error_type"),
            "stack_trace": kwargs.get("stack_trace"),
            **kwargs
        }
    
    def set_performance(self, route: str, **kwargs):
        """Set performance analytics."""
        self.route = route
        self.analytics_type = "performance"
        self.data = {
            "event": "performance",
            "load_time_ms": kwargs.get("load_time_ms"),
            "ttfb_ms": kwargs.get("ttfb_ms"),  # Time to first byte
            "fcp_ms": kwargs.get("fcp_ms"),  # First contentful paint
            "lcp_ms": kwargs.get("lcp_ms"),  # Largest contentful paint
            **kwargs
        }
    
    def set_custom_event(self, route: str, event_name: str, **kwargs):
        """Set custom event analytics."""
        self.route = route
        self.analytics_type = "custom"
        self.data = {
            "event": event_name,
            **kwargs
        }
