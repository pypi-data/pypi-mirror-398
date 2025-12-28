"""
Refund model for payment system.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import datetime as dt
from typing import Optional, Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class Refund(BaseTenantUserModel):
    """
    Refund - Reversal metadata for payment refunds.
    
    Represents a refund transaction that reverses all or part of a payment.
    Contains details about the refund amount, reason, and status.
    Links back to the original payment.
    
    Multi-Tenancy:
    - tenant_id: Organization/company issuing the refund
    
    Access Patterns (DynamoDB Keys):
    - pk: REFUND#{tenant_id}#{refund_id}
    - sk: metadata
    - gsi1_pk: tenant#{tenant_id}
    - gsi1_sk: REFUND#{created_utc_ts}
    - gsi2_pk: PAYMENT#{payment_id}
    - gsi2_sk: REFUND#{created_utc_ts}
    - gsi3_pk: PSP_REFUND#{psp_type}#{psp_refund_id}
    - gsi3_sk: metadata
    """

    def __init__(self):
        super().__init__()
        
        # Identity (inherited from BaseModel: id, tenant_id)
        self._payment_id: str | None = None  # Original payment being refunded
        self._billing_account_id: str | None = None  # Associated billing account
        
        # PSP Information
        self._psp_type: str = "stripe"  # "stripe", "paypal", "square", etc.
        self._psp_refund_id: str | None = None  # PSP's refund identifier
        self._psp_balance_transaction_id: str | None = None  # PSP balance transaction
        
        # Refund Amount (in cents to avoid float issues)
        self._amount_cents: int = 0  # Amount being refunded
        self._currency_code: str = "USD"  # ISO 4217 currency code
        
        # Refund Details
        self._reason: str | None = None  # "duplicate", "fraudulent", "requested_by_customer"
        self._description: str | None = None  # Detailed reason/notes
        
        # Status
        self._status: str = "pending"  # "pending", "succeeded", "failed", "canceled"
        self._failure_reason: str | None = None  # Reason if failed
        
        # Processing Details
        self._initiated_utc_ts: float | None = None  # When refund was initiated
        self._succeeded_utc_ts: float | None = None  # When refund succeeded
        self._failed_utc_ts: float | None = None  # When refund failed
        
        # Receipt
        self._receipt_number: str | None = None  # Refund receipt number
        
        # Metadata
        self._initiated_by_id: str | None = None  # User who initiated refund
        self._notes: str | None = None  # Internal notes
        
        # Related Records
        self._dispute_id: str | None = None  # Related dispute (if applicable)
        
        # Additional PSP Data
        self._psp_metadata: Dict[str, Any] | None = None  # Raw PSP data
        
        # Setup indexes
        self._setup_indexes()
        
        # Mark initialization as complete
        object.__setattr__(self, '_initializing', False)
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for refund queries."""
        
        # Primary index: Refund by ID
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("refund", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Refunds by tenant
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("refund", self.created_utc_ts))
        self.indexes.add_secondary(gsi)
        
        # GSI2: Refunds by payment
        gsi = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("payment", self.payment_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("refund", self.created_utc_ts))
        self.indexes.add_secondary(gsi)
    
    # Refund Reason Constants
    REASON_DUPLICATE = "duplicate"
    REASON_FRAUDULENT = "fraudulent"
    REASON_REQUESTED_BY_CUSTOMER = "requested_by_customer"
    REASON_EXPIRED_UNCAPTURED_CHARGE = "expired_uncaptured_charge"
    
    # Status Constants
    STATUS_PENDING = "pending"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CANCELED = "canceled"
    
    # Properties - Identity
    @property
    def refund_id(self) -> str | None:
        """Unique refund ID (alias for id)."""
        return self.id
    
    @refund_id.setter
    def refund_id(self, value: str | None):
        self.id = value
    
    @property
    def payment_id(self) -> str | None:
        """Original payment being refunded."""
        return self._payment_id
    
    @payment_id.setter
    def payment_id(self, value: str | None):
        self._payment_id = value
    
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
    def psp_refund_id(self) -> str | None:
        """PSP refund identifier."""
        return self._psp_refund_id
    
    @psp_refund_id.setter
    def psp_refund_id(self, value: str | None):
        self._psp_refund_id = value
    
    @property
    def psp_balance_transaction_id(self) -> str | None:
        """PSP balance transaction ID."""
        return self._psp_balance_transaction_id
    
    @psp_balance_transaction_id.setter
    def psp_balance_transaction_id(self, value: str | None):
        self._psp_balance_transaction_id = value
    
    # Properties - Amount
    @property
    def amount_cents(self) -> int:
        """Refund amount in cents."""
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
    
    # Properties - Refund Details
    @property
    def reason(self) -> str | None:
        """Refund reason."""
        return self._reason
    
    @reason.setter
    def reason(self, value: str | None):
        valid_reasons = [
            self.REASON_DUPLICATE,
            self.REASON_FRAUDULENT,
            self.REASON_REQUESTED_BY_CUSTOMER,
            self.REASON_EXPIRED_UNCAPTURED_CHARGE,
        ]
        if value and value not in valid_reasons:
            # Allow custom reasons, but warn
            pass
        self._reason = value
    
    @property
    def description(self) -> str | None:
        """Detailed refund description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    # Properties - Status
    @property
    def status(self) -> str:
        """Refund status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        valid_statuses = [
            self.STATUS_PENDING,
            self.STATUS_SUCCEEDED,
            self.STATUS_FAILED,
            self.STATUS_CANCELED,
        ]
        if value not in valid_statuses:
            raise ValueError(f"Invalid status: {value}. Must be one of {valid_statuses}")
        self._status = value
    
    @property
    def failure_reason(self) -> str | None:
        """Failure reason if refund failed."""
        return self._failure_reason
    
    @failure_reason.setter
    def failure_reason(self, value: str | None):
        self._failure_reason = value
    
    # Properties - Processing Details
    @property
    def initiated_utc_ts(self) -> float | None:
        """Timestamp when refund was initiated."""
        return self._initiated_utc_ts
    
    @initiated_utc_ts.setter
    def initiated_utc_ts(self, value: float | None):
        self._initiated_utc_ts = value
    
    @property
    def succeeded_utc_ts(self) -> float | None:
        """Timestamp when refund succeeded."""
        return self._succeeded_utc_ts
    
    @succeeded_utc_ts.setter
    def succeeded_utc_ts(self, value: float | None):
        self._succeeded_utc_ts = value
    
    @property
    def failed_utc_ts(self) -> float | None:
        """Timestamp when refund failed."""
        return self._failed_utc_ts
    
    @failed_utc_ts.setter
    def failed_utc_ts(self, value: float | None):
        self._failed_utc_ts = value
    
    # Properties - Receipt
    @property
    def receipt_number(self) -> str | None:
        """Refund receipt number."""
        return self._receipt_number
    
    @receipt_number.setter
    def receipt_number(self, value: str | None):
        self._receipt_number = value
    
    # Properties - Metadata
    @property
    def initiated_by_id(self) -> str | None:
        """User who initiated the refund."""
        return self._initiated_by_id
    
    @initiated_by_id.setter
    def initiated_by_id(self, value: str | None):
        self._initiated_by_id = value
    
    @property
    def notes(self) -> str | None:
        """Internal notes."""
        return self._notes
    
    @notes.setter
    def notes(self, value: str | None):
        self._notes = value
    
    # Properties - Related Records
    @property
    def dispute_id(self) -> str | None:
        """Related dispute ID (if applicable)."""
        return self._dispute_id
    
    @dispute_id.setter
    def dispute_id(self, value: str | None):
        self._dispute_id = value
    
    # Properties - Additional Data
    @property
    def psp_metadata(self) -> Dict[str, Any] | None:
        """Raw PSP metadata."""
        return self._psp_metadata
    
    @psp_metadata.setter
    def psp_metadata(self, value: Dict[str, Any] | None):
        self._psp_metadata = value if isinstance(value, dict) else None
    
    # Helper Methods
    def is_pending(self) -> bool:
        """Check if refund is pending."""
        return self._status == self.STATUS_PENDING
    
    def is_succeeded(self) -> bool:
        """Check if refund succeeded."""
        return self._status == self.STATUS_SUCCEEDED
    
    def is_failed(self) -> bool:
        """Check if refund failed."""
        return self._status == self.STATUS_FAILED
    
    def is_canceled(self) -> bool:
        """Check if refund was canceled."""
        return self._status == self.STATUS_CANCELED
    
    def get_amount_dollars(self) -> float:
        """Get refund amount in dollars."""
        return self._amount_cents / 100.0
    
    def mark_as_succeeded(self):
        """Mark refund as succeeded."""
        self._status = self.STATUS_SUCCEEDED
        self._succeeded_utc_ts = dt.datetime.now(dt.UTC).timestamp()
    
    def mark_as_failed(self, reason: str | None = None):
        """Mark refund as failed."""
        self._status = self.STATUS_FAILED
        self._failed_utc_ts = dt.datetime.now(dt.UTC).timestamp()
        self._failure_reason = reason
    
    def mark_as_canceled(self):
        """Mark refund as canceled."""
        self._status = self.STATUS_CANCELED
    
    def get_processing_duration_seconds(self) -> float | None:
        """Get processing duration in seconds (from initiation to completion)."""
        if not self._initiated_utc_ts:
            return None
        
        end_ts = self._succeeded_utc_ts or self._failed_utc_ts
        if not end_ts:
            # Still processing
            return dt.datetime.now(dt.UTC).timestamp() - self._initiated_utc_ts
        
        return end_ts - self._initiated_utc_ts
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the refund.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Required fields
        if not self.tenant_id:
            errors.append("tenant_id is required")
        if not self._payment_id:
            errors.append("payment_id is required")
        if self._amount_cents <= 0:
            errors.append("amount_cents must be greater than 0")
        if not self._currency_code:
            errors.append("currency_code is required")
        
        return (len(errors) == 0, errors)
