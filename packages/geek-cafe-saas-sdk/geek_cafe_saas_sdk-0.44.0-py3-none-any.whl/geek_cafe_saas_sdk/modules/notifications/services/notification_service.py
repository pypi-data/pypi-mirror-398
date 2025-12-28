"""
NotificationService - Multi-channel notification delivery.

Handles notification creation, delivery, state management, and user preferences.
Supports email, SMS, in-app, push, and webhook channels.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import datetime as dt
from typing import Optional, Dict, List, Any
from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3.dynamodb.conditions import Key
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.modules.notifications.models import (
    Notification,
    NotificationPreference,
    WebhookSubscription
)


class NotificationService(DatabaseService[Notification]):
    """
    Service for managing notifications and multi-channel delivery.
    
    Features:
    - Multi-channel delivery (email, SMS, push, in-app, webhook)
    - User preference management
    - Quiet hours and DND support
    - Retry logic
    - State tracking
    - Webhook subscriptions
    """
    
    
    
    # ========================================================================
    # Abstract Method Implementations (Required by DatabaseService)
    # ========================================================================
    
    @service_method("create")

    
    def create(self, **kwargs) -> ServiceResult[Notification]:
        """Create a new notification. Delegates to create_notification."""
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        return self.create_notification(
            tenant_id=tenant_id,
            notification_type=kwargs.get('notification_type', 'general'),
            channel=kwargs.get('channel', 'in_app'),
            recipient_id=kwargs.get('recipient_id', user_id),
            **kwargs
        )
    
    @service_method("get_by_id")
    def get_by_id(self, notification_id: str) -> ServiceResult[Notification]:
        """Get notification by ID. Delegates to get_notification."""
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        return self.get_notification(tenant_id=tenant_id, notification_id=notification_id)
    
    @service_method("update")
    def update(self, notification_id: str, updates: Dict[str, Any]) -> ServiceResult[Notification]:
        """Update notification. Delegates to update_notification_state."""
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        return self.update_notification_state(
            tenant_id=tenant_id,
            notification_id=notification_id,
            **updates
        )
    
    @service_method("delete")
    def delete(self, notification_id: str) -> ServiceResult[bool]:
        """Delete (archive) notification by updating its state."""
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            result = self.update_notification_state(
                tenant_id=tenant_id,
                notification_id=notification_id,
                state='archived'
            )
            return ServiceResult.success_result(result.success)
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "delete_notification")
    
    # ========================================================================
    # Notification Operations
    # ========================================================================
    
    def create_notification(
        self,
        notification_type: str,
        channel: str,
        recipient_id: str,
        body: str,
        **kwargs
    ) -> ServiceResult[Notification]:
        """
        Create a new notification.
        
        Args:
            tenant_id: Tenant ID
            notification_type: Type identifier (e.g., "payment_receipt")
            channel: Delivery channel (email, sms, push, in_app, webhook)
            recipient_id: User ID receiving notification
            body: Notification content
            **kwargs: Additional fields (subject, title, template_id, etc.)
            
        Returns:
            ServiceResult with Notification
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        
        try:
            notification = Notification().map(kwargs)
            notification.tenant_id = tenant_id
            notification.user_id = recipient_id  # Required by BaseTenantUserModel
            notification.notification_type = notification_type
            notification.channel = channel
            notification.recipient_id = recipient_id
            notification.body = body
                                
            # Set queued timestamp
            notification.queued_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            
            # Validate
            is_valid, errors = notification.validate()
            if not is_valid:
                return ServiceResult.error_result(
                    message=f"Validation failed: {', '.join(errors)}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Save using helper method - automatically handles pk/sk from _setup_indexes()
            notification.prep_for_save()
            return self._save_model(notification)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "create_notification")
    
    def get_notification(
        self,
        notification_id: str
    ) -> ServiceResult[Notification]:
        """Get a notification by ID."""
        self.request_context.require_authentication()
        
        
        try:
            # Use helper to get notification with tenant check
            notification = self._get_by_id(
                notification_id, Notification
            )
            
            if not notification:
                return ServiceResult.error_result(
                    message=f"Notification not found: {notification_id}",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            return ServiceResult.success_result(notification)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_notification")
    
    def update_notification_state(
        self,
        notification_id: str,
        state: str,
        **kwargs
    ) -> ServiceResult[Notification]:
        """
        Update notification state.
        
        Args:
            tenant_id: Tenant ID
            notification_id: Notification ID
            state: New state (sent, delivered, failed, etc.)
            **kwargs: Additional fields (error_code, provider_message_id, etc.)
            
        Returns:
            ServiceResult with updated Notification
        """
        self.request_context.require_authentication()
        
        try:
            result = self.get_notification(notification_id)
            if not result.success:
                return result
            
            notification = result.data
            notification = notification.map(kwargs)            
            notification.state = state
            
            # Update timestamp based on state
            now = dt.datetime.now(dt.UTC).timestamp()
            if state == Notification.STATE_SENT:
                notification.sent_utc_ts = now
            elif state == Notification.STATE_DELIVERED:
                notification.delivered_utc_ts = now
            elif state == Notification.STATE_FAILED:
                notification.failed_utc_ts = now
            
            # Save
            notification.modified_utc_ts = now
            notification.version += 1
            notification.prep_for_save()
            
            return self._save_model(notification)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "update_notification_state")
    
    def list_notifications(
        self,
        recipient_id: str,
        limit: int = 50,
        unread_only: bool = False
    ) -> ServiceResult[List[Notification]]:
        """
        List notifications for a user.
        
        Args:
            recipient_id: User ID
            limit: Max results
            unread_only: Filter to unread notifications
            
        Returns:
            ServiceResult with list of Notifications
        """
        try:
            # Create temp notification with recipient_id set for index query
            temp_notification = Notification()
            temp_notification.recipient_id = recipient_id
            temp_notification.queued_utc_ts = 0  # Will match all
            
            result = self._query_by_index(
                temp_notification,
                "gsi1",
                ascending=False,  # Most recent first
                limit=limit
            )
            
            if not result.success:
                return result
            
            # Filter unread if requested
            notifications = []
            for notification in result.data:
                if unread_only and notification.read_utc_ts is not None:
                    continue
                notifications.append(notification)
            
            return ServiceResult.success_result(notifications)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "list_notifications")
    
    def mark_as_read(
        self,
        notification_id: str
    ) -> ServiceResult[Notification]:
        """Mark an in-app notification as read."""
        try:
            result = self.get_notification(notification_id)
            if not result.success:
                return result
            
            notification = result.data
            
            if notification.channel == Notification.CHANNEL_IN_APP:
                notification.mark_read(dt.datetime.now(dt.UTC).timestamp())
                notification.prep_for_save()
                return self._save_model(notification)
            
            return ServiceResult.success_result(notification)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "mark_as_read")
    
    # ========================================================================
    # Preference Operations
    # ========================================================================
    
    def get_user_preferences(
        self,
        user_id: str
    ) -> ServiceResult[NotificationPreference]:
        """
        Get user notification preferences.
        
        Creates default preferences if none exist.
        """
        try:
            preferences = NotificationPreference()
            preferences.user_id = user_id
            
            result = self.dynamodb.get(
                table_name=self.table_name,
                model=preferences,
            )
            
            if not result or "Item" not in result:
                # Create default preferences
                preferences = NotificationPreference()
                preferences.user_id = user_id
                return ServiceResult.success_result(preferences)
            
            # Use .map() instead of load_from_dictionary
            preferences = NotificationPreference().map(result["Item"])
            
            return ServiceResult.success_result(preferences)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_user_preferences")
    
    def update_preferences(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> ServiceResult[NotificationPreference]:
        """
        Update user notification preferences.
        
        Args:
            user_id: User ID
            updates: Fields to update
            
        Returns:
            ServiceResult with updated NotificationPreference
        """
        try:
            result = self.get_user_preferences(user_id)
            if not result.success:
                return result
            
            preferences = result.data
            
            # Apply updates
            preferences = preferences.map(updates)
            
            # Validate
            is_valid, errors = preferences.validate()
            if not is_valid:
                return ServiceResult.error_result(
                    message=f"Validation failed: {', '.join(errors)}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Save
            preferences.prep_for_save()
            return self._save_model(preferences)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "update_preferences")
    
    def set_type_preference(
        self,
        user_id: str,
        notification_type: str,
        channel: str,
        enabled: bool
    ) -> ServiceResult[NotificationPreference]:
        """Set preference for specific notification type and channel."""
        try:
            result = self.get_user_preferences(user_id)
            if not result.success:
                return result
            
            preferences = result.data
            preferences.set_type_preference(notification_type, channel, enabled)
            
            # Save
            preferences.prep_for_save()
            return self._save_model(preferences)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "set_type_preference")
    
    # ========================================================================
    # Webhook Subscription Operations
    # ========================================================================
    
    @service_method("create_webhook_subscription")

    
    def create_webhook_subscription(
        self,
        subscription_name: str,
        url: str,
        event_types: List[str],
        **kwargs
    ) -> ServiceResult[WebhookSubscription]:
        """
        Create a webhook subscription.
        
        Args:
            tenant_id: Tenant ID
            user_id: User creating the subscription
            subscription_name: Display name
            url: Webhook endpoint URL
            event_types: List of events to subscribe to
            **kwargs: Additional config (secret, headers, etc.)
            
        Returns:
            ServiceResult with WebhookSubscription
        """
        try:
            subscription = WebhookSubscription()
            # set optional fields
            subscription = subscription.map(kwargs)
            # set known fields from request_context
            subscription.tenant_id = self.request_context.target_tenant_id
            subscription.user_id = self.request_context.target_user_id
            subscription.subscription_name = subscription_name
            subscription.url = url
            subscription.event_types = event_types
            
            # Validate
            is_valid, errors = subscription.validate()
            if not is_valid:
                return ServiceResult.error_result(
                    message=f"Validation failed: {', '.join(errors)}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Save
            subscription.prep_for_save()
            return self._save_model(subscription)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "create_webhook_subscription")
    
    def get_webhook_subscription(
        self,
        subscription_id: str
    ) -> ServiceResult[WebhookSubscription]:
        """Get a webhook subscription by ID."""
        try:
            tenant_id = self.request_context.target_tenant_id
            subscription = self._get_by_id(
                subscription_id, WebhookSubscription
            )
            
            if not subscription:
                return ServiceResult.error_result(
                    message=f"Webhook subscription not found: {subscription_id}",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            return ServiceResult.success_result(subscription)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_webhook_subscription")
    
    def update_webhook_subscription(
        self,
        subscription_id: str,
        updates: Dict[str, Any]
    ) -> ServiceResult[WebhookSubscription]:
        """Update a webhook subscription."""
        try:
            result = self.get_webhook_subscription(subscription_id)
            if not result.success:
                return result
            
            subscription = result.data
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(subscription, key):
                    setattr(subscription, key, value)
            
            # Validate
            is_valid, errors = subscription.validate()
            if not is_valid:
                return ServiceResult.error_result(
                    message=f"Validation failed: {', '.join(errors)}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Save
            subscription.modified_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            subscription.version += 1
            subscription.prep_for_save()
            
            return self._save_model(subscription)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "update_webhook_subscription")
    
    def list_webhook_subscriptions(
        self,
        active_only: bool = True
    ) -> ServiceResult[List[WebhookSubscription]]:
        """List webhook subscriptions for a tenant."""
        try:
            gsi_pk = f"tenant#{tenant_id}"
            
            results = self.dynamodb.query(
                key=Key("gsi1_pk").eq(gsi_pk) & Key("gsi1_sk").begins_with("WEBHOOK#"),
                table_name=self.table_name,
                index_name="gsi1"
            )
            
            subscriptions = []
            for item in results.get("Items", []):
                # Use .map() instead of load_from_dictionary
                subscription = WebhookSubscription().map(item)
                
                if active_only and not subscription.is_active():
                    continue
                
                subscriptions.append(subscription)
            
            return ServiceResult.success_result(subscriptions)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "list_webhook_subscriptions")
    
    # ========================================================================
    # Delivery Helper Methods
    # ========================================================================
    
    def should_send(
        self,
        notification: Notification,
        preferences: NotificationPreference,
        current_time: Optional[str] = None
    ) -> tuple[bool, str]:
        """
        Check if notification should be sent based on preferences.
        
        Returns:
            Tuple of (should_send: bool, reason: str)
        """
        # Urgent notifications bypass all preference checks except global disable
        if notification.priority == Notification.PRIORITY_URGENT:
            if not preferences.enabled:
                return (False, "Notifications disabled")
            # Skip DND, channel preferences, type preferences, and quiet hours for urgent
            # Continue to expiration and scheduling checks below
        else:
            # Non-urgent: apply all preference checks
            if not preferences.enabled:
                return (False, "Notifications disabled")
            
            # Check DND
            if preferences.do_not_disturb:
                return (False, "Do not disturb enabled")
            
            # Check channel enabled
            if not preferences.is_channel_enabled(notification.channel):
                return (False, f"Channel {notification.channel} disabled")
            
            # Check type-specific preference
            if not preferences.is_type_enabled(notification.notification_type, notification.channel):
                return (False, f"Type {notification.notification_type} disabled for {notification.channel}")
            
            # Check quiet hours
            if current_time and preferences.is_in_quiet_hours(current_time):
                return (False, "In quiet hours")
        
        # Check expiration
        now = dt.datetime.now(dt.UTC).timestamp()
        if notification.is_expired(now):
            return (False, "Notification expired")
        
        # Check scheduling
        if not notification.should_send_now(now):
            return (False, "Scheduled for later")
        
        return (True, "OK")
    
    def get_unread_count(self, recipient_id: str) -> ServiceResult[int]:
        """Get count of unread in-app notifications."""
        try:
            result = self.list_notifications(recipient_id, limit=1000, unread_only=True)
            if not result.success:
                return result
            
            count = len(result.data)
            return ServiceResult.success_result(count)
            
        except Exception as e:
            return ServiceResult.exception_result(e, ErrorCode.INTERNAL_ERROR, "get_unread_count")
