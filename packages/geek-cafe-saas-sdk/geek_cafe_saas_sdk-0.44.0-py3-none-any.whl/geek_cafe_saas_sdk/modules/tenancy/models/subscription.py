"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.

Subscription model for tenant billing and plan management.
"""


from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from datetime import datetime, timezone
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class Subscription(BaseTenantUserModel):
    """
    Subscription/billing model for tenant plans.
    
    Tracks subscription history with one active subscription per tenant.
    Uses date-sorted SK in GSI1 to maintain sortable history.
    
    Key Features:
    - Full billing history (all subscriptions for a tenant)
    - Active subscription pointer (separate item for O(1) access)
    - Trial period tracking
    - Billing period management
    - Payment status tracking
    
    Access Patterns:
    - Get subscription by ID (primary key)
    - List subscription history for tenant (GSI1, date-sorted)
    - Query subscriptions by status (GSI2, for billing jobs)
    - Get active subscription via pointer item
    
    Active Subscription Pointer:
    - Separate DynamoDB item with SK="subscription#active"
    - Contains active_subscription_id for O(1) lookups
    - Updated atomically with TransactWrite when subscription changes
    """
    
    def __init__(self):
        super().__init__()
        # tenant_id inherited from BaseModel
        
        # Subscription status
        self._status: str = "trial"  # trial|active|past_due|canceled|expired
        
        # Plan details (NEW: References platform-wide Plan model)
        self._plan_id: str | None = None  # Reference to subscriptions.Plan.id
        self._plan_code: str | None = None  # "free"|"basic"|"pro"|"enterprise"
        self._plan_name: str | None = None  # Display name
        self._seat_count: int = 1  # Number of users/seats
        
        # Addons (NEW: Support for add-on modules)
        self._active_addons: list[str] = []  # List of active addon codes
        self._addon_metadata: dict[str, dict] = {}  # Per-addon settings
        
        # Discounts (NEW: Promotional discounts)
        self._discount_id: str | None = None  # Reference to subscriptions.Discount.id
        self._discount_code: str | None = None  # Promo code used
        self._discount_amount_cents: int = 0  # Discount applied per period
        
        # Pricing
        self._price_cents: int = 0  # Price in cents (e.g., 2999 = $29.99)
        self._currency: str = "USD"
        self._billing_interval: str = "month"  # month|year
        
        # Trial period
        self._trial_ends_utc_ts: float | None = None
        self._is_trial: bool = False
        
        # Billing periods
        self._current_period_start_utc_ts: float | None = None
        self._current_period_end_utc_ts: float | None = None
        
        # Cancellation
        self._canceled_utc_ts: float | None = None
        self._cancel_at_period_end: bool = False
        self._cancellation_reason: str | None = None
        
        # Payment tracking
        self._last_payment_utc_ts: float | None = None
        self._last_payment_amount_cents: int | None = None
        self._next_billing_utc_ts: float | None = None
        self._payment_method: str | None = None  # "card"|"invoice"|"paypal", etc.
        
        # External billing integration
        self._external_subscription_id: str | None = None  # Stripe, Paddle, etc.
        self._external_customer_id: str | None = None
        
        # Metadata
        self._notes: str | None = None
        
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for efficient subscription queries."""
        
        # Primary index: subscription by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("subscription", self.id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            ("subscription", self.id)
        )
        self.indexes.add_primary(primary)
        
        # GSI1: Subscriptions by tenant (history sorted by period start date)
        # SK includes date prefix for sortable history
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("subscription", self._get_date_prefix()),
            ("id", self.id)
        )
        self.indexes.add_secondary(gsi)
        
        # GSI2: Subscriptions by status (for billing queries/jobs)
        # Sorted by next_billing_date for processing queues
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("subscription_status", self.status)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("next_billing", self.next_billing_utc_ts or 0)
        )
        self.indexes.add_secondary(gsi)
        
        # GSI3: Subscriptions by plan code (for analytics)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("plan_code", self.plan_code or "unknown")
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)
    
    def _get_date_prefix(self) -> str | None:
        """
        Get date prefix for sortable history (yyyyMMdd).
        
        Uses current_period_start_utc_ts if available, otherwise created_utc_ts.
        """
        timestamp = self.current_period_start_utc_ts or self.created_utc_ts
        if timestamp is None or timestamp == 0:
            return None
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.strftime("%Y%m%d")
    
    # Status
    @property
    def status(self) -> str:
        """Subscription status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        valid_statuses = ["trial", "active", "past_due", "canceled", "expired"]
        if value not in valid_statuses:
            raise ValueError(f"Invalid status: {value}. Must be one of {valid_statuses}")
        self._status = value
    
    # Plan ID (NEW)
    @property
    def plan_id(self) -> str | None:
        """Plan ID reference."""
        return self._plan_id
    
    @plan_id.setter
    def plan_id(self, value: str | None):
        self._plan_id = value
    
    # Plan Code
    @property
    def plan_code(self) -> str | None:
        """Plan identifier code."""
        return self._plan_code
    
    @plan_code.setter
    def plan_code(self, value: str | None):
        self._plan_code = value
    
    # Plan Name
    @property
    def plan_name(self) -> str | None:
        """Plan display name."""
        return self._plan_name
    
    @plan_name.setter
    def plan_name(self, value: str | None):
        self._plan_name = value
    
    # Seat Count
    @property
    def seat_count(self) -> int:
        """Number of seats/users."""
        return self._seat_count
    
    @seat_count.setter
    def seat_count(self, value: int):
        if value < 1:
            raise ValueError("seat_count must be at least 1")
        self._seat_count = value
    
    # Price Cents
    @property
    def price_cents(self) -> int:
        """Price in cents."""
        return self._price_cents
    
    @price_cents.setter
    def price_cents(self, value: int):
        if value < 0:
            raise ValueError("price_cents cannot be negative")
        self._price_cents = value
    
    # Currency
    @property
    def currency(self) -> str:
        """Currency code (e.g., USD, EUR)."""
        return self._currency
    
    @currency.setter
    def currency(self, value: str):
        self._currency = value.upper() if value else "USD"
    
    # Billing Interval
    @property
    def billing_interval(self) -> str:
        """Billing interval (month|year)."""
        return self._billing_interval
    
    @billing_interval.setter
    def billing_interval(self, value: str):
        if value not in ["month", "year"]:
            raise ValueError("billing_interval must be 'month' or 'year'")
        self._billing_interval = value
    
    # Trial Ends
    @property
    def trial_ends_utc_ts(self) -> float | None:
        """Trial period end timestamp."""
        return self._trial_ends_utc_ts
    
    @trial_ends_utc_ts.setter
    def trial_ends_utc_ts(self, value: float | None):
        self._trial_ends_utc_ts = value
    
    # Is Trial
    @property
    def is_trial(self) -> bool:
        """Whether subscription is in trial period."""
        return self._is_trial
    
    @is_trial.setter
    def is_trial(self, value: bool):
        self._is_trial = value
    
    # Current Period Start
    @property
    def current_period_start_utc_ts(self) -> float | None:
        """Current billing period start timestamp."""
        return self._current_period_start_utc_ts
    
    @current_period_start_utc_ts.setter
    def current_period_start_utc_ts(self, value: float | None):
        self._current_period_start_utc_ts = value
    
    # Current Period End
    @property
    def current_period_end_utc_ts(self) -> float | None:
        """Current billing period end timestamp."""
        return self._current_period_end_utc_ts
    
    @current_period_end_utc_ts.setter
    def current_period_end_utc_ts(self, value: float | None):
        self._current_period_end_utc_ts = value
    
    # Canceled
    @property
    def canceled_utc_ts(self) -> float | None:
        """Cancellation timestamp."""
        return self._canceled_utc_ts
    
    @canceled_utc_ts.setter
    def canceled_utc_ts(self, value: float | None):
        self._canceled_utc_ts = value
    
    # Cancel at Period End
    @property
    def cancel_at_period_end(self) -> bool:
        """Whether to cancel at end of current period."""
        return self._cancel_at_period_end
    
    @cancel_at_period_end.setter
    def cancel_at_period_end(self, value: bool):
        self._cancel_at_period_end = value
    
    # Cancellation Reason
    @property
    def cancellation_reason(self) -> str | None:
        """Reason for cancellation."""
        return self._cancellation_reason
    
    @cancellation_reason.setter
    def cancellation_reason(self, value: str | None):
        self._cancellation_reason = value
    
    # Last Payment
    @property
    def last_payment_utc_ts(self) -> float | None:
        """Last successful payment timestamp."""
        return self._last_payment_utc_ts
    
    @last_payment_utc_ts.setter
    def last_payment_utc_ts(self, value: float | None):
        self._last_payment_utc_ts = value
    
    # Last Payment Amount
    @property
    def last_payment_amount_cents(self) -> int | None:
        """Last payment amount in cents."""
        return self._last_payment_amount_cents
    
    @last_payment_amount_cents.setter
    def last_payment_amount_cents(self, value: int | None):
        self._last_payment_amount_cents = value
    
    # Next Billing
    @property
    def next_billing_utc_ts(self) -> float | None:
        """Next billing date timestamp."""
        return self._next_billing_utc_ts
    
    @next_billing_utc_ts.setter
    def next_billing_utc_ts(self, value: float | None):
        self._next_billing_utc_ts = value
    
    # Payment Method
    @property
    def payment_method(self) -> str | None:
        """Payment method type."""
        return self._payment_method
    
    @payment_method.setter
    def payment_method(self, value: str | None):
        self._payment_method = value
    
    # External Subscription ID
    @property
    def external_subscription_id(self) -> str | None:
        """External billing provider subscription ID."""
        return self._external_subscription_id
    
    @external_subscription_id.setter
    def external_subscription_id(self, value: str | None):
        self._external_subscription_id = value
    
    # External Customer ID
    @property
    def external_customer_id(self) -> str | None:
        """External billing provider customer ID."""
        return self._external_customer_id
    
    @external_customer_id.setter
    def external_customer_id(self, value: str | None):
        self._external_customer_id = value
    
    # Notes
    @property
    def notes(self) -> str | None:
        """Internal notes about subscription."""
        return self._notes
    
    @notes.setter
    def notes(self, value: str | None):
        self._notes = value
    
    # Active Addons (NEW)
    @property
    def active_addons(self) -> list[str]:
        """List of active addon codes."""
        return self._active_addons
    
    @active_addons.setter
    def active_addons(self, value: list[str]):
        self._active_addons = value if value else []
    
    # Addon Metadata (NEW)
    @property
    def addon_metadata(self) -> dict[str, dict]:
        """Per-addon metadata."""
        return self._addon_metadata
    
    @addon_metadata.setter
    def addon_metadata(self, value: dict[str, dict]):
        self._addon_metadata = value if value else {}
    
    # Discount ID (NEW)
    @property
    def discount_id(self) -> str | None:
        """Discount ID reference."""
        return self._discount_id
    
    @discount_id.setter
    def discount_id(self, value: str | None):
        self._discount_id = value
    
    # Discount Code (NEW)
    @property
    def discount_code(self) -> str | None:
        """Promo code used."""
        return self._discount_code
    
    @discount_code.setter
    def discount_code(self, value: str | None):
        self._discount_code = value
    
    # Discount Amount Cents (NEW)
    @property
    def discount_amount_cents(self) -> int:
        """Discount amount per period in cents."""
        return self._discount_amount_cents
    
    @discount_amount_cents.setter
    def discount_amount_cents(self, value: int):
        if value < 0:
            raise ValueError("discount_amount_cents cannot be negative")
        self._discount_amount_cents = value
    
    # Helper Methods
    
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self._status == "active"
    
    def is_trial_active(self) -> bool:
        """Check if subscription is in active trial."""
        return self._status == "trial"
    
    def is_canceled(self) -> bool:
        """Check if subscription is canceled."""
        return self._status == "canceled"
    
    def is_past_due(self) -> bool:
        """Check if subscription payment is past due."""
        return self._status == "past_due"
    
    def is_expired(self) -> bool:
        """Check if subscription is expired."""
        return self._status == "expired"
    
    def cancel(self, reason: str | None = None, immediate: bool = False):
        """
        Cancel subscription.
        
        Args:
            reason: Optional cancellation reason
            immediate: If True, cancel immediately; if False, cancel at period end
        """
        import datetime as dt
        
        self._status = "canceled"
        self._canceled_utc_ts = dt.datetime.now(dt.UTC).timestamp()
        self._cancellation_reason = reason
        
        if not immediate:
            self._cancel_at_period_end = True
    
    def reactivate(self):
        """Reactivate a canceled subscription."""
        if self._status == "canceled":
            self._status = "active"
            self._canceled_utc_ts = None
            self._cancel_at_period_end = False
            self._cancellation_reason = None
    
    def record_payment(self, amount_cents: int):
        """Record a successful payment."""
        import datetime as dt
        
        self._last_payment_utc_ts = dt.datetime.now(dt.UTC).timestamp()
        self._last_payment_amount_cents = amount_cents
        
        # Update status if was past_due
        if self._status == "past_due":
            self._status = "active"
    
    def mark_past_due(self):
        """Mark subscription as past due (payment failed)."""
        self._status = "past_due"
    
    def get_price_display(self) -> str:
        """Get formatted price for display."""
        dollars = self._price_cents / 100
        return f"${dollars:.2f} {self._currency}"
    
    # NEW Helper Methods for Addons and Discounts
    
    def has_addon(self, addon_code: str) -> bool:
        """Check if addon is active on subscription."""
        return addon_code in self._active_addons
    
    def add_addon(self, addon_code: str, metadata: dict | None = None):
        """Add an addon to subscription."""
        if addon_code not in self._active_addons:
            self._active_addons.append(addon_code)
        
        if metadata:
            self._addon_metadata[addon_code] = metadata
    
    def remove_addon(self, addon_code: str):
        """Remove an addon from subscription."""
        if addon_code in self._active_addons:
            self._active_addons.remove(addon_code)
        
        if addon_code in self._addon_metadata:
            del self._addon_metadata[addon_code]
    
    def get_addon_metadata(self, addon_code: str) -> dict | None:
        """Get metadata for specific addon."""
        return self._addon_metadata.get(addon_code)
    
    def set_addon_metadata(self, addon_code: str, metadata: dict):
        """Set metadata for specific addon."""
        self._addon_metadata[addon_code] = metadata
    
    def has_discount(self) -> bool:
        """Check if subscription has an active discount."""
        return self._discount_id is not None
    
    def apply_discount(self, discount_id: str, discount_code: str, discount_amount_cents: int):
        """Apply a discount to subscription."""
        self._discount_id = discount_id
        self._discount_code = discount_code
        self._discount_amount_cents = discount_amount_cents
    
    def remove_discount(self):
        """Remove discount from subscription."""
        self._discount_id = None
        self._discount_code = None
        self._discount_amount_cents = 0
    
    def get_final_price_cents(self) -> int:
        """Get final price after discount."""
        return max(0, self._price_cents - self._discount_amount_cents)
