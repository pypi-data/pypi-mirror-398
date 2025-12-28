"""
SubscriptionManagerService for managing subscription plans, addons, usage, and discounts.

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
from geek_cafe_saas_sdk.modules.subscriptions.models import Plan, Addon, UsageRecord, Discount


class SubscriptionManagerService(DatabaseService[Plan]):
    """
    Service for managing subscription catalog: plans, addons, usage, and discounts.
    
    This service manages the platform-wide subscription configuration:
    - Plans: Tier definitions (Free, Pro, Enterprise)
    - Addons: Billable modules (Chat, Voting, Storage)
    - Usage Records: Metered billing events
    - Discounts: Promo codes and credits
    
    Note: This is separate from SubscriptionService which manages
    per-tenant subscription instances.
    """
    
    
    # ========================================================================
    # Abstract Method Implementations (DatabaseService)
    # ========================================================================
    
    def create(self, **kwargs) -> ServiceResult[Plan]:
        """Create a plan (delegates to create_plan)."""
        return self.create_plan(**kwargs)
    
    def get_by_id(self, id: str, **kwargs) -> ServiceResult[Plan]:
        """Get a plan by ID."""
        return self.get_plan(plan_id=id)
    
    def update(self, id: str, updates: Dict[str, Any], **kwargs) -> ServiceResult[Plan]:
        """Update a plan."""
        return self.update_plan(plan_id=id, updates=updates)
    
    def delete(self, id: str, **kwargs) -> ServiceResult[Plan]:
        """Archive a plan (soft delete)."""
        return self.archive_plan(plan_id=id)
    
    # ========================================================================
    # Plan Management
    # ========================================================================
    
    def create_plan(
        self,
        plan_code: str,
        plan_name: str,
        price_monthly_cents: int,
        **kwargs
    ) -> ServiceResult[Plan]:
        """
        Create a new subscription plan.
        
        Args:
            plan_code: Unique plan identifier
            plan_name: Display name
            price_monthly_cents: Monthly price in cents
            **kwargs: Additional plan fields
            
        Returns:
            ServiceResult with Plan
        """
        try:
            plan = Plan()

            # Set optional fields
            plan = plan.map(kwargs)
            
            # Set known fields
            plan.plan_code = plan_code
            plan.plan_name = plan_name
            plan.price_monthly_cents = price_monthly_cents
            
            
            
            # Validate
            is_valid, errors = plan.validate()
            if not is_valid:
                return ServiceResult.error_result(
                    message=f"Validation failed: {', '.join(errors)}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Save using helper method - automatically handles pk/sk from _setup_indexes()
            plan.prep_for_save()
            return self._save_model(plan)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "create_plan")
    
    def get_plan(self, plan_id: str) -> ServiceResult[Plan]:
        """Get a plan by ID."""
        try:
            plan = self._get_model_by_id(plan_id, Plan)
            
            if not plan:
                return ServiceResult.error_result(
                    message=f"Plan not found: {plan_id}",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            return ServiceResult.success_result(plan)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_plan")
    
    def get_plan_by_code(self, plan_code: str) -> ServiceResult[Plan]:
        """Get a plan by plan code."""
        try:
            # Query using GSI on plan_code
            # This assumes plans are queryable by code
            plans = self.list_plans(status="active")
            
            if not plans.success:
                return plans
            
            for plan in plans.data:
                if plan.plan_code == plan_code:
                    return ServiceResult.success_result(plan)
            
            return ServiceResult.error_result(
                message=f"Plan not found with code: {plan_code}",
                error_code=ErrorCode.NOT_FOUND
            )
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_plan_by_code")
    
    def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> ServiceResult[Plan]:
        """Update a plan."""
        try:
            # Get existing plan
            result = self.get_plan(plan_id)
            if not result.success:
                return result
            
            plan = result.data
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(plan, key) and not key.startswith('_'):
                    setattr(plan, key, value)
            
            # Validate
            is_valid, errors = plan.validate()
            if not is_valid:
                return ServiceResult.error_result(
                    message=f"Validation failed: {', '.join(errors)}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Increment version
            plan.version += 1
            plan.prep_for_save()
            
            # Save using helper method
            return self._save_model(plan)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "update_plan")
    
    def archive_plan(self, plan_id: str) -> ServiceResult[Plan]:
        """Archive a plan (soft delete)."""
        return self.update_plan(plan_id, {"status": Plan.STATUS_ARCHIVED})
    
    def list_plans(
        self,
        status: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 50
    ) -> ServiceResult[List[Plan]]:
        """
        List plans with optional filters.
        
        Args:
            status: Filter by status
            is_public: Filter by public visibility
            limit: Maximum results
            
        Returns:
            ServiceResult with list of Plans
        """
        try:
            # Create temp plan for query
            temp_plan = Plan()
            
            if status:
                # Use GSI1 to query by status (already sorted by sort_order + name)
                temp_plan.status = status
                query_result = self._query_by_index(temp_plan, "gsi1", limit=limit, ascending=True)
            else:
                # Use GSI2 to get all plans (sorted by code)
                query_result = self._query_by_index(temp_plan, "gsi2", limit=limit, ascending=True)
            
            if not query_result.success:
                return query_result
            
            # Apply additional filters
            plans = []
            for plan in query_result.data:
                if is_public is not None and plan.is_public != is_public:
                    continue
                plans.append(plan)
            
            return ServiceResult.success_result(plans)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "list_plans")
    
    # ========================================================================
    # Addon Management
    # ========================================================================
    
    def create_addon(
        self,
        addon_code: str,
        addon_name: str,
        pricing_model: str,
        **kwargs
    ) -> ServiceResult[Addon]:
        """
        Create a new addon.
        
        Args:
            addon_code: Unique addon identifier
            addon_name: Display name
            pricing_model: "fixed", "per_unit", or "tiered"
            **kwargs: Additional addon fields
            
        Returns:
            ServiceResult with Addon
        """
        try:
            addon = Addon()
            # Set optional fields
            addon = addon.map(kwargs)
            # Set known fields
            addon.addon_code = addon_code
            addon.addon_name = addon_name
            addon.pricing_model = pricing_model
            
            
            
            # Validate
            is_valid, errors = addon.validate()
            if not is_valid:
                return ServiceResult.error_result(
                    message=f"Validation failed: {', '.join(errors)}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Save using helper method - automatically handles pk/sk from _setup_indexes()
            addon.prep_for_save()
            return self._save_model(addon)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "create_addon")
    
    def get_addon(self, addon_id: str) -> ServiceResult[Addon]:
        """Get an addon by ID."""
        try:
            addon = self._get_model_by_id(addon_id, Addon)
            
            if not addon:
                return ServiceResult.error_result(
                    message=f"Addon not found: {addon_id}",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            return ServiceResult.success_result(addon)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_addon")
    
    def get_addon_by_code(self, addon_code: str) -> ServiceResult[Addon]:
        """Get an addon by addon code."""
        try:
            addons = self.list_addons(status="active")
            
            if not addons.success:
                return addons
            
            for addon in addons.data:
                if addon.addon_code == addon_code:
                    return ServiceResult.success_result(addon)
            
            return ServiceResult.error_result(
                message=f"Addon not found with code: {addon_code}",
                error_code=ErrorCode.NOT_FOUND
            )
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_addon_by_code")
    
    def update_addon(self, addon_id: str, updates: Dict[str, Any]) -> ServiceResult[Addon]:
        """Update an addon."""
        try:
            result = self.get_addon(addon_id)
            if not result.success:
                return result
            
            addon = result.data
            
            for key, value in updates.items():
                if hasattr(addon, key) and not key.startswith('_'):
                    setattr(addon, key, value)
            
            is_valid, errors = addon.validate()
            if not is_valid:
                return ServiceResult.error_result(
                    message=f"Validation failed: {', '.join(errors)}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            addon.version += 1
            addon.prep_for_save()
            
            return self._save_model(addon)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "update_addon")
    
    def list_addons(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> ServiceResult[List[Addon]]:
        """List addons with optional filters."""
        try:
            # Create temp addon for query
            temp_addon = Addon()
            
            if status:
                # Use GSI1 to query by status (already sorted by category + sort_order)
                temp_addon.status = status
                if category:
                    temp_addon.category = category
                query_result = self._query_by_index(temp_addon, "gsi1", limit=limit, ascending=True)
            else:
                # Use GSI2 to get all addons
                query_result = self._query_by_index(temp_addon, "gsi2", limit=limit, ascending=True)
            
            if not query_result.success:
                return query_result
            
            # Apply additional filters if needed
            addons = []
            for addon in query_result.data:
                if category and status is None and addon.category != category:
                    continue
                addons.append(addon)
            
            return ServiceResult.success_result(addons)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "list_addons")
    
    # ========================================================================
    # Usage Record Management
    # ========================================================================
    
    def record_usage(
        self,
        subscription_id: str,
        addon_code: str,
        meter_event_name: str,
        quantity: float,
        **kwargs
    ) -> ServiceResult[UsageRecord]:
        """
        Record a usage event for metered billing.
        
        Args:
            subscription_id: Subscription ID
            addon_code: Addon code
            meter_event_name: Event name
            quantity: Usage quantity
            **kwargs: Additional fields
            
        Returns:
            ServiceResult with UsageRecord
        """
        try:
            # Get tenant from request_context
            tenant_id = self.request_context.target_tenant_id
            
            # Check for idempotency
            idempotency_key = kwargs.get('idempotency_key')
            if idempotency_key:
                existing = self._get_usage_by_idempotency_key(idempotency_key)
                if existing:
                    return ServiceResult.success_result(existing)
            
            usage = UsageRecord()
            # Set optional fields
            usage = usage.map(kwargs)

            # Set known fields
            usage.tenant_id = tenant_id
            usage.subscription_id = subscription_id
            usage.addon_code = addon_code
            usage.meter_event_name = meter_event_name
            usage.quantity = quantity
            usage.timestamp_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            
            
            
            # Save
            usage.prep_for_save()
            return self._save_model(usage)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "record_usage")
    
    def _get_usage_by_idempotency_key(self, idempotency_key: str) -> Optional[UsageRecord]:
        """Check if usage record exists with idempotency key."""
        try:
            # This would require a GSI on idempotency_key
            # For now, return None (no deduplication)
            return None
        except:
            return None
    
    def get_usage_for_period(
        self,
        subscription_id: str,
        addon_code: str,
        period_start: float,
        period_end: float
    ) -> ServiceResult[List[UsageRecord]]:
        """
        Get usage records for a billing period.
        
        Args:
            tenant_id: Tenant ID
            subscription_id: Subscription ID
            addon_code: Addon code
            period_start: Period start timestamp
            period_end: Period end timestamp
            
        Returns:
            ServiceResult with list of UsageRecords
        """
        try:
            # This would ideally use a GSI for efficient querying
            # For now, scan with filters
            result = self.dynamodb.scan(
                table_name=self.table_name
            )
            
            records = []
            for item in result.get('Items', []):
                if item.get('pk', '').startswith('usage#'):
                    usage = UsageRecord()
                    usage.map(item)
                    
                    if (usage.tenant_id == tenant_id and
                        usage.subscription_id == subscription_id and
                        usage.addon_code == addon_code and
                        period_start <= usage.timestamp_utc_ts <= period_end):
                        records.append(usage)
            
            return ServiceResult.success_result(records)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_usage_for_period")
    
    def aggregate_usage(
        self,
        subscription_id: str,
        addon_code: str,
        period_start: float,
        period_end: float
    ) -> ServiceResult[float]:
        """Aggregate total usage for a period."""
        try:
            result = self.get_usage_for_period(
                tenant_id, subscription_id, addon_code,
                period_start, period_end
            )
            
            if not result.success:
                return result
            
            total = sum(record.quantity for record in result.data)
            return ServiceResult.success_result(total)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "aggregate_usage")
    
    # ========================================================================
    # Discount Management
    # ========================================================================
    
    def create_discount(
        self,
        discount_code: str,
        discount_name: str,
        discount_type: str,
        **kwargs
    ) -> ServiceResult[Discount]:
        """
        Create a new discount/promo code.
        
        Args:
            discount_code: Unique code (e.g., "SUMMER25")
            discount_name: Display name
            discount_type: "percentage", "fixed", "credit", "trial_extension"
            **kwargs: Additional fields
            
        Returns:
            ServiceResult with Discount
        """
        try:
            discount = Discount()
            # Set optional fields
            discount = discount.map(kwargs)

            # Set known fields
            discount.discount_code = discount_code
            discount.discount_name = discount_name
            discount.discount_type = discount_type
            
            
            
            is_valid, errors = discount.validate()
            if not is_valid:
                return ServiceResult.error_result(
                    message=f"Validation failed: {', '.join(errors)}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            discount.prep_for_save()
            return self._save_model(discount)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "create_discount")
    
    def get_discount(self, discount_id: str) -> ServiceResult[Discount]:
        """Get a discount by ID."""
        try:
            discount = self._get_model_by_id(discount_id, Discount)
            
            if not discount:
                return ServiceResult.error_result(
                    message=f"Discount not found: {discount_id}",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            return ServiceResult.success_result(discount)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_discount")
    
    def get_discount_by_code(self, discount_code: str) -> ServiceResult[Discount]:
        """Get a discount by code."""
        try:
            discounts = self.list_discounts(status="active")
            
            if not discounts.success:
                return discounts
            
            for discount in discounts.data:
                if discount.discount_code == discount_code.upper():
                    return ServiceResult.success_result(discount)
            
            return ServiceResult.error_result(
                message=f"Discount not found with code: {discount_code}",
                error_code=ErrorCode.NOT_FOUND
            )
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_discount_by_code")
    
    def validate_discount(
        self,
        discount_code: str,
        plan_code: Optional[str] = None,
        amount_cents: Optional[int] = None,
        is_first_purchase: bool = False
    ) -> ServiceResult[Discount]:
        """
        Validate that a discount can be applied.
        
        Args:
            discount_code: Discount code to validate
            plan_code: Plan code (optional)
            amount_cents: Purchase amount (optional)
            is_first_purchase: Whether this is first purchase
            
        Returns:
            ServiceResult with Discount if valid
        """
        try:
            result = self.get_discount_by_code(discount_code)
            if not result.success:
                return result
            
            discount = result.data
            
            # Check if can be redeemed
            if not discount.can_be_redeemed():
                return ServiceResult.error_result(
                    message="Discount code is not currently valid",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Check plan restriction
            if plan_code and not discount.applies_to_plan(plan_code):
                return ServiceResult.error_result(
                    message=f"Discount does not apply to plan: {plan_code}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Check minimum amount
            if amount_cents and discount.minimum_amount_cents:
                if amount_cents < discount.minimum_amount_cents:
                    min_dollars = discount.minimum_amount_cents / 100.0
                    return ServiceResult.error_result(
                        message=f"Minimum purchase amount is ${min_dollars:.2f}",
                        error_code=ErrorCode.VALIDATION_ERROR
                    )
            
            # Check first-time restriction
            if discount.first_time_transaction and not is_first_purchase:
                return ServiceResult.error_result(
                    message="Discount only valid for first-time purchases",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            return ServiceResult.success_result(discount)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "validate_discount")
    
    def redeem_discount(self, discount_id: str) -> ServiceResult[Discount]:
        """Increment redemption count for a discount."""
        try:
            result = self.get_discount(discount_id)
            if not result.success:
                return result
            
            discount = result.data
            discount.increment_redemption_count()
            
            discount.prep_for_save()
            return self._save_model(discount)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "redeem_discount")
    
    def list_discounts(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> ServiceResult[List[Discount]]:
        """List discounts with optional filters."""
        try:
            # Create temp discount for query
            temp_discount = Discount()
            
            if status:
                # Use GSI1 to query by status
                temp_discount.status = status
                query_result = self._query_by_index(temp_discount, "gsi1", limit=limit, ascending=False)
            else:
                # Use GSI2 to get all discounts
                query_result = self._query_by_index(temp_discount, "gsi2", limit=limit, ascending=True)
            
            if not query_result.success:
                return query_result
            
            return ServiceResult.success_result(query_result.data)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "list_discounts")
