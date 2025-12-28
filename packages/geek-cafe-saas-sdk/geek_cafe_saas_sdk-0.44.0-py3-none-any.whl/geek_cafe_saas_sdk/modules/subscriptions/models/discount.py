"""
Discount model for promotional codes and credits.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import datetime as dt
from typing import Dict, Any, Optional, List
from geek_cafe_saas_sdk.core.models.base_model import BaseModel
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class Discount(BaseModel):
    """
    Discount/promo code/credit definition.
    
    Represents discounts that can be applied to subscriptions:
    - Promo codes (SUMMER25)
    - Account credits ($100 credit)
    - Referral bonuses
    - Trial extensions
    
    Key Features:
    - Percentage or fixed amount
    - Duration limits
    - Usage limits
    - Plan restrictions
    - Expiration dates
    
    Examples:
    - 25% off for 3 months (promo code)
    - $100 account credit
    - First month free (trial extension)
    - 20% off annual plans (campaign)
    """
    
    # Discount type constants
    TYPE_PERCENTAGE = "percentage"  # Percentage off
    TYPE_FIXED = "fixed"  # Fixed amount off
    TYPE_CREDIT = "credit"  # Account credit
    TYPE_TRIAL_EXTENSION = "trial_extension"  # Extra trial days
    
    # Duration constants
    DURATION_ONCE = "once"  # Apply once
    DURATION_REPEATING = "repeating"  # Apply for N months
    DURATION_FOREVER = "forever"  # Apply indefinitely
    
    # Status constants
    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_DEPLETED = "depleted"  # All uses consumed
    STATUS_ARCHIVED = "archived"
    
    def __init__(self):
        super().__init__()
        
        # Identification
        self._discount_code: str = ""  # e.g., "SUMMER25", "REFERRAL50"
        self._discount_name: str = ""  # Display name
        self._description: Optional[str] = None
        
        # Type and value
        self._discount_type: str = self.TYPE_PERCENTAGE
        self._amount_off_cents: int = 0  # For fixed type
        self._percent_off: float = 0.0  # For percentage type (e.g., 25.0 for 25%)
        self._trial_extension_days: int = 0  # For trial_extension type
        
        # Currency (for fixed discounts)
        self._currency: str = "USD"
        
        # Duration
        self._duration: str = self.DURATION_ONCE
        self._duration_in_months: Optional[int] = None  # For repeating
        
        # Validity period
        self._valid_from_utc_ts: Optional[float] = None
        self._valid_until_utc_ts: Optional[float] = None
        
        # Usage limits
        self._max_redemptions: Optional[int] = None  # Total uses allowed
        self._redemption_count: int = 0  # Times already used
        self._max_redemptions_per_customer: int = 1  # Uses per customer
        
        # Status
        self._status: str = self.STATUS_ACTIVE
        
        # Restrictions
        self._minimum_amount_cents: Optional[int] = None  # Minimum purchase
        self._applies_to_plan_codes: List[str] = []  # Empty = all plans
        self._applies_to_addon_codes: List[str] = []  # Empty = all addons
        self._applies_to_intervals: List[str] = []  # ["month", "year"]
        
        # First-time only
        self._first_time_transaction: bool = False  # Only for new customers
        
        # Metadata
        self._campaign_name: Optional[str] = None
        self._source: Optional[str] = None  # Where discount came from
        self._notes: Optional[str] = None
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for discount queries."""
        
        # Primary index: Discount by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("discount", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Discounts by status
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("status", self.status))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("created", self.created_utc_ts))
        self.indexes.add_secondary(gsi)
        
        # GSI2: Discounts by discount_code (for code lookup)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: "DISCOUNT"
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("code", self.discount_code))
        self.indexes.add_secondary(gsi)
    
    # Discount Code
    @property
    def discount_code(self) -> str:
        """Unique discount code."""
        return self._discount_code
    
    @discount_code.setter
    def discount_code(self, value: str):
        if not value:
            raise ValueError("discount_code is required")
        self._discount_code = value.upper().strip()
    
    # Discount Name
    @property
    def discount_name(self) -> str:
        """Display name."""
        return self._discount_name
    
    @discount_name.setter
    def discount_name(self, value: str):
        if not value:
            raise ValueError("discount_name is required")
        self._discount_name = value.strip()
    
    # Description
    @property
    def description(self) -> Optional[str]:
        """Detailed description."""
        return self._description
    
    @description.setter
    def description(self, value: Optional[str]):
        self._description = value
    
    # Discount Type
    @property
    def discount_type(self) -> str:
        """Discount type."""
        return self._discount_type
    
    @discount_type.setter
    def discount_type(self, value: str):
        valid_types = [self.TYPE_PERCENTAGE, self.TYPE_FIXED, self.TYPE_CREDIT, self.TYPE_TRIAL_EXTENSION]
        if value not in valid_types:
            raise ValueError(f"Invalid discount_type: {value}. Must be one of {valid_types}")
        self._discount_type = value
    
    # Amount Off Cents
    @property
    def amount_off_cents(self) -> int:
        """Fixed amount off in cents."""
        return self._amount_off_cents
    
    @amount_off_cents.setter
    def amount_off_cents(self, value: int):
        if value < 0:
            raise ValueError("amount_off_cents cannot be negative")
        self._amount_off_cents = value
    
    # Percent Off
    @property
    def percent_off(self) -> float:
        """Percentage off."""
        return self._percent_off
    
    @percent_off.setter
    def percent_off(self, value: float):
        if value < 0 or value > 100:
            raise ValueError("percent_off must be between 0 and 100")
        self._percent_off = value
    
    # Trial Extension Days
    @property
    def trial_extension_days(self) -> int:
        """Trial extension days."""
        return self._trial_extension_days
    
    @trial_extension_days.setter
    def trial_extension_days(self, value: int):
        if value < 0:
            raise ValueError("trial_extension_days cannot be negative")
        self._trial_extension_days = value
    
    # Currency
    @property
    def currency(self) -> str:
        """Currency code."""
        return self._currency
    
    @currency.setter
    def currency(self, value: str):
        self._currency = value.upper() if value else "USD"
    
    # Duration
    @property
    def duration(self) -> str:
        """Duration type."""
        return self._duration
    
    @duration.setter
    def duration(self, value: str):
        valid_durations = [self.DURATION_ONCE, self.DURATION_REPEATING, self.DURATION_FOREVER]
        if value not in valid_durations:
            raise ValueError(f"Invalid duration: {value}. Must be one of {valid_durations}")
        self._duration = value
    
    # Duration In Months
    @property
    def duration_in_months(self) -> Optional[int]:
        """Duration in months (for repeating)."""
        return self._duration_in_months
    
    @duration_in_months.setter
    def duration_in_months(self, value: Optional[int]):
        if value is not None and value < 1:
            raise ValueError("duration_in_months must be at least 1")
        self._duration_in_months = value
    
    # Valid From
    @property
    def valid_from_utc_ts(self) -> Optional[float]:
        """Valid from timestamp."""
        return self._valid_from_utc_ts
    
    @valid_from_utc_ts.setter
    def valid_from_utc_ts(self, value: Optional[float]):
        self._valid_from_utc_ts = value
    
    # Valid Until
    @property
    def valid_until_utc_ts(self) -> Optional[float]:
        """Valid until timestamp."""
        return self._valid_until_utc_ts
    
    @valid_until_utc_ts.setter
    def valid_until_utc_ts(self, value: Optional[float]):
        self._valid_until_utc_ts = value
    
    # Max Redemptions
    @property
    def max_redemptions(self) -> Optional[int]:
        """Maximum total redemptions."""
        return self._max_redemptions
    
    @max_redemptions.setter
    def max_redemptions(self, value: Optional[int]):
        if value is not None and value < 1:
            raise ValueError("max_redemptions must be at least 1")
        self._max_redemptions = value
    
    # Redemption Count
    @property
    def redemption_count(self) -> int:
        """Current redemption count."""
        return self._redemption_count
    
    @redemption_count.setter
    def redemption_count(self, value: int):
        if value < 0:
            raise ValueError("redemption_count cannot be negative")
        self._redemption_count = value
    
    # Max Redemptions Per Customer
    @property
    def max_redemptions_per_customer(self) -> int:
        """Max redemptions per customer."""
        return self._max_redemptions_per_customer
    
    @max_redemptions_per_customer.setter
    def max_redemptions_per_customer(self, value: int):
        if value < 1:
            raise ValueError("max_redemptions_per_customer must be at least 1")
        self._max_redemptions_per_customer = value
    
    # Status
    @property
    def status(self) -> str:
        """Discount status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        valid_statuses = [self.STATUS_ACTIVE, self.STATUS_EXPIRED, self.STATUS_DEPLETED, self.STATUS_ARCHIVED]
        if value not in valid_statuses:
            raise ValueError(f"Invalid status: {value}. Must be one of {valid_statuses}")
        self._status = value
    
    # Minimum Amount Cents
    @property
    def minimum_amount_cents(self) -> Optional[int]:
        """Minimum purchase amount."""
        return self._minimum_amount_cents
    
    @minimum_amount_cents.setter
    def minimum_amount_cents(self, value: Optional[int]):
        if value is not None and value < 0:
            raise ValueError("minimum_amount_cents cannot be negative")
        self._minimum_amount_cents = value
    
    # Applies To Plan Codes
    @property
    def applies_to_plan_codes(self) -> List[str]:
        """Applicable plan codes."""
        return self._applies_to_plan_codes
    
    @applies_to_plan_codes.setter
    def applies_to_plan_codes(self, value: List[str]):
        self._applies_to_plan_codes = value if value else []
    
    # Applies To Addon Codes
    @property
    def applies_to_addon_codes(self) -> List[str]:
        """Applicable addon codes."""
        return self._applies_to_addon_codes
    
    @applies_to_addon_codes.setter
    def applies_to_addon_codes(self, value: List[str]):
        self._applies_to_addon_codes = value if value else []
    
    # Applies To Intervals
    @property
    def applies_to_intervals(self) -> List[str]:
        """Applicable billing intervals."""
        return self._applies_to_intervals
    
    @applies_to_intervals.setter
    def applies_to_intervals(self, value: List[str]):
        self._applies_to_intervals = value if value else []
    
    # First Time Transaction
    @property
    def first_time_transaction(self) -> bool:
        """Whether discount is for first-time customers only."""
        return self._first_time_transaction
    
    @first_time_transaction.setter
    def first_time_transaction(self, value: bool):
        self._first_time_transaction = value
    
    # Helper Methods
    
    def is_active(self) -> bool:
        """Check if discount is active."""
        return self._status == self.STATUS_ACTIVE
    
    def is_valid_now(self) -> bool:
        """Check if discount is currently valid."""
        now = dt.datetime.now(dt.UTC).timestamp()
        
        if self._valid_from_utc_ts and now < self._valid_from_utc_ts:
            return False
        
        if self._valid_until_utc_ts and now > self._valid_until_utc_ts:
            return False
        
        return True
    
    def is_depleted(self) -> bool:
        """Check if all redemptions are used."""
        if self._max_redemptions is None:
            return False
        return self._redemption_count >= self._max_redemptions
    
    def can_be_redeemed(self) -> bool:
        """Check if discount can currently be redeemed."""
        return (self.is_active() and 
                self.is_valid_now() and 
                not self.is_depleted())
    
    def applies_to_plan(self, plan_code: str) -> bool:
        """Check if discount applies to a plan."""
        if not self._applies_to_plan_codes:
            return True  # Empty = applies to all
        return plan_code in self._applies_to_plan_codes
    
    def applies_to_addon(self, addon_code: str) -> bool:
        """Check if discount applies to an addon."""
        if not self._applies_to_addon_codes:
            return True  # Empty = applies to all
        return addon_code in self._applies_to_addon_codes
    
    def applies_to_interval(self, interval: str) -> bool:
        """Check if discount applies to billing interval."""
        if not self._applies_to_intervals:
            return True  # Empty = applies to all
        return interval in self._applies_to_intervals
    
    def calculate_discount(self, price_cents: int) -> int:
        """
        Calculate discount amount for a given price.
        
        Args:
            price_cents: Original price in cents
            
        Returns:
            Discount amount in cents
        """
        if self._discount_type == self.TYPE_PERCENTAGE:
            return int(price_cents * (self._percent_off / 100.0))
        
        elif self._discount_type == self.TYPE_FIXED:
            return min(self._amount_off_cents, price_cents)
        
        elif self._discount_type == self.TYPE_CREDIT:
            return min(self._amount_off_cents, price_cents)
        
        return 0
    
    def increment_redemption_count(self):
        """Increment redemption counter."""
        self._redemption_count += 1
        
        # Auto-update status if depleted
        if self.is_depleted():
            self._status = self.STATUS_DEPLETED
    
    def get_discount_display(self) -> str:
        """Get formatted discount for display."""
        if self._discount_type == self.TYPE_PERCENTAGE:
            return f"{self._percent_off:.0f}% off"
        elif self._discount_type == self.TYPE_FIXED:
            dollars = self._amount_off_cents / 100.0
            return f"${dollars:.2f} off"
        elif self._discount_type == self.TYPE_CREDIT:
            dollars = self._amount_off_cents / 100.0
            return f"${dollars:.2f} credit"
        elif self._discount_type == self.TYPE_TRIAL_EXTENSION:
            return f"{self._trial_extension_days} day trial extension"
        return "Discount"
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate discount data.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not self._discount_code:
            errors.append("discount_code is required")
        
        if not self._discount_name:
            errors.append("discount_name is required")
        
        if self._discount_type == self.TYPE_PERCENTAGE and (self._percent_off <= 0 or self._percent_off > 100):
            errors.append("percent_off must be between 0 and 100")
        
        if self._discount_type in [self.TYPE_FIXED, self.TYPE_CREDIT] and self._amount_off_cents <= 0:
            errors.append("amount_off_cents must be greater than 0")
        
        if self._discount_type == self.TYPE_TRIAL_EXTENSION and self._trial_extension_days <= 0:
            errors.append("trial_extension_days must be greater than 0")
        
        if self._duration == self.DURATION_REPEATING and not self._duration_in_months:
            errors.append("duration_in_months is required for repeating duration")
        
        return (len(errors) == 0, errors)
