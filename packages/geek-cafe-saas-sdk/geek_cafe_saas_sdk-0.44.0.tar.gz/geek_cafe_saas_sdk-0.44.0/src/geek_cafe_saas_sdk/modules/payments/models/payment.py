"""
Payment model for payment system.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import datetime as dt
from typing import Optional, Dict, Any, List
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class Payment(BaseTenantUserModel):
    """
    Payment - Settled payment record with gross, fees, and net amounts.
    
    Represents a completed payment transaction with full financial details.
    This is an immutable record created after a payment intent succeeds.
    Contains gross amount, processing fees, and net amount deposited.
    
    Multi-Tenancy:
    - tenant_id: Organization/company receiving the payment
    
    Access Patterns (DynamoDB Keys):
    - pk: PAYMENT#{tenant_id}#{payment_id}
    - sk: metadata
    - gsi1_pk: tenant#{tenant_id}
    - gsi1_sk: PAYMENT#{settled_utc_ts}
    - gsi2_pk: BILLING_ACCOUNT#{billing_account_id}
    - gsi2_sk: PAYMENT#{settled_utc_ts}
    - gsi3_pk: PSP_TRANSACTION#{psp_type}#{psp_transaction_id}
    - gsi3_sk: metadata
    
    Immutability:
    After settlement, core financial fields should not be modified.
    Only status and metadata fields can be updated (e.g., for disputes).
    """

    def __init__(self):
        super().__init__()
        
        # Identity (inherited from BaseModel: id, tenant_id)
        self._billing_account_id: str | None = None  # Associated billing account
        self._payment_intent_ref_id: str | None = None  # Related payment intent
        
        # PSP Information
        self._psp_type: str = "stripe"  # "stripe", "paypal", "square", etc.
        self._psp_transaction_id: str | None = None  # PSP's transaction ID
        self._psp_charge_id: str | None = None  # PSP's charge ID (Stripe specific)
        self._psp_balance_transaction_id: str | None = None  # PSP balance transaction
        
        # Financial Details (in cents to avoid float issues)
        # Gross = Total amount charged
        # Fees = Processing fees charged by PSP
        # Net = Amount deposited (gross - fees)
        self._gross_amount_cents: int = 0  # Total amount charged
        self._fee_amount_cents: int = 0  # Processing fees
        self._net_amount_cents: int = 0  # Net amount (gross - fees)
        self._currency_code: str = "USD"  # ISO 4217 currency code
        
        # Fee Breakdown (optional detailed fee structure)
        self._fee_details: Dict[str, Any] | None = None  # Detailed fee breakdown
        
        # Payment Method Details
        self._payment_method_id: str | None = None  # PSP payment method ID
        self._payment_method_type: str | None = None  # "card", "ach_debit", etc.
        self._payment_method_last4: str | None = None  # Last 4 digits
        self._payment_method_brand: str | None = None  # "visa", "mastercard", etc.
        self._payment_method_funding: str | None = None  # "credit", "debit", "prepaid"
        
        # Settlement Details
        self._settled_utc_ts: float | None = None  # When payment settled
        self._settlement_date: str | None = None  # Expected settlement date (YYYY-MM-DD)
        self._payout_id: str | None = None  # Related payout batch ID
        
        # Status
        self._status: str = "succeeded"  # "succeeded", "refunded", "partially_refunded", "disputed"
        self._is_refunded: bool = False  # Full refund flag
        self._is_partially_refunded: bool = False  # Partial refund flag
        
        # Refund Tracking (in cents)
        self._refunded_amount_cents: int = 0  # Total refunded amount
        self._refund_count: int = 0  # Number of refunds
        self._refund_ids: List[str] = []  # List of refund IDs
        
        # Dispute Tracking
        self._is_disputed: bool = False
        self._dispute_id: str | None = None  # PSP dispute ID
        self._dispute_status: str | None = None  # "warning_needs_response", "won", "lost"
        self._dispute_reason: str | None = None  # "fraudulent", "duplicate", etc.
        
        # Related Records
        self._invoice_id: str | None = None  # Related invoice
        self._subscription_id: str | None = None  # Related subscription
        self._customer_id: str | None = None  # Customer/user ID
        
        # Metadata
        self._description: str | None = None  # Payment description
        self._statement_descriptor: str | None = None  # Appears on card statement
        self._receipt_number: str | None = None  # Receipt number
        self._receipt_email: str | None = None  # Email receipt sent to
        self._receipt_url: str | None = None  # URL to receipt
        
        # Reconciliation
        self._reconciled: bool = False
        self._reconciled_utc_ts: float | None = None
        self._reconciliation_notes: str | None = None
        
        # Additional PSP Data
        self._psp_metadata: Dict[str, Any] | None = None  # Raw PSP data
        self._application_fee_amount_cents: int | None = None  # Platform fee (if any)
        
        # Setup indexes
        self._setup_indexes()
        
        # Mark initialization as complete
        object.__setattr__(self, '_initializing', False)
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for payment queries."""
        
        # Primary index: Payment by ID
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("payment", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Payments by tenant (for listing/reporting)
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("payment", self.settled_utc_ts))
        self.indexes.add_secondary(gsi)
        
        # GSI2: Payments by billing account
        gsi = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("billing_account", self.billing_account_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("payment", self.settled_utc_ts))
        self.indexes.add_secondary(gsi)
        
        # GSI3: Payment by PSP transaction ID (for webhook lookups)
        if self.psp_transaction_id:
            gsi = DynamoDBIndex()
            gsi.name = "gsi3"
            gsi.partition_key.attribute_name = f"{gsi.name}_pk"
            gsi.partition_key.value = lambda: DynamoDBKey.build_key(("psp_transaction", self.psp_type), ("tx", self.psp_transaction_id))
            gsi.sort_key.attribute_name = f"{gsi.name}_sk"
            gsi.sort_key.value = lambda: "metadata"
            self.indexes.add_secondary(gsi)
    
    # Properties - Identity
    @property
    def payment_id(self) -> str | None:
        """Unique payment ID (alias for id)."""
        return self.id
    
    @payment_id.setter
    def payment_id(self, value: str | None):
        self.id = value
    
    @property
    def billing_account_id(self) -> str | None:
        """Associated billing account ID."""
        return self._billing_account_id
    
    @billing_account_id.setter
    def billing_account_id(self, value: str | None):
        self._billing_account_id = value
    
    @property
    def payment_intent_ref_id(self) -> str | None:
        """Related payment intent reference ID."""
        return self._payment_intent_ref_id
    
    @payment_intent_ref_id.setter
    def payment_intent_ref_id(self, value: str | None):
        self._payment_intent_ref_id = value
    
    # Properties - PSP Information
    @property
    def psp_type(self) -> str:
        """Payment service provider type."""
        return self._psp_type
    
    @psp_type.setter
    def psp_type(self, value: str):
        valid_types = ["stripe", "paypal", "square", "braintree"]
        if value not in valid_types:
            raise ValueError(f"Invalid psp_type: {value}. Must be one of {valid_types}")
        self._psp_type = value
    
    @property
    def psp_transaction_id(self) -> str | None:
        """PSP transaction ID."""
        return self._psp_transaction_id
    
    @psp_transaction_id.setter
    def psp_transaction_id(self, value: str | None):
        self._psp_transaction_id = value
    
    @property
    def psp_charge_id(self) -> str | None:
        """PSP charge ID (Stripe specific)."""
        return self._psp_charge_id
    
    @psp_charge_id.setter
    def psp_charge_id(self, value: str | None):
        self._psp_charge_id = value
    
    @property
    def psp_balance_transaction_id(self) -> str | None:
        """PSP balance transaction ID."""
        return self._psp_balance_transaction_id
    
    @psp_balance_transaction_id.setter
    def psp_balance_transaction_id(self, value: str | None):
        self._psp_balance_transaction_id = value
    
    # Properties - Financial Details
    @property
    def gross_amount_cents(self) -> int:
        """Gross amount charged in cents."""
        return self._gross_amount_cents
    
    @gross_amount_cents.setter
    def gross_amount_cents(self, value: int):
        if value < 0:
            raise ValueError("gross_amount_cents must be non-negative")
        self._gross_amount_cents = value
        # Auto-calculate net amount
        self._net_amount_cents = self._gross_amount_cents - self._fee_amount_cents
    
    @property
    def fee_amount_cents(self) -> int:
        """Processing fee in cents."""
        return self._fee_amount_cents
    
    @fee_amount_cents.setter
    def fee_amount_cents(self, value: int):
        if value < 0:
            raise ValueError("fee_amount_cents must be non-negative")
        self._fee_amount_cents = value
        # Auto-calculate net amount
        self._net_amount_cents = self._gross_amount_cents - self._fee_amount_cents
    
    @property
    def net_amount_cents(self) -> int:
        """Net amount deposited in cents (gross - fees)."""
        return self._net_amount_cents
    
    # Net amount is calculated, but allow setter for deserialization
    @net_amount_cents.setter
    def net_amount_cents(self, value: int):
        self._net_amount_cents = value
    
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
    def fee_details(self) -> Dict[str, Any] | None:
        """Detailed fee breakdown."""
        return self._fee_details
    
    @fee_details.setter
    def fee_details(self, value: Dict[str, Any] | None):
        self._fee_details = value if isinstance(value, dict) else None
    
    # Properties - Payment Method
    @property
    def payment_method_id(self) -> str | None:
        """PSP payment method ID."""
        return self._payment_method_id
    
    @payment_method_id.setter
    def payment_method_id(self, value: str | None):
        self._payment_method_id = value
    
    @property
    def payment_method_type(self) -> str | None:
        """Payment method type."""
        return self._payment_method_type
    
    @payment_method_type.setter
    def payment_method_type(self, value: str | None):
        self._payment_method_type = value
    
    @property
    def payment_method_last4(self) -> str | None:
        """Last 4 digits of payment method."""
        return self._payment_method_last4
    
    @payment_method_last4.setter
    def payment_method_last4(self, value: str | None):
        self._payment_method_last4 = value
    
    @property
    def payment_method_brand(self) -> str | None:
        """Payment method brand."""
        return self._payment_method_brand
    
    @payment_method_brand.setter
    def payment_method_brand(self, value: str | None):
        self._payment_method_brand = value
    
    @property
    def payment_method_funding(self) -> str | None:
        """Payment method funding type."""
        return self._payment_method_funding
    
    @payment_method_funding.setter
    def payment_method_funding(self, value: str | None):
        self._payment_method_funding = value
    
    # Properties - Settlement
    @property
    def settled_utc_ts(self) -> float | None:
        """Timestamp when payment settled."""
        return self._settled_utc_ts
    
    @settled_utc_ts.setter
    def settled_utc_ts(self, value: float | None):
        self._settled_utc_ts = value
    
    @property
    def settlement_date(self) -> str | None:
        """Expected settlement date (YYYY-MM-DD)."""
        return self._settlement_date
    
    @settlement_date.setter
    def settlement_date(self, value: str | None):
        self._settlement_date = value
    
    @property
    def payout_id(self) -> str | None:
        """Related payout batch ID."""
        return self._payout_id
    
    @payout_id.setter
    def payout_id(self, value: str | None):
        self._payout_id = value
    
    # Properties - Status
    @property
    def status(self) -> str:
        """Payment status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        valid_statuses = ["succeeded", "refunded", "partially_refunded", "disputed"]
        if value not in valid_statuses:
            raise ValueError(f"Invalid status: {value}. Must be one of {valid_statuses}")
        self._status = value
    
    @property
    def is_refunded(self) -> bool:
        """Full refund flag."""
        return self._is_refunded
    
    @is_refunded.setter
    def is_refunded(self, value: bool):
        self._is_refunded = bool(value)
    
    @property
    def is_partially_refunded(self) -> bool:
        """Partial refund flag."""
        return self._is_partially_refunded
    
    @is_partially_refunded.setter
    def is_partially_refunded(self, value: bool):
        self._is_partially_refunded = bool(value)
    
    # Properties - Refund Tracking
    @property
    def refunded_amount_cents(self) -> int:
        """Total refunded amount in cents."""
        return self._refunded_amount_cents
    
    @refunded_amount_cents.setter
    def refunded_amount_cents(self, value: int):
        if value < 0:
            raise ValueError("refunded_amount_cents must be non-negative")
        self._refunded_amount_cents = value
    
    @property
    def refund_count(self) -> int:
        """Number of refunds."""
        return self._refund_count
    
    @refund_count.setter
    def refund_count(self, value: int):
        self._refund_count = value if value is not None else 0
    
    @property
    def refund_ids(self) -> List[str]:
        """List of refund IDs."""
        return self._refund_ids
    
    @refund_ids.setter
    def refund_ids(self, value: List[str] | None):
        self._refund_ids = value if isinstance(value, list) else []
    
    # Properties - Dispute
    @property
    def is_disputed(self) -> bool:
        """Dispute flag."""
        return self._is_disputed
    
    @is_disputed.setter
    def is_disputed(self, value: bool):
        self._is_disputed = bool(value)
    
    @property
    def dispute_id(self) -> str | None:
        """PSP dispute ID."""
        return self._dispute_id
    
    @dispute_id.setter
    def dispute_id(self, value: str | None):
        self._dispute_id = value
    
    @property
    def dispute_status(self) -> str | None:
        """Dispute status."""
        return self._dispute_status
    
    @dispute_status.setter
    def dispute_status(self, value: str | None):
        self._dispute_status = value
    
    @property
    def dispute_reason(self) -> str | None:
        """Dispute reason."""
        return self._dispute_reason
    
    @dispute_reason.setter
    def dispute_reason(self, value: str | None):
        self._dispute_reason = value
    
    # Properties - Related Records
    @property
    def invoice_id(self) -> str | None:
        """Related invoice ID."""
        return self._invoice_id
    
    @invoice_id.setter
    def invoice_id(self, value: str | None):
        self._invoice_id = value
    
    @property
    def subscription_id(self) -> str | None:
        """Related subscription ID."""
        return self._subscription_id
    
    @subscription_id.setter
    def subscription_id(self, value: str | None):
        self._subscription_id = value
    
    @property
    def customer_id(self) -> str | None:
        """Customer/user ID."""
        return self._customer_id
    
    @customer_id.setter
    def customer_id(self, value: str | None):
        self._customer_id = value
    
    # Properties - Metadata
    @property
    def description(self) -> str | None:
        """Payment description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    @property
    def statement_descriptor(self) -> str | None:
        """Statement descriptor."""
        return self._statement_descriptor
    
    @statement_descriptor.setter
    def statement_descriptor(self, value: str | None):
        self._statement_descriptor = value
    
    @property
    def receipt_number(self) -> str | None:
        """Receipt number."""
        return self._receipt_number
    
    @receipt_number.setter
    def receipt_number(self, value: str | None):
        self._receipt_number = value
    
    @property
    def receipt_email(self) -> str | None:
        """Email receipt sent to."""
        return self._receipt_email
    
    @receipt_email.setter
    def receipt_email(self, value: str | None):
        self._receipt_email = value
    
    @property
    def receipt_url(self) -> str | None:
        """URL to receipt."""
        return self._receipt_url
    
    @receipt_url.setter
    def receipt_url(self, value: str | None):
        self._receipt_url = value
    
    # Properties - Reconciliation
    @property
    def reconciled(self) -> bool:
        """Reconciliation flag."""
        return self._reconciled
    
    @reconciled.setter
    def reconciled(self, value: bool):
        self._reconciled = bool(value)
    
    @property
    def reconciled_utc_ts(self) -> float | None:
        """Timestamp when reconciled."""
        return self._reconciled_utc_ts
    
    @reconciled_utc_ts.setter
    def reconciled_utc_ts(self, value: float | None):
        self._reconciled_utc_ts = value
    
    @property
    def reconciliation_notes(self) -> str | None:
        """Reconciliation notes."""
        return self._reconciliation_notes
    
    @reconciliation_notes.setter
    def reconciliation_notes(self, value: str | None):
        self._reconciliation_notes = value
    
    # Properties - Additional Data
    @property
    def psp_metadata(self) -> Dict[str, Any] | None:
        """Raw PSP metadata."""
        return self._psp_metadata
    
    @psp_metadata.setter
    def psp_metadata(self, value: Dict[str, Any] | None):
        self._psp_metadata = value if isinstance(value, dict) else None
    
    @property
    def application_fee_amount_cents(self) -> int | None:
        """Platform application fee in cents."""
        return self._application_fee_amount_cents
    
    @application_fee_amount_cents.setter
    def application_fee_amount_cents(self, value: int | None):
        self._application_fee_amount_cents = value
    
    # Helper Methods
    def get_gross_amount_dollars(self) -> float:
        """Get gross amount in dollars."""
        return self._gross_amount_cents / 100.0
    
    def get_fee_amount_dollars(self) -> float:
        """Get fee amount in dollars."""
        return self._fee_amount_cents / 100.0
    
    def get_net_amount_dollars(self) -> float:
        """Get net amount in dollars."""
        return self._net_amount_cents / 100.0
    
    def get_refunded_amount_dollars(self) -> float:
        """Get refunded amount in dollars."""
        return self._refunded_amount_cents / 100.0
    
    def get_remaining_amount_cents(self) -> int:
        """Get remaining amount after refunds (in cents)."""
        return self._gross_amount_cents - self._refunded_amount_cents
    
    def get_remaining_amount_dollars(self) -> float:
        """Get remaining amount after refunds (in dollars)."""
        return self.get_remaining_amount_cents() / 100.0
    
    def is_fully_refunded(self) -> bool:
        """Check if payment is fully refunded."""
        return self._is_refunded or self._refunded_amount_cents >= self._gross_amount_cents
    
    def has_refunds(self) -> bool:
        """Check if payment has any refunds."""
        return self._refund_count > 0 or self._refunded_amount_cents > 0
    
    def add_refund(self, refund_id: str, refund_amount_cents: int):
        """Record a refund."""
        self._refund_ids.append(refund_id)
        self._refund_count += 1
        self._refunded_amount_cents += refund_amount_cents
        
        # Update status
        if self._refunded_amount_cents >= self._gross_amount_cents:
            self._status = "refunded"
            self._is_refunded = True
        else:
            self._status = "partially_refunded"
            self._is_partially_refunded = True
    
    def mark_as_disputed(self, dispute_id: str, dispute_reason: str | None = None):
        """Mark payment as disputed."""
        self._is_disputed = True
        self._dispute_id = dispute_id
        self._dispute_reason = dispute_reason
        self._status = "disputed"
    
    def mark_as_reconciled(self, notes: str | None = None):
        """Mark payment as reconciled."""
        self._reconciled = True
        self._reconciled_utc_ts = dt.datetime.now(dt.UTC).timestamp()
        self._reconciliation_notes = notes
    
    def calculate_fee_percentage(self) -> float:
        """Calculate fee as percentage of gross amount."""
        if self._gross_amount_cents == 0:
            return 0.0
        return (self._fee_amount_cents / self._gross_amount_cents) * 100.0
