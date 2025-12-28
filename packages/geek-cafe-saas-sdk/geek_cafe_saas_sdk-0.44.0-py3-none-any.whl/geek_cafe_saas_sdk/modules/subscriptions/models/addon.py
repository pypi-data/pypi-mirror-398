"""
Addon model for subscription add-on modules.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import datetime as dt
from typing import Dict, Any, Optional, List
from geek_cafe_saas_sdk.core.models.base_model import BaseModel
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class Addon(BaseModel):
    """
    Subscription addon/module definition.
    
    Represents a billable feature or module that can be added to subscriptions
    (e.g., Chat Module, Voting Module, Extra Storage, etc.)
    
    Key Features:
    - Fixed or per-unit pricing
    - Feature flags and limits
    - Plan compatibility
    - Usage tracking support
    - Trial periods
    
    Pricing Models:
    - Fixed: Flat monthly fee (e.g., $10/month for chat)
    - Per Unit: Price per unit (e.g., $0.01 per GB storage)
    - Tiered: Different rates based on usage tiers
    
    Examples:
    - Chat Module: $15/mo fixed
    - Extra Storage: $0.10 per GB/month
    - Priority Support: $50/mo fixed
    - API Calls: $0.001 per call (metered)
    """
    
    # Status constants
    STATUS_ACTIVE = "active"
    STATUS_ARCHIVED = "archived"
    STATUS_DRAFT = "draft"
    
    # Pricing model constants
    PRICING_FIXED = "fixed"  # Flat monthly fee
    PRICING_PER_UNIT = "per_unit"  # Price per unit (metered)
    PRICING_TIERED = "tiered"  # Different rates by tier
    
    def __init__(self):
        super().__init__()
        
        # Addon identification
        self._addon_code: str = ""  # Unique identifier (e.g., "chat", "extra_storage")
        self._addon_name: str = ""  # Display name
        self._description: Optional[str] = None
        self._category: Optional[str] = None  # e.g., "communication", "storage", "features"
        
        # Status and visibility
        self._status: str = self.STATUS_DRAFT
        self._is_public: bool = True
        self._sort_order: Optional[int] = None
        
        # Pricing model
        self._pricing_model: str = self.PRICING_FIXED
        
        # Fixed pricing
        self._price_monthly_cents: int = 0
        self._price_annual_cents: Optional[int] = None
        self._currency: str = "USD"
        
        # Per-unit pricing
        self._price_per_unit_cents: int = 0  # For per_unit model
        self._unit_name: Optional[str] = None  # e.g., "GB", "seat", "call"
        self._included_units: int = 0  # Free units included
        self._min_units: int = 0  # Minimum billable units
        self._max_units: Optional[int] = None  # Maximum allowed units
        
        # Tiered pricing
        self._pricing_tiers: List[Dict[str, Any]] = []
        # Example: [{"from": 0, "to": 100, "price_cents": 1000}, ...]
        
        # Trial configuration
        self._trial_days: int = 0
        
        # Feature flags
        self._features: Dict[str, bool] = {}
        
        # Limits
        self._limits: Dict[str, int] = {}
        
        # Plan compatibility
        self._compatible_plan_codes: List[str] = []  # Empty = all plans
        self._incompatible_addon_codes: List[str] = []  # Mutually exclusive addons
        
        # Metadata
        self._feature_list: List[str] = []
        self._icon: Optional[str] = None  # Icon name/URL
        self._color: Optional[str] = None  # Brand color
        
        # Metering
        self._is_metered: bool = False  # Requires usage tracking
        self._meter_event_name: Optional[str] = None  # Event to track
        self._billing_scheme: str = "per_month"  # per_month, per_year, per_use
        
        # Version tracking
        self._version: int = 1
        self._previous_version_id: Optional[str] = None
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for addon queries."""
        
        # Primary index: Addon by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("addon", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Addons by status and category
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("status", self.status))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("category", self.category), ("sort", self.sort_order))
        self.indexes.add_secondary(gsi)
        
        # GSI2: Addons by addon_code
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: "ADDON"
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("code", self.addon_code))
        self.indexes.add_secondary(gsi)
    
    # Addon Code
    @property
    def addon_code(self) -> str:
        """Unique addon identifier code."""
        return self._addon_code
    
    @addon_code.setter
    def addon_code(self, value: str):
        if not value:
            raise ValueError("addon_code is required")
        self._addon_code = value.lower().strip()
    
    # Addon Name
    @property
    def addon_name(self) -> str:
        """Display name for addon."""
        return self._addon_name
    
    @addon_name.setter
    def addon_name(self, value: str):
        if not value:
            raise ValueError("addon_name is required")
        self._addon_name = value.strip()
    
    # Description
    @property
    def description(self) -> Optional[str]:
        """Detailed addon description."""
        return self._description
    
    @description.setter
    def description(self, value: Optional[str]):
        self._description = value
    
    # Category
    @property
    def category(self) -> Optional[str]:
        """Addon category."""
        return self._category
    
    @category.setter
    def category(self, value: Optional[str]):
        self._category = value
    
    # Status
    @property
    def status(self) -> str:
        """Addon status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        valid_statuses = [self.STATUS_ACTIVE, self.STATUS_ARCHIVED, self.STATUS_DRAFT]
        if value not in valid_statuses:
            raise ValueError(f"Invalid status: {value}. Must be one of {valid_statuses}")
        self._status = value
    
    # Sort Order
    @property
    def sort_order(self) -> int:
        """Sort order for display."""
        return self._sort_order
    
    @sort_order.setter
    def sort_order(self, value: int):
        self._sort_order = value
    
    # Is Public
    @property
    def is_public(self) -> bool:
        """Whether addon is publicly available."""
        return self._is_public
    
    @is_public.setter
    def is_public(self, value: bool):
        self._is_public = value
    
    # Pricing Model
    @property
    def pricing_model(self) -> str:
        """Pricing model type."""
        return self._pricing_model
    
    @pricing_model.setter
    def pricing_model(self, value: str):
        valid_models = [self.PRICING_FIXED, self.PRICING_PER_UNIT, self.PRICING_TIERED]
        if value not in valid_models:
            raise ValueError(f"Invalid pricing_model: {value}. Must be one of {valid_models}")
        self._pricing_model = value
    
    # Price Monthly Cents
    @property
    def price_monthly_cents(self) -> int:
        """Monthly price in cents (fixed model)."""
        return self._price_monthly_cents
    
    @price_monthly_cents.setter
    def price_monthly_cents(self, value: int):
        if value < 0:
            raise ValueError("price_monthly_cents cannot be negative")
        self._price_monthly_cents = value
    
    # Price Annual Cents
    @property
    def price_annual_cents(self) -> Optional[int]:
        """Annual price in cents (fixed model)."""
        return self._price_annual_cents
    
    @price_annual_cents.setter
    def price_annual_cents(self, value: Optional[int]):
        if value is not None and value < 0:
            raise ValueError("price_annual_cents cannot be negative")
        self._price_annual_cents = value
    
    # Currency
    @property
    def currency(self) -> str:
        """Currency code."""
        return self._currency
    
    @currency.setter
    def currency(self, value: str):
        self._currency = value.upper() if value else "USD"
    
    # Price Per Unit Cents
    @property
    def price_per_unit_cents(self) -> int:
        """Price per unit in cents (per_unit model)."""
        return self._price_per_unit_cents
    
    @price_per_unit_cents.setter
    def price_per_unit_cents(self, value: int):
        if value < 0:
            raise ValueError("price_per_unit_cents cannot be negative")
        self._price_per_unit_cents = value
    
    # Unit Name
    @property
    def unit_name(self) -> Optional[str]:
        """Unit name for per_unit pricing."""
        return self._unit_name
    
    @unit_name.setter
    def unit_name(self, value: Optional[str]):
        self._unit_name = value
    
    # Included Units
    @property
    def included_units(self) -> int:
        """Free units included."""
        return self._included_units
    
    @included_units.setter
    def included_units(self, value: int):
        if value < 0:
            raise ValueError("included_units cannot be negative")
        self._included_units = value
    
    # Min Units
    @property
    def min_units(self) -> int:
        """Minimum billable units."""
        return self._min_units
    
    @min_units.setter
    def min_units(self, value: int):
        if value < 0:
            raise ValueError("min_units cannot be negative")
        self._min_units = value
    
    # Max Units
    @property
    def max_units(self) -> Optional[int]:
        """Maximum allowed units."""
        return self._max_units
    
    @max_units.setter
    def max_units(self, value: Optional[int]):
        if value is not None and value < 0:
            raise ValueError("max_units cannot be negative")
        self._max_units = value
    
    # Pricing Tiers
    @property
    def pricing_tiers(self) -> List[Dict[str, Any]]:
        """Tiered pricing configuration."""
        return self._pricing_tiers
    
    @pricing_tiers.setter
    def pricing_tiers(self, value: List[Dict[str, Any]]):
        self._pricing_tiers = value if value else []
    
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
    
    # Compatible Plan Codes
    @property
    def compatible_plan_codes(self) -> List[str]:
        """List of compatible plan codes."""
        return self._compatible_plan_codes
    
    @compatible_plan_codes.setter
    def compatible_plan_codes(self, value: List[str]):
        self._compatible_plan_codes = value if value else []
    
    # Incompatible Addon Codes
    @property
    def incompatible_addon_codes(self) -> List[str]:
        """List of mutually exclusive addon codes."""
        return self._incompatible_addon_codes
    
    @incompatible_addon_codes.setter
    def incompatible_addon_codes(self, value: List[str]):
        self._incompatible_addon_codes = value if value else []
    
    # Feature List
    @property
    def feature_list(self) -> List[str]:
        """Marketing feature list."""
        return self._feature_list
    
    @feature_list.setter
    def feature_list(self, value: List[str]):
        self._feature_list = value if value else []
    
    # Is Metered
    @property
    def is_metered(self) -> bool:
        """Whether addon requires usage metering."""
        return self._is_metered
    
    @is_metered.setter
    def is_metered(self, value: bool):
        self._is_metered = value
    
    # Meter Event Name
    @property
    def meter_event_name(self) -> Optional[str]:
        """Event name for metering."""
        return self._meter_event_name
    
    @meter_event_name.setter
    def meter_event_name(self, value: Optional[str]):
        self._meter_event_name = value
    
    # Billing Scheme
    @property
    def billing_scheme(self) -> str:
        """Billing scheme."""
        return self._billing_scheme
    
    @billing_scheme.setter
    def billing_scheme(self, value: str):
        self._billing_scheme = value
    
    @property
    def sort_order(self) -> int:
        """Sort order for display."""
        return self._sort_order
    
    @sort_order.setter
    def sort_order(self, value: int):
        self._sort_order = value    

    # Helper Methods
    
    def is_active(self) -> bool:
        """Check if addon is active."""
        return self._status == self.STATUS_ACTIVE
    
    def is_fixed_pricing(self) -> bool:
        """Check if addon uses fixed pricing."""
        return self._pricing_model == self.PRICING_FIXED
    
    def is_per_unit_pricing(self) -> bool:
        """Check if addon uses per-unit pricing."""
        return self._pricing_model == self.PRICING_PER_UNIT
    
    def is_tiered_pricing(self) -> bool:
        """Check if addon uses tiered pricing."""
        return self._pricing_model == self.PRICING_TIERED
    
    def has_trial(self) -> bool:
        """Check if addon has a trial period."""
        return self._trial_days > 0
    
    def is_compatible_with_plan(self, plan_code: str) -> bool:
        """Check if addon is compatible with a plan."""
        if not self._compatible_plan_codes:
            return True  # Empty list = compatible with all
        return plan_code in self._compatible_plan_codes
    
    def is_compatible_with_addon(self, addon_code: str) -> bool:
        """Check if addon is compatible with another addon."""
        return addon_code not in self._incompatible_addon_codes
    
    def get_monthly_price_dollars(self) -> float:
        """Get monthly price in dollars (fixed model)."""
        return self._price_monthly_cents / 100.0
    
    def get_price_per_unit_dollars(self) -> float:
        """Get per-unit price in dollars."""
        return self._price_per_unit_cents / 100.0
    
    def calculate_fixed_price(self, annual: bool = False) -> int:
        """
        Calculate fixed price.
        
        Args:
            annual: Whether to use annual pricing
            
        Returns:
            Price in cents
        """
        if self._pricing_model != self.PRICING_FIXED:
            return 0
        
        if annual and self._price_annual_cents is not None:
            return self._price_annual_cents
        
        return self._price_monthly_cents
    
    def calculate_per_unit_price(self, units: int) -> int:
        """
        Calculate price for per-unit model.
        
        Args:
            units: Number of units to calculate
            
        Returns:
            Price in cents
        """
        if self._pricing_model != self.PRICING_PER_UNIT:
            return 0
        
        # Apply included units
        billable_units = max(0, units - self._included_units)
        
        # Apply min units
        billable_units = max(billable_units, self._min_units)
        
        # Apply max units
        if self._max_units is not None:
            billable_units = min(billable_units, self._max_units)
        
        return billable_units * self._price_per_unit_cents
    
    def calculate_tiered_price(self, units: int) -> int:
        """
        Calculate price using tiered pricing.
        
        Args:
            units: Number of units to calculate
            
        Returns:
            Price in cents
        """
        if self._pricing_model != self.PRICING_TIERED or not self._pricing_tiers:
            return 0
        
        total_price = 0
        remaining_units = units
        
        # Sort tiers by 'from' value
        sorted_tiers = sorted(self._pricing_tiers, key=lambda t: t.get('from', 0))
        
        for tier in sorted_tiers:
            tier_from = tier.get('from', 0)
            tier_to = tier.get('to', float('inf'))
            tier_price = tier.get('price_cents', 0)
            
            if remaining_units <= 0:
                break
            
            # Calculate units in this tier
            tier_units = min(remaining_units, tier_to - tier_from + 1)
            
            total_price += tier_units * tier_price
            remaining_units -= tier_units
        
        return total_price
    
    def calculate_price(self, units: int = 1, annual: bool = False) -> int:
        """
        Calculate price based on pricing model.
        
        Args:
            units: Number of units (for per_unit/tiered)
            annual: Whether to use annual pricing (for fixed)
            
        Returns:
            Price in cents
        """
        if self._pricing_model == self.PRICING_FIXED:
            return self.calculate_fixed_price(annual)
        elif self._pricing_model == self.PRICING_PER_UNIT:
            return self.calculate_per_unit_price(units)
        elif self._pricing_model == self.PRICING_TIERED:
            return self.calculate_tiered_price(units)
        
        return 0
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate addon data.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not self._addon_code:
            errors.append("addon_code is required")
        
        if not self._addon_name:
            errors.append("addon_name is required")
        
        if self._pricing_model == self.PRICING_FIXED and self._price_monthly_cents < 0:
            errors.append("price_monthly_cents cannot be negative")
        
        if self._pricing_model == self.PRICING_PER_UNIT:
            if self._price_per_unit_cents < 0:
                errors.append("price_per_unit_cents cannot be negative")
            if not self._unit_name:
                errors.append("unit_name is required for per_unit pricing")
        
        if self._pricing_model == self.PRICING_TIERED and not self._pricing_tiers:
            errors.append("pricing_tiers is required for tiered pricing")
        
        if self._is_metered and not self._meter_event_name:
            errors.append("meter_event_name is required for metered addons")
        
        return (len(errors) == 0, errors)
