

from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel

class BaseAsyncEventModel(BaseTenantUserModel):
    """
    Base model for asynchronous event handling.
    Provides common properties and methods for event-driven systems.
    """
    
    def __init__(self) -> None:
        self.event_id: str | None = None
        self.event_type: str | None = None
        self.event_name: str | None = None
        self.payload: dict | None = None
        self.created_at: float | None = None
        self.processed_at: float | None = None
        self.status: str = "pending"  # pending, processing, completed, failed
        self.correlation_id: str | None = None  # stays the same across the whole business flow
        self.request_id: str | None = None  # id of the specific event that caused this one
        self.retry_count: int = 0
        self.max_retries: int = 3
        self.action: str | None = None
        self.initiated_by: dict | None = None
        self.performed_by: dict | None = None
        self.claims_snapshot: dict | None = None
        self.privileges: list[str] | None = None
        self.privacy_context: dict | None = None
        super().__init__()
    