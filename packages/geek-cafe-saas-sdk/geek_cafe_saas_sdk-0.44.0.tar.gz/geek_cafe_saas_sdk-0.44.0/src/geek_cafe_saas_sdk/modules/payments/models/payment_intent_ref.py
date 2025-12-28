"""
PaymentIntentRef model for payment system.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import datetime as dt
from typing import Optional, Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class PaymentIntentRef(BaseTenantUserModel):
    """
    PaymentIntentRef - PSP payment intent reference and status tracking.
    
    Represents a payment intent created with a payment service provider (PSP)
    like Stripe. Tracks the intent lifecycle from creation through completion
    or cancellation. Used to handle async payment flows and webhooks.
    
    Multi-Tenancy:
    - tenant_id: Organization/company initiating the payment
    
    Access Patterns (DynamoDB Keys):
    - pk: PAYMENT_INTENT#{tenant_id}#{intent_ref_id}
    - sk: metadata
    - gsi1_pk: tenant#{tenant_id}
    - gsi1_sk: PAYMENT_INTENT#{created_utc_ts}
    - gsi2_pk: PSP_INTENT#{psp_type}#{psp_intent_id}
    - gsi2_sk: metadata
    - gsi3_pk: BILLING_ACCOUNT#{billing_account_id}
    - gsi3_sk: PAYMENT_INTENT#{created_utc_ts}
    """

    def __init__(self):
        super().__init__()
        
        # Identity (inherited from BaseModel: id, tenant_id)
        self._billing_account_id: str | None = None  # Associated billing account
        
        # PSP Information
        self._psp_type: str = "stripe"  # "stripe", "paypal", "square", etc.
        self._psp_intent_id: str | None = None  # PSP's intent identifier
        self._psp_client_secret: str | None = None  # Client secret for frontend
        
        # Amount (in cents to avoid float issues)
        self._amount_cents: int = 0  # Total amount
        self._currency_code: str = "USD"  # ISO 4217 currency code
        
        # Payment Method
        self._payment_method_id: str | None = None  # PSP payment method ID
        self._payment_method_type: str | None = None  # "card", "ach_debit", etc.
        self._payment_method_last4: str | None = None  # Last 4 digits
        self._payment_method_brand: str | None = None  # "visa", "mastercard", etc.
        
        # Status Tracking
        self._status: str = "created"  # Status of the payment intent
        self._status_history: list[Dict[str, Any]] = []  # Status change log
        self._last_status_change_utc_ts: float | None = None
        
        # Processing Details
        self._setup_future_usage: str | None = None  # "on_session", "off_session"
        self._capture_method: str = "automatic"  # "automatic", "manual"
        self._confirmation_method: str = "automatic"  # "automatic", "manual"
        
        # Metadata
        self._description: str | None = None  # Payment description
        self._statement_descriptor: str | None = None  # Appears on card statement
        self._receipt_email: str | None = None  # Email for receipt
        
        # Error Tracking
        self._error_code: str | None = None  # PSP error code
        self._error_message: str | None = None  # Human-readable error
        self._error_type: str | None = None  # "card_error", "invalid_request", etc.
        
        # Webhooks & Events
        self._last_webhook_utc_ts: float | None = None  # Last webhook received
        self._webhook_count: int = 0  # Number of webhooks received
        
        # Related Records
        self._payment_id: str | None = None  # Settled Payment record (if succeeded)
        self._invoice_id: str | None = None  # Related invoice
        self._subscription_id: str | None = None  # Related subscription
        
        # Cancellation
        self._canceled_utc_ts: float | None = None
        self._cancellation_reason: str | None = None  # "duplicate", "fraudulent", etc.
        
        # Additional PSP Data
        self._psp_metadata: Dict[str, Any] | None = None  # Raw PSP data
        
        # Setup indexes
        self._setup_indexes()
        
        # Mark initialization as complete
        object.__setattr__(self, '_initializing', False)
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for payment intent queries."""
        
        # Primary index: Payment intent by ID
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("payment_intent", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Payment intents by tenant
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("payment_intent", self.created_utc_ts))
        self.indexes.add_secondary(gsi)
        
        # GSI2: Payment intent by PSP intent ID (for webhook lookups)
        if self.psp_intent_id:
            gsi = DynamoDBIndex()
            gsi.name = "gsi2"
            gsi.partition_key.attribute_name = f"{gsi.name}_pk"
            gsi.partition_key.value = lambda: DynamoDBKey.build_key(("psp_intent", self.psp_type), ("intent", self.psp_intent_id))
            gsi.sort_key.attribute_name = f"{gsi.name}_sk"
            gsi.sort_key.value = lambda: "metadata"
            self.indexes.add_secondary(gsi)
    
    # Status Constants
    STATUS_CREATED = "created"
    STATUS_PROCESSING = "processing"
    STATUS_REQUIRES_ACTION = "requires_action"  # e.g., 3D Secure
    STATUS_REQUIRES_CONFIRMATION = "requires_confirmation"
    STATUS_REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_CANCELED = "canceled"
    STATUS_FAILED = "failed"
    
    # Properties - Identity
    @property
    def intent_ref_id(self) -> str | None:
        """Unique intent reference ID (alias for id)."""
        return self.id
    
    @intent_ref_id.setter
    def intent_ref_id(self, value: str | None):
        self.id = value
    
    @property
    def billing_account_id(self) -> str | None:
        """Associated billing account ID."""
        return self._billing_account_id
    
    @billing_account_id.setter
    def billing_account_id(self, value: str | None):
        self._billing_account_id = value
    
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
    def psp_intent_id(self) -> str | None:
        """PSP's payment intent identifier."""
        return self._psp_intent_id
    
    @psp_intent_id.setter
    def psp_intent_id(self, value: str | None):
        self._psp_intent_id = value
    
    @property
    def psp_client_secret(self) -> str | None:
        """Client secret for frontend confirmation."""
        return self._psp_client_secret
    
    @psp_client_secret.setter
    def psp_client_secret(self, value: str | None):
        self._psp_client_secret = value
    
    # Properties - Amount
    @property
    def amount_cents(self) -> int:
        """Payment amount in cents."""
        return self._amount_cents
    
    @amount_cents.setter
    def amount_cents(self, value: int):
        if value < 0:
            raise ValueError("amount_cents must be non-negative")
        self._amount_cents = value
    
    @property
    def currency_code(self) -> str:
        """ISO 4217 currency code."""
        return self._currency_code
    
    @currency_code.setter
    def currency_code(self, value: str):
        if not value or len(value) != 3:
            raise ValueError("currency_code must be a 3-letter ISO 4217 code")
        self._currency_code = value.upper()
    
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
        """Payment method type (e.g., 'card', 'ach_debit')."""
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
        """Payment method brand (e.g., 'visa', 'mastercard')."""
        return self._payment_method_brand
    
    @payment_method_brand.setter
    def payment_method_brand(self, value: str | None):
        self._payment_method_brand = value
    
    # Properties - Status
    @property
    def status(self) -> str:
        """Current payment intent status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        valid_statuses = [
            self.STATUS_CREATED,
            self.STATUS_PROCESSING,
            self.STATUS_REQUIRES_ACTION,
            self.STATUS_REQUIRES_CONFIRMATION,
            self.STATUS_REQUIRES_PAYMENT_METHOD,
            self.STATUS_SUCCEEDED,
            self.STATUS_CANCELED,
            self.STATUS_FAILED,
        ]
        if value not in valid_statuses:
            raise ValueError(f"Invalid status: {value}. Must be one of {valid_statuses}")
        
        # Record status change in history
        if value != self._status:
            self._status_history.append({
                "from_status": self._status,
                "to_status": value,
                "timestamp": dt.datetime.now(dt.UTC).timestamp(),
            })
            self._last_status_change_utc_ts = dt.datetime.now(dt.UTC).timestamp()
        
        self._status = value
    
    @property
    def status_history(self) -> list[Dict[str, Any]]:
        """Status change history."""
        return self._status_history
    
    @status_history.setter
    def status_history(self, value: list[Dict[str, Any]] | None):
        self._status_history = value if isinstance(value, list) else []
    
    @property
    def last_status_change_utc_ts(self) -> float | None:
        """Timestamp of last status change."""
        return self._last_status_change_utc_ts
    
    @last_status_change_utc_ts.setter
    def last_status_change_utc_ts(self, value: float | None):
        self._last_status_change_utc_ts = value
    
    # Properties - Processing Details
    @property
    def setup_future_usage(self) -> str | None:
        """Setup for future usage: 'on_session', 'off_session'."""
        return self._setup_future_usage
    
    @setup_future_usage.setter
    def setup_future_usage(self, value: str | None):
        if value and value not in ["on_session", "off_session"]:
            raise ValueError("setup_future_usage must be 'on_session' or 'off_session'")
        self._setup_future_usage = value
    
    @property
    def capture_method(self) -> str:
        """Capture method: 'automatic', 'manual'."""
        return self._capture_method
    
    @capture_method.setter
    def capture_method(self, value: str):
        if value not in ["automatic", "manual"]:
            raise ValueError("capture_method must be 'automatic' or 'manual'")
        self._capture_method = value
    
    @property
    def confirmation_method(self) -> str:
        """Confirmation method: 'automatic', 'manual'."""
        return self._confirmation_method
    
    @confirmation_method.setter
    def confirmation_method(self, value: str):
        if value not in ["automatic", "manual"]:
            raise ValueError("confirmation_method must be 'automatic' or 'manual'")
        self._confirmation_method = value
    
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
        """Statement descriptor (appears on card statement)."""
        return self._statement_descriptor
    
    @statement_descriptor.setter
    def statement_descriptor(self, value: str | None):
        self._statement_descriptor = value
    
    @property
    def receipt_email(self) -> str | None:
        """Email for receipt."""
        return self._receipt_email
    
    @receipt_email.setter
    def receipt_email(self, value: str | None):
        self._receipt_email = value
    
    # Properties - Error Tracking
    @property
    def error_code(self) -> str | None:
        """PSP error code."""
        return self._error_code
    
    @error_code.setter
    def error_code(self, value: str | None):
        self._error_code = value
    
    @property
    def error_message(self) -> str | None:
        """Human-readable error message."""
        return self._error_message
    
    @error_message.setter
    def error_message(self, value: str | None):
        self._error_message = value
    
    @property
    def error_type(self) -> str | None:
        """Error type (e.g., 'card_error', 'invalid_request')."""
        return self._error_type
    
    @error_type.setter
    def error_type(self, value: str | None):
        self._error_type = value
    
    # Properties - Webhooks
    @property
    def last_webhook_utc_ts(self) -> float | None:
        """Timestamp of last webhook received."""
        return self._last_webhook_utc_ts
    
    @last_webhook_utc_ts.setter
    def last_webhook_utc_ts(self, value: float | None):
        self._last_webhook_utc_ts = value
    
    @property
    def webhook_count(self) -> int:
        """Number of webhooks received."""
        return self._webhook_count
    
    @webhook_count.setter
    def webhook_count(self, value: int):
        self._webhook_count = value if value is not None else 0
    
    # Properties - Related Records
    @property
    def payment_id(self) -> str | None:
        """ID of settled Payment record (if succeeded)."""
        return self._payment_id
    
    @payment_id.setter
    def payment_id(self, value: str | None):
        self._payment_id = value
    
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
    
    # Properties - Cancellation
    @property
    def canceled_utc_ts(self) -> float | None:
        """Timestamp when canceled."""
        return self._canceled_utc_ts
    
    @canceled_utc_ts.setter
    def canceled_utc_ts(self, value: float | None):
        self._canceled_utc_ts = value
    
    @property
    def cancellation_reason(self) -> str | None:
        """Reason for cancellation."""
        return self._cancellation_reason
    
    @cancellation_reason.setter
    def cancellation_reason(self, value: str | None):
        self._cancellation_reason = value
    
    # Properties - PSP Data
    @property
    def psp_metadata(self) -> Dict[str, Any] | None:
        """Raw PSP metadata."""
        return self._psp_metadata
    
    @psp_metadata.setter
    def psp_metadata(self, value: Dict[str, Any] | None):
        self._psp_metadata = value if isinstance(value, dict) else None
    
    # Helper Methods
    def is_succeeded(self) -> bool:
        """Check if payment succeeded."""
        return self._status == self.STATUS_SUCCEEDED
    
    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self._status == self.STATUS_FAILED
    
    def is_canceled(self) -> bool:
        """Check if payment was canceled."""
        return self._status == self.STATUS_CANCELED
    
    def is_processing(self) -> bool:
        """Check if payment is processing."""
        return self._status == self.STATUS_PROCESSING
    
    def requires_action(self) -> bool:
        """Check if payment requires user action."""
        return self._status == self.STATUS_REQUIRES_ACTION
    
    def is_pending(self) -> bool:
        """Check if payment is in any pending state."""
        pending_statuses = [
            self.STATUS_CREATED,
            self.STATUS_PROCESSING,
            self.STATUS_REQUIRES_ACTION,
            self.STATUS_REQUIRES_CONFIRMATION,
            self.STATUS_REQUIRES_PAYMENT_METHOD,
        ]
        return self._status in pending_statuses
    
    def is_terminal(self) -> bool:
        """Check if payment is in a terminal state."""
        terminal_statuses = [
            self.STATUS_SUCCEEDED,
            self.STATUS_CANCELED,
            self.STATUS_FAILED,
        ]
        return self._status in terminal_statuses
    
    def get_amount_dollars(self) -> float:
        """Get amount in dollars."""
        return self._amount_cents / 100.0
    
    def has_error(self) -> bool:
        """Check if payment has an error."""
        return self._error_code is not None or self._error_message is not None
    
    def increment_webhook_count(self):
        """Increment webhook counter."""
        self._webhook_count += 1
        self._last_webhook_utc_ts = dt.datetime.now(dt.UTC).timestamp()
    
    def set_error(self, error_code: str, error_message: str, error_type: str | None = None):
        """Set error information."""
        self._error_code = error_code
        self._error_message = error_message
        self._error_type = error_type
    
    def clear_error(self):
        """Clear error information."""
        self._error_code = None
        self._error_message = None
        self._error_type = None
    
    def mark_as_canceled(self, reason: str | None = None):
        """Mark the intent as canceled."""
        self.status = self.STATUS_CANCELED
        self._canceled_utc_ts = dt.datetime.now(dt.UTC).timestamp()
        self._cancellation_reason = reason
    
    def get_status_duration_seconds(self) -> float | None:
        """Get duration in current status (in seconds)."""
        if not self._last_status_change_utc_ts:
            return None
        return dt.datetime.now(dt.UTC).timestamp() - self._last_status_change_utc_ts
