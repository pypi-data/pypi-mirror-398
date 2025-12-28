"""
Plan model for subscription tier definitions.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import datetime as dt
from typing import Dict, Any, Optional, List
from geek_cafe_saas_sdk.core.models.base_model import BaseModel
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class Plan(BaseModel):
    """
    Subscription plan/tier definition.
    
    Represents a platform-wide subscription tier (Free, Pro, Enterprise, etc.)
    with pricing, features, and limits. Plans are templates that get applied
    to tenant Subscriptions.
    
    Key Features:
    - Multiple pricing tiers (month/year)
    - Feature flags and limits
    - Trial period configuration
    - Addon compatibility
    - Version tracking for plan changes
    
    Examples:
    - Free Plan: $0, 100 items, basic features
    - Pro Plan: $29/mo, unlimited items, advanced features
    - Enterprise Plan: Custom pricing, white-label, priority support
    """
    
    # Status constants
    STATUS_ACTIVE = "active"
    STATUS_ARCHIVED = "archived"
    STATUS_DRAFT = "draft"
    
    def __init__(self):
        super().__init__()
        
        # Plan identification
        self._plan_code: str = ""  # Unique identifier (e.g., "pro", "enterprise")
        self._plan_name: str = ""  # Display name
        self._description: Optional[str] = None
        self._tagline: Optional[str] = None  # Short marketing copy
        
        # Status and visibility
        self._status: str = self.STATUS_DRAFT
        self._is_public: bool = True  # Show in pricing page
        self._is_featured: bool = False  # Highlight in UI
        self._sort_order: int = 0  # Display ordering
        
        # Pricing - Monthly
        self._price_monthly_cents: int = 0
        self._price_monthly_currency: str = "USD"
        
        # Pricing - Annual (optional)
        self._price_annual_cents: Optional[int] = None
        self._price_annual_currency: str = "USD"
        self._annual_discount_percentage: Optional[float] = None  # e.g., 20.0 for 20% off
        
        # Trial configuration
        self._trial_days: int = 0  # Number of trial days (0 = no trial)
        self._trial_requires_payment_method: bool = True
        
        # Seat/user configuration
        self._min_seats: int = 1
        self._max_seats: Optional[int] = None  # None = unlimited
        self._price_per_additional_seat_cents: int = 0
        
        # Feature flags (boolean features)
        self._features: Dict[str, bool] = {}
        # Example: {"api_access": True, "white_label": False, "sso": True}
        
        # Numeric limits
        self._limits: Dict[str, int] = {}
        # Example: {"max_projects": 10, "max_storage_gb": 100, "max_api_calls_per_day": 1000}
        
        # Addon compatibility
        self._included_addon_ids: List[str] = []  # Addons included in base price
        self._compatible_addon_ids: List[str] = []  # Addons that can be added
        
        # Metadata for display
        self._feature_list: List[str] = []  # Marketing feature list
        self._cta_text: str = "Get Started"  # Call-to-action button text
        self._recommended: bool = False  # "Most Popular" badge
        
        # Version tracking
        self._version: int = 1
        self._previous_version_id: Optional[str] = None
        
        # Grandfathering
        self._allow_downgrades: bool = True
        self._allow_upgrades: bool = True
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for plan queries."""
        
        # Primary index: Plan by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("plan", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Plans by status (for listing active/archived plans)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("status", self.status))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("sort_order", self.sort_order), ("name", self.plan_name))
        self.indexes.add_secondary(gsi)
        
        # GSI2: Plans by plan_code (for lookups by code)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: "PLAN"
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("code", self.plan_code))
        self.indexes.add_secondary(gsi)
    
    # Plan Code
    @property
    def plan_code(self) -> str:
        """Unique plan identifier code."""
        return self._plan_code
    
    @plan_code.setter
    def plan_code(self, value: str):
        if not value:
            raise ValueError("plan_code is required")
        self._plan_code = value.lower().strip()
    
    # Plan Name
    @property
    def plan_name(self) -> str:
        """Display name for plan."""
        return self._plan_name
    
    @plan_name.setter
    def plan_name(self, value: str):
        if not value:
            raise ValueError("plan_name is required")
        self._plan_name = value.strip()
    
    # Description
    @property
    def description(self) -> Optional[str]:
        """Detailed plan description."""
        return self._description
    
    @description.setter
    def description(self, value: Optional[str]):
        self._description = value
    
    # Tagline
    @property
    def tagline(self) -> Optional[str]:
        """Short marketing tagline."""
        return self._tagline
    
    @tagline.setter
    def tagline(self, value: Optional[str]):
        self._tagline = value
    
    # Status
    @property
    def status(self) -> str:
        """Plan status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        valid_statuses = [self.STATUS_ACTIVE, self.STATUS_ARCHIVED, self.STATUS_DRAFT]
        if value not in valid_statuses:
            raise ValueError(f"Invalid status: {value}. Must be one of {valid_statuses}")
        self._status = value
    
    # Is Public
    @property
    def is_public(self) -> bool:
        """Whether plan is shown publicly."""
        return self._is_public
    
    @is_public.setter
    def is_public(self, value: bool):
        self._is_public = value
    
    # Is Featured
    @property
    def is_featured(self) -> bool:
        """Whether plan is featured/highlighted."""
        return self._is_featured
    
    @is_featured.setter
    def is_featured(self, value: bool):
        self._is_featured = value
    
    # Sort Order
    @property
    def sort_order(self) -> int:
        """Display sort order."""
        return self._sort_order
    
    @sort_order.setter
    def sort_order(self, value: int):
        self._sort_order = value
    
    # Price Monthly Cents
    @property
    def price_monthly_cents(self) -> int:
        """Monthly price in cents."""
        return self._price_monthly_cents
    
    @price_monthly_cents.setter
    def price_monthly_cents(self, value: int):
        if value < 0:
            raise ValueError("price_monthly_cents cannot be negative")
        self._price_monthly_cents = value
    
    # Price Monthly Currency
    @property
    def price_monthly_currency(self) -> str:
        """Monthly price currency code."""
        return self._price_monthly_currency
    
    @price_monthly_currency.setter
    def price_monthly_currency(self, value: str):
        self._price_monthly_currency = value.upper() if value else "USD"
    
    # Price Annual Cents
    @property
    def price_annual_cents(self) -> Optional[int]:
        """Annual price in cents."""
        return self._price_annual_cents
    
    @price_annual_cents.setter
    def price_annual_cents(self, value: Optional[int]):
        if value is not None and value < 0:
            raise ValueError("price_annual_cents cannot be negative")
        self._price_annual_cents = value
    
    # Price Annual Currency
    @property
    def price_annual_currency(self) -> str:
        """Annual price currency code."""
        return self._price_annual_currency
    
    @price_annual_currency.setter
    def price_annual_currency(self, value: str):
        self._price_annual_currency = value.upper() if value else "USD"
    
    # Annual Discount Percentage
    @property
    def annual_discount_percentage(self) -> Optional[float]:
        """Annual billing discount percentage."""
        return self._annual_discount_percentage
    
    @annual_discount_percentage.setter
    def annual_discount_percentage(self, value: Optional[float]):
        if value is not None and (value < 0 or value > 100):
            raise ValueError("annual_discount_percentage must be between 0 and 100")
        self._annual_discount_percentage = value
    
    # Trial Days
    @property
    def trial_days(self) -> int:
        """Number of trial days."""
        return self._trial_days
    
    @trial_days.setter
    def trial_days(self, value: int):
        if value < 0:
            raise ValueError("trial_days cannot be negative")
        self._trial_days = value
    
    # Trial Requires Payment Method
    @property
    def trial_requires_payment_method(self) -> bool:
        """Whether trial requires payment method upfront."""
        return self._trial_requires_payment_method
    
    @trial_requires_payment_method.setter
    def trial_requires_payment_method(self, value: bool):
        self._trial_requires_payment_method = value
    
    # Min Seats
    @property
    def min_seats(self) -> int:
        """Minimum number of seats."""
        return self._min_seats
    
    @min_seats.setter
    def min_seats(self, value: int):
        if value < 1:
            raise ValueError("min_seats must be at least 1")
        self._min_seats = value
    
    # Max Seats
    @property
    def max_seats(self) -> Optional[int]:
        """Maximum number of seats (None = unlimited)."""
        return self._max_seats
    
    @max_seats.setter
    def max_seats(self, value: Optional[int]):
        if value is not None and value < 1:
            raise ValueError("max_seats must be at least 1")
        self._max_seats = value
    
    # Price Per Additional Seat Cents
    @property
    def price_per_additional_seat_cents(self) -> int:
        """Price per additional seat in cents."""
        return self._price_per_additional_seat_cents
    
    @price_per_additional_seat_cents.setter
    def price_per_additional_seat_cents(self, value: int):
        if value < 0:
            raise ValueError("price_per_additional_seat_cents cannot be negative")
        self._price_per_additional_seat_cents = value
    
    # Features
    @property
    def features(self) -> Dict[str, bool]:
        """Feature flags dictionary."""
        return self._features
    
    @features.setter
    def features(self, value: Dict[str, bool]):
        self._features = value if value else {}
    
    # Limits
    @property
    def limits(self) -> Dict[str, int]:
        """Numeric limits dictionary."""
        return self._limits
    
    @limits.setter
    def limits(self, value: Dict[str, int]):
        self._limits = value if value else {}
    
    # Included Addon IDs
    @property
    def included_addon_ids(self) -> List[str]:
        """List of included addon IDs."""
        return self._included_addon_ids
    
    @included_addon_ids.setter
    def included_addon_ids(self, value: List[str]):
        self._included_addon_ids = value if value else []
    
    # Compatible Addon IDs
    @property
    def compatible_addon_ids(self) -> List[str]:
        """List of compatible addon IDs."""
        return self._compatible_addon_ids
    
    @compatible_addon_ids.setter
    def compatible_addon_ids(self, value: List[str]):
        self._compatible_addon_ids = value if value else []
    
    # Feature List
    @property
    def feature_list(self) -> List[str]:
        """Marketing feature list."""
        return self._feature_list
    
    @feature_list.setter
    def feature_list(self, value: List[str]):
        self._feature_list = value if value else []
    
    # CTA Text
    @property
    def cta_text(self) -> str:
        """Call-to-action button text."""
        return self._cta_text
    
    @cta_text.setter
    def cta_text(self, value: str):
        self._cta_text = value if value else "Get Started"
    
    # Recommended
    @property
    def recommended(self) -> bool:
        """Whether plan is marked as recommended."""
        return self._recommended
    
    @recommended.setter
    def recommended(self, value: bool):
        self._recommended = value
    
    # Version
    @property
    def version(self) -> int:
        """Plan version number."""
        return self._version
    
    @version.setter
    def version(self, value: int):
        self._version = value
    
    # Previous Version ID
    @property
    def previous_version_id(self) -> Optional[str]:
        """ID of previous plan version."""
        return self._previous_version_id
    
    @previous_version_id.setter
    def previous_version_id(self, value: Optional[str]):
        self._previous_version_id = value
    
    # Allow Downgrades
    @property
    def allow_downgrades(self) -> bool:
        """Whether downgrades from this plan are allowed."""
        return self._allow_downgrades
    
    @allow_downgrades.setter
    def allow_downgrades(self, value: bool):
        self._allow_downgrades = value
    
    # Allow Upgrades
    @property
    def allow_upgrades(self) -> bool:
        """Whether upgrades to this plan are allowed."""
        return self._allow_upgrades
    
    @allow_upgrades.setter
    def allow_upgrades(self, value: bool):
        self._allow_upgrades = value
    
    # Helper Methods
    
    def is_active(self) -> bool:
        """Check if plan is active."""
        return self._status == self.STATUS_ACTIVE
    
    def is_archived(self) -> bool:
        """Check if plan is archived."""
        return self._status == self.STATUS_ARCHIVED
    
    def is_draft(self) -> bool:
        """Check if plan is in draft status."""
        return self._status == self.STATUS_DRAFT
    
    def is_free(self) -> bool:
        """Check if plan is free."""
        return self._price_monthly_cents == 0
    
    def has_trial(self) -> bool:
        """Check if plan has a trial period."""
        return self._trial_days > 0
    
    def has_annual_pricing(self) -> bool:
        """Check if plan has annual pricing option."""
        return self._price_annual_cents is not None
    
    def get_monthly_price_dollars(self) -> float:
        """Get monthly price in dollars."""
        return self._price_monthly_cents / 100.0
    
    def get_annual_price_dollars(self) -> Optional[float]:
        """Get annual price in dollars."""
        if self._price_annual_cents is None:
            return None
        return self._price_annual_cents / 100.0
    
    def calculate_annual_savings_cents(self) -> int:
        """Calculate annual savings vs monthly billing."""
        if not self.has_annual_pricing():
            return 0
        monthly_total = self._price_monthly_cents * 12
        return monthly_total - self._price_annual_cents
    
    def get_annual_savings_percentage(self) -> float:
        """Calculate annual savings percentage."""
        if not self.has_annual_pricing():
            return 0.0
        monthly_total = self._price_monthly_cents * 12
        if monthly_total == 0:
            return 0.0
        savings = self.calculate_annual_savings_cents()
        return (savings / monthly_total) * 100.0
    
    def has_feature(self, feature_key: str) -> bool:
        """Check if plan has a specific feature."""
        return self._features.get(feature_key, False)
    
    def get_limit(self, limit_key: str, default: int = 0) -> int:
        """Get a specific limit value."""
        return self._limits.get(limit_key, default)
    
    def has_unlimited_limit(self, limit_key: str) -> bool:
        """Check if a limit is unlimited (-1 convention)."""
        return self.get_limit(limit_key, 0) == -1
    
    def includes_addon(self, addon_id: str) -> bool:
        """Check if addon is included in plan."""
        return addon_id in self._included_addon_ids
    
    def is_addon_compatible(self, addon_id: str) -> bool:
        """Check if addon can be added to plan."""
        return addon_id in self._compatible_addon_ids or addon_id in self._included_addon_ids
    
    def calculate_price_for_seats(self, seat_count: int, annual: bool = False) -> int:
        """
        Calculate total price for given number of seats.
        
        Args:
            seat_count: Number of seats
            annual: Whether to use annual pricing
            
        Returns:
            Price in cents
        """
        if seat_count < self._min_seats:
            seat_count = self._min_seats
        
        if self._max_seats and seat_count > self._max_seats:
            seat_count = self._max_seats
        
        base_price = self._price_annual_cents if annual and self.has_annual_pricing() else self._price_monthly_cents
        
        if seat_count <= self._min_seats:
            return base_price
        
        additional_seats = seat_count - self._min_seats
        additional_cost = additional_seats * self._price_per_additional_seat_cents
        
        return base_price + additional_cost
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate plan data.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not self._plan_code:
            errors.append("plan_code is required")
        
        if not self._plan_name:
            errors.append("plan_name is required")
        
        if self._price_monthly_cents < 0:
            errors.append("price_monthly_cents cannot be negative")
        
        if self._price_annual_cents is not None and self._price_annual_cents < 0:
            errors.append("price_annual_cents cannot be negative")
        
        if self._min_seats < 1:
            errors.append("min_seats must be at least 1")
        
        if self._max_seats and self._max_seats < self._min_seats:
            errors.append("max_seats must be >= min_seats")
        
        return (len(errors) == 0, errors)
