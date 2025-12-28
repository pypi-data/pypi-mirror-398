"""
BillingAccount model for payment system.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class BillingAccount(BaseTenantUserModel):
    """
    BillingAccount - Payer/payee configuration with PSP integration.
    
    Represents billing configuration for a tenant or specific entity,
    including payment service provider (PSP) customer references,
    currency settings, and tax configuration.
    
    Multi-Tenancy:
    - tenant_id: Organization/company that owns this billing account
    - account_holder_id: Specific entity (user/org) this account belongs to
    
    Access Patterns (DynamoDB Keys):
    - pk: BILLING_ACCOUNT#{tenant_id}#{account_id}
    - sk: metadata
    - gsi1_pk: tenant#{tenant_id}
    - gsi1_sk: BILLING_ACCOUNT#{created_utc_ts}
    - gsi2_pk: STRIPE_CUSTOMER#{stripe_customer_id}
    - gsi2_sk: metadata
    """

    def __init__(self):
        super().__init__()
        
        # Identity (inherited from BaseModel: id, tenant_id)
        self._account_holder_id: str | None = None  # Entity that owns this account
        self._account_holder_type: str = "user"  # "user", "organization", "property"
        
        # PSP Integration (Stripe)
        self._stripe_customer_id: str | None = None  # Stripe customer reference
        self._stripe_account_id: str | None = None  # Connected account (for payees)
        
        # Currency & Localization
        self._currency_code: str = "USD"  # ISO 4217 currency code
        self._country_code: str | None = None  # ISO 3166-1 alpha-2 country code
        self._locale: str | None = None  # Locale for formatting (e.g., "en_US")
        
        # Tax Configuration
        self._tax_id: str | None = None  # VAT/tax ID number
        self._tax_id_type: str | None = None  # "us_ein", "eu_vat", etc.
        self._tax_exempt: bool = False  # Tax exemption status
        self._tax_metadata: Dict[str, Any] | None = None  # Additional tax info
        
        # Billing Details
        self._billing_email: str | None = None  # Email for invoices/receipts
        self._billing_name: str | None = None  # Name on account
        self._billing_phone: str | None = None  # Contact phone
        
        # Address
        self._address_line1: str | None = None
        self._address_line2: str | None = None
        self._address_city: str | None = None
        self._address_state: str | None = None
        self._address_postal_code: str | None = None
        self._address_country: str | None = None  # ISO 3166-1 alpha-2
        
        # Payment Method Configuration
        self._default_payment_method_id: str | None = None  # Stripe payment method ID
        self._allowed_payment_methods: list[str] = ["card"]  # card, ach_debit, etc.
        
        # Account Settings
        self._auto_charge_enabled: bool = False  # Auto-charge for recurring
        self._require_cvv: bool = True  # Require CVV for payments
        self._send_receipts: bool = True  # Auto-send receipt emails
        
        # Balance & Limits (in cents to avoid float issues)
        self._balance_cents: int = 0  # Current account balance (negative = credit)
        self._credit_limit_cents: int | None = None  # Maximum credit allowed
        
        # Status
        self._status: str = "active"  # "active", "suspended", "closed"
        self._status_reason: str | None = None  # Reason for status change
        
        # Metadata
        self._notes: str | None = None  # Internal notes
        self._external_reference: str | None = None  # External system reference
        
        # Setup indexes
        self._setup_indexes()
        
        # Mark initialization as complete
        object.__setattr__(self, '_initializing', False)
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for billing account queries."""
        
        # Primary index: Billing account by ID
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("billing_account", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Billing accounts by tenant
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("billing_account", self.created_utc_ts))
        self.indexes.add_secondary(gsi)
        
        # GSI2: Billing account by Stripe customer ID (for webhook lookups)
        if self.stripe_customer_id:
            gsi = DynamoDBIndex()
            gsi.name = "gsi2"
            gsi.partition_key.attribute_name = f"{gsi.name}_pk"
            gsi.partition_key.value = lambda: DynamoDBKey.build_key(("stripe_customer", self.stripe_customer_id))
            gsi.sort_key.attribute_name = f"{gsi.name}_sk"
            gsi.sort_key.value = lambda: "metadata"
            self.indexes.add_secondary(gsi)
    
    # Properties - Account Identity
    @property
    def account_id(self) -> str | None:
        """Unique account ID (alias for id)."""
        return self.id
    
    @account_id.setter
    def account_id(self, value: str | None):
        self.id = value
    
    @property
    def account_holder_id(self) -> str | None:
        """Entity that owns this billing account."""
        return self._account_holder_id
    
    @account_holder_id.setter
    def account_holder_id(self, value: str | None):
        self._account_holder_id = value
    
    @property
    def account_holder_type(self) -> str:
        """Type of account holder: 'user', 'organization', 'property'."""
        return self._account_holder_type
    
    @account_holder_type.setter
    def account_holder_type(self, value: str):
        valid_types = ["user", "organization", "property"]
        if value not in valid_types:
            raise ValueError(f"Invalid account_holder_type: {value}. Must be one of {valid_types}")
        self._account_holder_type = value
    
    # Properties - PSP Integration
    @property
    def stripe_customer_id(self) -> str | None:
        """Stripe customer reference ID."""
        return self._stripe_customer_id
    
    @stripe_customer_id.setter
    def stripe_customer_id(self, value: str | None):
        self._stripe_customer_id = value
    
    @property
    def stripe_account_id(self) -> str | None:
        """Stripe connected account ID (for payees)."""
        return self._stripe_account_id
    
    @stripe_account_id.setter
    def stripe_account_id(self, value: str | None):
        self._stripe_account_id = value
    
    # Properties - Currency & Localization
    @property
    def currency_code(self) -> str:
        """ISO 4217 currency code."""
        return self._currency_code
    
    @currency_code.setter
    def currency_code(self, value: str):
        if not value or len(value) != 3:
            raise ValueError("currency_code must be a 3-letter ISO 4217 code")
        self._currency_code = value.upper()
    
    @property
    def country_code(self) -> str | None:
        """ISO 3166-1 alpha-2 country code."""
        return self._country_code
    
    @country_code.setter
    def country_code(self, value: str | None):
        if value and len(value) != 2:
            raise ValueError("country_code must be a 2-letter ISO 3166-1 alpha-2 code")
        self._country_code = value.upper() if value else None
    
    @property
    def locale(self) -> str | None:
        """Locale for formatting (e.g., 'en_US')."""
        return self._locale
    
    @locale.setter
    def locale(self, value: str | None):
        self._locale = value
    
    # Properties - Tax Configuration
    @property
    def tax_id(self) -> str | None:
        """VAT/tax ID number."""
        return self._tax_id
    
    @tax_id.setter
    def tax_id(self, value: str | None):
        self._tax_id = value
    
    @property
    def tax_id_type(self) -> str | None:
        """Type of tax ID: 'us_ein', 'eu_vat', etc."""
        return self._tax_id_type
    
    @tax_id_type.setter
    def tax_id_type(self, value: str | None):
        self._tax_id_type = value
    
    @property
    def tax_exempt(self) -> bool:
        """Tax exemption status."""
        return self._tax_exempt
    
    @tax_exempt.setter
    def tax_exempt(self, value: bool):
        self._tax_exempt = bool(value)
    
    @property
    def tax_metadata(self) -> Dict[str, Any] | None:
        """Additional tax information."""
        return self._tax_metadata
    
    @tax_metadata.setter
    def tax_metadata(self, value: Dict[str, Any] | None):
        self._tax_metadata = value if isinstance(value, dict) else None
    
    # Properties - Billing Details
    @property
    def billing_email(self) -> str | None:
        """Email for invoices and receipts."""
        return self._billing_email
    
    @billing_email.setter
    def billing_email(self, value: str | None):
        self._billing_email = value
    
    @property
    def billing_name(self) -> str | None:
        """Name on billing account."""
        return self._billing_name
    
    @billing_name.setter
    def billing_name(self, value: str | None):
        self._billing_name = value
    
    @property
    def billing_phone(self) -> str | None:
        """Billing contact phone."""
        return self._billing_phone
    
    @billing_phone.setter
    def billing_phone(self, value: str | None):
        self._billing_phone = value
    
    # Properties - Address
    @property
    def address_line1(self) -> str | None:
        """Address line 1."""
        return self._address_line1
    
    @address_line1.setter
    def address_line1(self, value: str | None):
        self._address_line1 = value
    
    @property
    def address_line2(self) -> str | None:
        """Address line 2."""
        return self._address_line2
    
    @address_line2.setter
    def address_line2(self, value: str | None):
        self._address_line2 = value
    
    @property
    def address_city(self) -> str | None:
        """City."""
        return self._address_city
    
    @address_city.setter
    def address_city(self, value: str | None):
        self._address_city = value
    
    @property
    def address_state(self) -> str | None:
        """State/province."""
        return self._address_state
    
    @address_state.setter
    def address_state(self, value: str | None):
        self._address_state = value
    
    @property
    def address_postal_code(self) -> str | None:
        """Postal/ZIP code."""
        return self._address_postal_code
    
    @address_postal_code.setter
    def address_postal_code(self, value: str | None):
        self._address_postal_code = value
    
    @property
    def address_country(self) -> str | None:
        """Country (ISO 3166-1 alpha-2)."""
        return self._address_country
    
    @address_country.setter
    def address_country(self, value: str | None):
        if value and len(value) != 2:
            raise ValueError("address_country must be a 2-letter ISO 3166-1 alpha-2 code")
        self._address_country = value.upper() if value else None
    
    # Properties - Payment Method Configuration
    @property
    def default_payment_method_id(self) -> str | None:
        """Default Stripe payment method ID."""
        return self._default_payment_method_id
    
    @default_payment_method_id.setter
    def default_payment_method_id(self, value: str | None):
        self._default_payment_method_id = value
    
    @property
    def allowed_payment_methods(self) -> list[str]:
        """Allowed payment method types."""
        return self._allowed_payment_methods
    
    @allowed_payment_methods.setter
    def allowed_payment_methods(self, value: list[str] | None):
        self._allowed_payment_methods = value if isinstance(value, list) else ["card"]
    
    # Properties - Account Settings
    @property
    def auto_charge_enabled(self) -> bool:
        """Auto-charge enabled for recurring payments."""
        return self._auto_charge_enabled
    
    @auto_charge_enabled.setter
    def auto_charge_enabled(self, value: bool):
        self._auto_charge_enabled = bool(value)
    
    @property
    def require_cvv(self) -> bool:
        """Require CVV for card payments."""
        return self._require_cvv
    
    @require_cvv.setter
    def require_cvv(self, value: bool):
        self._require_cvv = bool(value)
    
    @property
    def send_receipts(self) -> bool:
        """Auto-send receipt emails."""
        return self._send_receipts
    
    @send_receipts.setter
    def send_receipts(self, value: bool):
        self._send_receipts = bool(value)
    
    # Properties - Balance & Limits
    @property
    def balance_cents(self) -> int:
        """Current account balance in cents (negative = credit)."""
        return self._balance_cents
    
    @balance_cents.setter
    def balance_cents(self, value: int):
        self._balance_cents = value if value is not None else 0
    
    @property
    def credit_limit_cents(self) -> int | None:
        """Maximum credit limit in cents."""
        return self._credit_limit_cents
    
    @credit_limit_cents.setter
    def credit_limit_cents(self, value: int | None):
        self._credit_limit_cents = value
    
    # Properties - Status
    @property
    def status(self) -> str:
        """Account status: 'active', 'suspended', 'closed'."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        valid_statuses = ["active", "suspended", "closed"]
        if value not in valid_statuses:
            raise ValueError(f"Invalid status: {value}. Must be one of {valid_statuses}")
        self._status = value
    
    @property
    def status_reason(self) -> str | None:
        """Reason for status change."""
        return self._status_reason
    
    @status_reason.setter
    def status_reason(self, value: str | None):
        self._status_reason = value
    
    # Properties - Metadata
    @property
    def notes(self) -> str | None:
        """Internal notes."""
        return self._notes
    
    @notes.setter
    def notes(self, value: str | None):
        self._notes = value
    
    @property
    def external_reference(self) -> str | None:
        """External system reference."""
        return self._external_reference
    
    @external_reference.setter
    def external_reference(self, value: str | None):
        self._external_reference = value
    
    # Helper Methods
    def is_active(self) -> bool:
        """Check if account is active."""
        return self._status == "active"
    
    def is_suspended(self) -> bool:
        """Check if account is suspended."""
        return self._status == "suspended"
    
    def is_closed(self) -> bool:
        """Check if account is closed."""
        return self._status == "closed"
    
    def has_credit(self) -> bool:
        """Check if account has credit balance."""
        return self._balance_cents < 0
    
    def has_debit(self) -> bool:
        """Check if account has debit balance."""
        return self._balance_cents > 0
    
    def get_balance_dollars(self) -> float:
        """Get balance in dollars."""
        return self._balance_cents / 100.0
    
    def get_credit_limit_dollars(self) -> float | None:
        """Get credit limit in dollars."""
        return self._credit_limit_cents / 100.0 if self._credit_limit_cents else None
    
    def has_stripe_customer(self) -> bool:
        """Check if Stripe customer ID is set."""
        return self._stripe_customer_id is not None and self._stripe_customer_id != ""
    
    def has_default_payment_method(self) -> bool:
        """Check if default payment method is set."""
        return self._default_payment_method_id is not None and self._default_payment_method_id != ""
    
    def get_full_address(self) -> str | None:
        """Get formatted full address."""
        parts = []
        if self._address_line1:
            parts.append(self._address_line1)
        if self._address_line2:
            parts.append(self._address_line2)
        
        city_state_zip = []
        if self._address_city:
            city_state_zip.append(self._address_city)
        if self._address_state:
            city_state_zip.append(self._address_state)
        if self._address_postal_code:
            city_state_zip.append(self._address_postal_code)
        
        if city_state_zip:
            parts.append(", ".join(city_state_zip))
        
        if self._address_country:
            parts.append(self._address_country)
        
        return "\n".join(parts) if parts else None
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the billing account.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Required fields
        if not self.tenant_id:
            errors.append("tenant_id is required")
        if not self._account_holder_id:
            errors.append("account_holder_id is required")
        if not self._currency_code:
            errors.append("currency_code is required")
        
        # Email validation (basic)
        if self._billing_email and "@" not in self._billing_email:
            errors.append("billing_email must be a valid email address")
        
        # Balance and credit limit validation
        if self._credit_limit_cents is not None and self._credit_limit_cents < 0:
            errors.append("credit_limit_cents must be non-negative")
        
        return (len(errors) == 0, errors)
