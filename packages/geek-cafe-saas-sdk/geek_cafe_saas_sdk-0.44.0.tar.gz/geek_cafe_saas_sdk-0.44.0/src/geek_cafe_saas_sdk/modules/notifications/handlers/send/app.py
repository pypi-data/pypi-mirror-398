"""Lambda handler for sending notifications."""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.notifications.services import NotificationService


handler_wrapper = create_handler(
    service_class=NotificationService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Send a notification.
    
    POST /notifications
    
    Body:
    {
        "notificationType": "payment_receipt",
        "channel": "email",
        "recipientId": "user-123",
        "body": "Your payment was successful",
        "subject": "Payment Confirmation",
        "priority": "normal"
    }
    """
    return handler_wrapper.execute(event, context, send_notification, injected_service)


def send_notification(event: LambdaEvent, service: NotificationService) -> ServiceResult:
    """Business logic for sending notification."""
    tenant_id = user_context.get("tenant_id")
    payload = event.body()
    
    notification_type = payload.get("notification_type")
    if not notification_type:
        raise ValueError("notification_type is required")
    
    channel = payload.get("channel")
    if not channel:
        raise ValueError("channel is required")
    
    recipient_id = payload.get("recipient_id")
    if not recipient_id:
        raise ValueError("recipient_id is required")
    
    body = payload.get("body")
    if not body:
        raise ValueError("body is required")
    
    # Extract optional fields
    kwargs = {}
    optional_fields = [
        "subject", "title", "body_html", "template_id", "template_data",
        "recipient_email", "recipient_phone", "recipient_device_token", "recipient_name",
        "send_after_utc_ts", "expires_utc_ts", "priority",
        "email_config", "sms_config", "push_config", "webhook_config",
        "triggered_by_event", "related_resource_type", "related_resource_id",
        "campaign_id", "tags", "metadata"
    ]
    
    for field in optional_fields:
        if field in payload:
            kwargs[field] = payload[field]
    
    result = service.create_notification(
        tenant_id=tenant_id,
        notification_type=notification_type,
        channel=channel,
        recipient_id=recipient_id,
        body=body,
        **kwargs
    )
    
    return result
