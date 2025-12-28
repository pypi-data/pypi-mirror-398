"""PaymentService for payment operations with DynamoDB and PSP integration.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional, List
import datetime as dt
from boto3.dynamodb.conditions import Key
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.modules.payments.models.billing_account import BillingAccount
from geek_cafe_saas_sdk.modules.payments.models.payment_intent_ref import PaymentIntentRef
from geek_cafe_saas_sdk.modules.payments.models.payment import Payment
from geek_cafe_saas_sdk.modules.payments.models.refund import Refund


class PaymentService(DatabaseService[Payment]):
    """Service for managing payments, billing accounts, and refunds."""
    
    
    
    # Abstract method implementations (delegating to specific methods)
    def create(self, **kwargs) -> ServiceResult[Payment]:
        """Create method - delegates to record_payment."""
        return self.record_payment(**kwargs)
    
    def get_by_id(self, payment_id: str, **kwargs) -> ServiceResult[Payment]:
        """Get by ID method - delegates to get_payment."""
        tenant_id = kwargs.get("tenant_id")
        return self.get_payment(payment_id=payment_id, tenant_id=tenant_id)
    
    def update(self, payment_id: str, updates: Dict[str, Any], **kwargs) -> ServiceResult[Payment]:
        """Update method - not supported for immutable payments."""
        return ServiceResult.error_result(
            message="Direct payment updates not supported (payments are immutable)",
            error_code="OPERATION_NOT_SUPPORTED"
        )
    
    def delete(self, payment_id: str, **kwargs) -> ServiceResult[bool]:
        """Delete method - not supported for payments."""
        return ServiceResult.error_result(
            message="Payment deletion not supported (use refunds instead)",
            error_code="OPERATION_NOT_SUPPORTED"
        )
    
    # ====================
    # BILLING ACCOUNT METHODS
    # ====================
    
    @service_method("create_billing_account")
    def create_billing_account(
        self,
        account_holder_id: str,
        account_holder_type: str = "user",
        currency_code: str = "USD",
        billing_email: Optional[str] = None,
        **kwargs
    ) -> ServiceResult[BillingAccount]:
        """Create a new billing account."""
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        try:
            account = BillingAccount()
            
            account.tenant_id = tenant_id
            account.user_id = user_id  # Required by BaseTenantUserModel
            account.account_holder_id = account_holder_id
            account.account_holder_type = account_holder_type
            account.currency_code = currency_code
            account.billing_email = billing_email
            account.prep_for_save()
            
            # Set optional fields
            account = account.map(kwargs)
            
            # Validate
            is_valid, errors = account.validate()
            if not is_valid:
                raise ValidationError(f"Validation failed: {', '.join(errors)}", "billing_account")
            
            # Save to DynamoDB
            account.prep_for_save()
            return self._save_model(account)
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "create_billing_account")
    
    def get_billing_account(self, account_id: str) -> ServiceResult[BillingAccount]:
        """Get billing account by ID."""
        self.request_context.require_authentication()
        try:
            account = self._get_by_id(account_id, BillingAccount)
            
            if not account:
                raise NotFoundError(f"Billing account not found: {account_id}")
            
            return ServiceResult.success_result(account)
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_billing_account")
    
    def update_billing_account(
        self,
        account_id: str,
        updates: Dict[str, Any]
    ) -> ServiceResult[BillingAccount]:
        """Update billing account."""
        self.request_context.require_authentication()
        try:
            # Get current account
            result = self.get_billing_account(account_id)
            if not result.success:
                return result
            
            account = result.data
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(account, key):
                    setattr(account, key, value)
            
            account.modified_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            
            # Validate
            is_valid, errors = account.validate()
            if not is_valid:
                raise ValidationError(f"Validation failed: {', '.join(errors)}", "billing_account")
            
            # Save
            account.prep_for_save()
            return self._save_model(account)
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "update_billing_account")
    
    # ====================
    # PAYMENT INTENT METHODS
    # ====================
    
    @service_method("create_payment_intent")
    def create_payment_intent(
        self,
        billing_account_id: str,
        amount_cents: int,
        currency_code: str = "USD",
        psp_type: str = "stripe",
        **kwargs
    ) -> ServiceResult[PaymentIntentRef]:
        """Create a payment intent reference."""
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        try:
            intent = PaymentIntentRef()
            intent.tenant_id = tenant_id
            intent.user_id = user_id  # Required by BaseTenantUserModel
            intent.billing_account_id = billing_account_id
            intent.amount_cents = amount_cents
            intent.currency_code = currency_code
            intent.psp_type = psp_type
            # Note: created_utc_ts will be set by prep_for_save()
            
            intent = intent.map(kwargs)
            
            # Save
            intent.prep_for_save()
            return self._save_model(intent)
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "create_payment_intent")
    
    def get_payment_intent(self, intent_ref_id: str) -> ServiceResult[PaymentIntentRef]:
        """Get payment intent by ID."""
        self.request_context.require_authentication()
        try:
            intent = self._get_by_id(intent_ref_id, PaymentIntentRef)
            
            if not intent:
                raise NotFoundError(f"Payment intent not found: {intent_ref_id}")
            
            return ServiceResult.success_result(intent)
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_payment_intent")
    
    def update_payment_intent_status(
        self,
        intent_ref_id: str,
        status: str,
        **kwargs
    ) -> ServiceResult[PaymentIntentRef]:
        """Update payment intent status."""
        self.request_context.require_authentication()
        try:
            result = self.get_payment_intent(intent_ref_id)
            if not result.success:
                return result
            
            intent = result.data
            intent = intent.map(kwargs)
            intent.status = status
            intent.modified_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            
            
            
            # Save
            intent.prep_for_save()
            return self._save_model(intent)
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "update_payment_intent_status")
    
    # ====================
    # PAYMENT METHODS
    # ====================
    
    @service_method("record_payment")
    def record_payment(
        self,
        billing_account_id: str,
        payment_intent_ref_id: Optional[str],
        gross_amount_cents: int,
        fee_amount_cents: int,
        currency_code: str = "USD",
        psp_type: str = "stripe",
        **kwargs
    ) -> ServiceResult[Payment]:
        """Record a settled payment."""
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        try:
            payment = Payment()
            # set optional fields
            payment = payment.map(kwargs)
            # set known fields
            payment.tenant_id = tenant_id
            payment.user_id = user_id  # Required by BaseTenantUserModel
            payment.billing_account_id = billing_account_id
            payment.payment_intent_ref_id = payment_intent_ref_id
            payment.gross_amount_cents = gross_amount_cents
            payment.fee_amount_cents = fee_amount_cents
            payment.currency_code = currency_code
            payment.psp_type = psp_type
            payment.settled_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            payment.status = "succeeded"
            
            # Save payment
            payment.prep_for_save()
            save_result = self._save_model(payment)
            
            if not save_result.success:
                return save_result
            
            # Update the payment intent to link back to this payment
            if payment_intent_ref_id:
                intent = self._get_by_id(
                    payment_intent_ref_id, PaymentIntentRef
                )
                if intent:
                    intent.payment_id = payment.payment_id
                    intent.status = PaymentIntentRef.STATUS_SUCCEEDED
                    intent.prep_for_save()
                    self._save_model(intent)
            
            return save_result
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "record_payment")
    
    def get_payment(self, payment_id: str) -> ServiceResult[Payment]:
        """Get payment by ID."""
        self.request_context.require_authentication()
        try:
            payment = self._get_by_id(payment_id, Payment)
            
            if not payment:
                raise NotFoundError(f"Payment not found: {payment_id}")
            
            return ServiceResult.success_result(payment)
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_payment")
    
    def list_payments(
        self,
        billing_account_id: Optional[str] = None,
        limit: int = 50
    ) -> ServiceResult[List[Payment]]:
        """List payments for a tenant or billing account."""
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            # Create temp payment with appropriate fields for query
            temp_payment = Payment()
            
            if billing_account_id:
                # Use GSI2 to query by billing account
                temp_payment.billing_account_id = billing_account_id
                gsi_name = "gsi2"
            else:
                # Use GSI1 to query by tenant
                temp_payment.tenant_id = tenant_id
                gsi_name = "gsi1"
            
            # Query using helper method
            query_result = self._query_by_index(temp_payment, gsi_name, limit=limit, ascending=False)
            
            if not query_result.success:
                return query_result
            
            return ServiceResult.success_result(query_result.data)
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "list_payments")
    
    # ====================
    # REFUND METHODS
    # ====================
    
    @service_method("create_refund")
    def create_refund(
        self,
        payment_id: str,
        amount_cents: int,
        reason: Optional[str] = None,
        initiated_by_id: Optional[str] = None,
        **kwargs
    ) -> ServiceResult[Refund]:
        """Create a refund for a payment."""
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        try:
            # Get the payment
            payment_result = self.get_payment(payment_id)
            if not payment_result.success:
                return payment_result
            
            payment = payment_result.data
            
            # Validate refund amount
            remaining = payment.get_remaining_amount_cents()
            if amount_cents > remaining:
                raise ValidationError(
                    f"Refund amount ({amount_cents}) exceeds remaining amount ({remaining})",
                    "amount_cents"
                )
            
            # Create refund
            refund = Refund()
            # set optional fields
            refund = refund.map(kwargs)
            # set known fields
            refund.tenant_id = tenant_id
            refund.user_id = user_id  # Required by BaseTenantUserModel
            refund.payment_id = payment_id
            refund.billing_account_id = payment.billing_account_id
            refund.amount_cents = amount_cents
            refund.currency_code = payment.currency_code
            refund.psp_type = payment.psp_type
            refund.reason = reason
            refund.initiated_by_id = initiated_by_id or user_id  # Default to user_id if not specified
            refund.initiated_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            
            # Validate
            is_valid, errors = refund.validate()
            if not is_valid:
                raise ValidationError(f"Validation failed: {', '.join(errors)}", "refund")
            
            # Save refund
            refund.prep_for_save()
            refund_result = self._save_model(refund)
            
            if not refund_result.success:
                return refund_result
            
            # Update payment's refund tracking
            payment.add_refund(refund_result.data.refund_id, amount_cents)
            payment.prep_for_save()
            self._save_model(payment)
            
            return ServiceResult.success_result(refund_result.data)
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "create_refund")
    
    def get_refund(self, refund_id: str) -> ServiceResult[Refund]:
        """Get refund by ID."""
        self.request_context.require_authentication()
        try:
            refund = self._get_by_id(refund_id, Refund)
            
            if not refund:
                raise NotFoundError(f"Refund not found: {refund_id}")
            
            return ServiceResult.success_result(refund)
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_refund")
    
    def update_refund_status(
        self,
        refund_id: str,
        status: str,
        **kwargs
    ) -> ServiceResult[Refund]:
        """Update refund status."""
        try:
            result = self.get_refund(refund_id)
            if not result.success:
                return result
            
            refund = result.data
            refund = refund.map(kwargs)
            refund.status = status
            refund.modified_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            
            if status == Refund.STATUS_SUCCEEDED:
                refund.succeeded_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            elif status == Refund.STATUS_FAILED:
                refund.failed_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            
            
            
            # Save
            refund.prep_for_save()
            return self._save_model(refund)
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "update_refund_status")
